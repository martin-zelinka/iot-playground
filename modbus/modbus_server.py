#!/usr/bin/env python3
"""Modbus TCP server for weather data storage and serving."""

import asyncio
import logging
import os
import signal
import struct
import sys
from typing import Optional

from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import SimData, SimDevice, DataType

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mqtt.weather import get_weather_async

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModbusTCPServer:
    """Modbus TCP server that polls London weather data and serves it via holding registers."""

    def __init__(self, host: str = "0.0.0.0", port: int = 5020, poll_interval: int = 5):
        """
        Initialize Modbus TCP server for London weather data.

        Args:
            host: Host address to bind to
            port: Modbus TCP port (standard is 502, requires root)
            poll_interval: Weather data polling interval in seconds
        """
        self.host = host
        self.port = port
        self.poll_interval = poll_interval

        # City configuration (name, register_low, register_high)
        self.city = "LON"
        self.reg_low, self.reg_high = 1, 2

        # Register storage with initial values
        self._register_values = [0, 0]
        self._register_lock = asyncio.Lock()

        # Initialize holding registers using SimData
        self.holding_registers = SimData(
            address=1,
            values=self._register_values,
            datatype=DataType.REGISTERS
        )

        # Server instance
        self.server: Optional[ModbusTcpServer] = None

        # Async control
        self._running = False
        self._polling_task: Optional[asyncio.Task] = None

    def _float_to_registers(self, value: float) -> list[int]:
        """
        Convert float value to two 16-bit registers (IEEE 754 binary32).

        Args:
            value: Float value to convert

        Returns:
            List of two 16-bit register values
        """
        # Pack float as 32-bit little-endian
        packed = struct.pack('<f', value)
        # Unpack as two 16-bit values
        reg1, reg2 = struct.unpack('<HH', packed)
        return [reg1, reg2]

    async def _update_registers(self, registers: list[int]):
        """Update holding registers in the server's context."""
        async with self._register_lock:
            self._register_values[:] = registers

        # Update the actual device context (pymodbus internal state)
        if self.server and self.server.context:
            device = self.server.context.devices.get(1)
            if device and hasattr(device, 'block'):
                block = device.block.get('x', [])
                if block and len(block) >= 3:
                    # Update values in the block
                    values = list(block[2])
                    values[:len(registers)] = registers
                    device.block['x'] = (block[0], block[1], values, block[3])

    async def _poll_weather_data(self):
        """Background task to poll London weather data periodically."""
        logger.info(f"🌤️  Weather polling task started (interval: {self.poll_interval}s)")

        while self._running:
            try:
                temp = await get_weather_async(self.city)  # type: ignore

                if temp is not None:
                    # Convert float to registers
                    registers = self._float_to_registers(temp)

                    # Update holding registers
                    await self._update_registers(registers)

                    logger.info(f"📊 {self.city}: {temp:.1f}°C → Registers {self.reg_low}-{self.reg_high}: {registers}")
                else:
                    logger.warning(f"⚠️  {self.city}: API timeout, skipping register update")

            except Exception as e:
                logger.error(f"❌ Error in weather polling cycle: {e}")

            # Wait for next poll cycle
            await asyncio.sleep(self.poll_interval)

        logger.info("Weather polling task stopped")

    async def start(self):
        """Start the Modbus TCP server and weather polling."""
        try:
            # Start async tasks
            self._running = True

            # Create Modbus server
            device = SimDevice(
                id=1,
                simdata=[self.holding_registers]
            )
            self.server = ModbusTcpServer(
                context=device,
                address=(self.host, self.port)
            )

            # Log startup info
            logger.info(f"🚀 Starting Modbus TCP server on {self.host}:{self.port}")
            logger.info(f"📍 Register mapping: {self.city} → Registers {self.reg_low}-{self.reg_high}")

            # Start weather polling task
            self._polling_task = asyncio.create_task(self._poll_weather_data())

            # Start Modbus server
            await self.server.serve_forever()

        except PermissionError:
            logger.error(f"✗ Permission denied for port {self.port}. Port 502 requires root privileges.")
            logger.error("  Run with: sudo python -m modbus.modbus_server")
            logger.error("  Or use a non-standard port (e.g., 5020) with: MODBUS_SERVER_PORT=5020")
            raise
        except OSError as e:
            if e.errno == 48:  # Address already in use
                logger.error(f"✗ Port {self.port} is already in use. Choose a different port.")
            else:
                logger.error(f"✗ Failed to start server: {e}")
            raise
        except Exception as e:
            logger.error(f"✗ Server error: {e}")
            raise

    async def stop(self):
        """Stop the Modbus TCP server and weather polling."""
        logger.info("Stopping Modbus TCP server...")

        self._running = False

        # Stop polling task
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await asyncio.wait_for(self._polling_task, timeout=2)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        # Stop server
        if self.server:
            self.server.shutdown()

        logger.info("Modbus TCP server stopped")


async def signal_handler(signum):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    if server_instance:
        await server_instance.stop()
    sys.exit(0)


# Global server instance for signal handling
server_instance: Optional[ModbusTCPServer] = None


async def main():
    global server_instance

    # Load configuration from environment
    host = os.getenv("MODBUS_SERVER_HOST", "localhost")
    port = int(os.getenv("MODBUS_SERVER_PORT", "5020"))
    poll_interval = int(os.getenv("MODBUS_SERVER_POLL_INTERVAL", "5"))

    # Create server instance
    server_instance = ModbusTCPServer(host=host, port=port, poll_interval=poll_interval)

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(signal_handler(sig)))

    # Start server (blocking, async)
    try:
        await server_instance.start()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
