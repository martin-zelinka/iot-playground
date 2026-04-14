#!/usr/bin/env python3
"""Modbus TCP client for reading weather data and storing to MongoDB."""

import logging
import os
import signal
import struct
import sys
import threading
import time
from typing import Optional, Dict, Any

from pymodbus.client import ModbusTcpClient

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_clients.mongo_client import MongoDBClient, create_mongo_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModbusTCPClient:
    """Modbus TCP client that reads London weather data and stores it to MongoDB."""

    def __init__(self, server_host: str = "localhost", server_port: int = 5020,
                 poll_interval: int = 10, mongo_client: Optional[MongoDBClient] = None):
        """
        Initialize Modbus TCP client for London weather data.

        Args:
            server_host: Modbus server hostname or IP
            server_port: Modbus server port
            poll_interval: Data collection interval in seconds
            mongo_client: MongoDB client instance (optional, will create if None)
        """
        self.server_host = server_host
        self.server_port = server_port
        self.poll_interval = poll_interval

        # Modbus client instance
        self.modbus_client: Optional[ModbusTcpClient] = None

        # MongoDB client
        self.mongo_client = mongo_client

        # Threading control
        self._running = False
        self._collection_thread: Optional[Any] = None  # threading.Thread type

        # Register mapping (1-based addressing to match server)
        self.city_registers = {
            "LON": (1, 2),   # Registers 1-2: London temperature
        }

    def _registers_to_float(self, registers: list[int]) -> float:
        """
        Convert two 16-bit registers to float value (IEEE 754 binary32).

        Args:
            registers: List of two 16-bit register values

        Returns:
            Float value
        """
        if len(registers) != 2:
            raise ValueError(f"Expected 2 registers, got {len(registers)}")

        # Pack two 16-bit values as 32-bit little-endian
        packed = struct.pack('<HH', registers[0], registers[1])
        # Unpack as float
        value = struct.unpack('<f', packed)[0]
        return float(value)

    def _read_weather_registers(self) -> Optional[Dict[str, float]]:
        """
        Read London weather data from Modbus holding registers.

        Returns:
            Dictionary with London temperature or None on error
        """
        if not self.modbus_client or not self.modbus_client.connected:
            logger.error("Modbus client not connected")
            return None

        try:
            # Read 2 holding registers starting at address 1
            # The server's SimData starts at address=1, so we read from address=1
            result = self.modbus_client.read_holding_registers(address=1, count=2)

            if result.isError():
                logger.error(f"Failed to read registers: {result}")
                return None

            registers = result.registers
            weather_data = {}

            for city, (reg_low, reg_high) in self.city_registers.items():
                try:
                    # Extract the two registers for this city
                    # Since we read from address 1, registers[0] is address 1, registers[1] is address 2
                    city_regs = registers[0:2]  # Get first 2 registers
                    temp = self._registers_to_float(city_regs)
                    weather_data[city] = temp

                    logger.info(f"📊 {city}: {temp:.1f}°C ← Registers {reg_low}-{reg_high}: {city_regs}")

                except Exception as e:
                    logger.error(f"Error decoding {city} registers: {e}")
                    weather_data[city] = None

            return weather_data

        except Exception as e:
            logger.error(f"Error reading weather registers: {e}")
            return None

    def _store_to_mongodb(self, weather_data: Dict[str, float]):
        """
        Store London weather data to MongoDB.

        Args:
            weather_data: Dictionary with London temperature
        """
        if not self.mongo_client or not self.mongo_client.connected:
            logger.warning("MongoDB client not connected, skipping storage")
            return

        try:
            # Store using existing method
            doc_id = self.mongo_client.store_modbus_packet(weather_data)

            if doc_id:
                logger.info(f"✓ Stored weather data to MongoDB: {weather_data}")
            else:
                logger.error("Failed to store weather data to MongoDB")

        except Exception as e:
            logger.error(f"Error storing to MongoDB: {e}")

    def _collect_data(self):
        """Background thread function to collect data periodically."""
        logger.info(f"🔄 Data collection thread started (interval: {self.poll_interval}s)")

        while self._running:
            try:
                # Read weather data from Modbus registers
                weather_data = self._read_weather_registers()

                if weather_data:
                    # Store to MongoDB
                    self._store_to_mongodb(weather_data)
                else:
                    logger.warning("Failed to read weather data from Modbus server")

            except Exception as e:
                logger.error(f"Error in data collection cycle: {e}")

            # Wait for next collection cycle
            time.sleep(self.poll_interval)

        logger.info("Data collection thread stopped")

    def start(self):
        """Start Modbus TCP client and begin data collection."""
        try:
            # Create and connect Modbus client
            logger.info(f"🔌 Connecting to Modbus server at {self.server_host}:{self.server_port}")
            self.modbus_client = ModbusTcpClient(host=self.server_host, port=self.server_port)

            # Try to connect with retries
            max_retries = 5
            retry_delay = 2

            for attempt in range(max_retries):
                if self.modbus_client.connect():
                    logger.info(f"✓ Connected to Modbus server")
                    break
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️  Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        raise ConnectionError(f"Failed to connect to Modbus server at {self.server_host}:{self.server_port} after {max_retries} attempts")

            # Create MongoDB client if not provided
            if not self.mongo_client:
                logger.info("🔗 Connecting to MongoDB...")
                self.mongo_client = create_mongo_client()

            # Start data collection
            self._running = True
            self._collection_thread = threading.Thread(target=self._collect_data, daemon=True)

            # Run data collection in foreground
            logger.info("🚀 Starting Modbus client data collection...")
            self._collect_data()

        except ConnectionError as e:
            logger.error(f"✗ Connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"✗ Client error: {e}")
            raise

    def stop(self):
        """Stop Modbus TCP client and data collection."""
        logger.info("Stopping Modbus TCP client...")

        self._running = False

        if self.modbus_client and self.modbus_client.connected:
            self.modbus_client.close()

        if self.mongo_client:
            self.mongo_client.disconnect()

        logger.info("Modbus TCP client stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    if client_instance:
        client_instance.stop()
    sys.exit(0)


# Global client instance for signal handling
client_instance: Optional[ModbusTCPClient] = None


def main():
    """Main entry point for standalone execution."""
    global client_instance

    # Load configuration from environment
    server_host = os.getenv("MODBUS_CLIENT_HOST", "localhost")
    server_port = int(os.getenv("MODBUS_SERVER_PORT", "5020"))
    poll_interval = int(os.getenv("MODBUS_CLIENT_POLL_INTERVAL", "10"))

    # Create client instance
    client_instance = ModbusTCPClient(
        server_host=server_host,
        server_port=server_port,
        poll_interval=poll_interval
    )

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start client
    try:
        client_instance.start()
    except Exception as e:
        logger.error(f"Failed to start client: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
