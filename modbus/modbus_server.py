#!/usr/bin/env python3
"""Modbus TCP Server with Float32 Holding Registers"""
import asyncio
import logging
import os
from dotenv import load_dotenv
from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice
from pymodbus.client import ModbusTcpClient

from mqtt.weather import get_weather_async

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CITY='LON'

async def update_float32_values(server, poll_interval=5):
    """Background task to update float32 register values"""
    device_id = 1
    func_code = 3  # Function code for holding registers
    address = 0

    while True:
        # Convert float32 to registers
        temperature = await get_weather_async(CITY)

        if not temperature:
            continue

        # Convert float32 values to register pairs
        temp_regs = ModbusTcpClient.convert_to_registers(
            temperature,
            data_type=ModbusTcpClient.DATATYPE.FLOAT32
        )

        # Write to registers
        await server.async_setValues(device_id, func_code, address, temp_regs)

        logger.info(f"publishing value 📊 {CITY}: {temperature:.1f}°C → Holding Registers")
        await asyncio.sleep(poll_interval)

async def run_modbus_server():
    # Create server with float32 holding registers
    # Each float32 value uses 2 registers
    float32_block = SimData(
        address=0,           # Starting address
        count=2,             # 2 registers = 1 float32 values
        values=[0.0],   # Initial float32 values
        datatype=DataType.FLOAT32
    )

    device = SimDevice(1, [float32_block])

    # Load configuration from environment
    load_dotenv()
    host = os.getenv("MODBUS_SERVER_HOST", "localhost")
    port = int(os.getenv("MODBUS_SERVER_PORT", "5020"))
    poll_interval = int(os.getenv("MODBUS_SERVER_POLL_INTERVAL", "5"))

    server = ModbusTcpServer(
        device,
        address=(host, port)
    )

    # Start background task to update float32 values
    update_task = asyncio.create_task(update_float32_values(server, poll_interval))

    # Start server
    logger.info("Starting Modbus TCP Server with Float32 support")
    await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(run_modbus_server())
