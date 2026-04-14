#!/usr/bin/env python3
"""Modbus TCP modbus_client to read Float32 values from server and store it to mongo"""
import logging
import os
import time
from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient
from iot_devices.db_clients.mongo_client import create_mongo_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_modbus_client():

    load_dotenv()
    server_host = os.getenv("MODBUS_CLIENT_HOST", "localhost")
    server_port = int(os.getenv("MODBUS_SERVER_PORT", "5020"))
    poll_interval = int(os.getenv("MODBUS_CLIENT_POLL_INTERVAL", "5"))

    # Connect to the server
    modbus_client = ModbusTcpClient(server_host, port=server_port)
    mongo_client = create_mongo_client()

    if not modbus_client.connect():
        logger.error("Failed to connect to server")
        return

    logger.info("Connected to Modbus TCP server")

    try:
        while True:
            # Read holding registers
            # Address 0, count 2 (float32 uses 2 registers)
            result = modbus_client.read_holding_registers(
                address=0,    # Starting address
                count=2,      # Number of registers to read (float32 = 2 registers)
                device_id=1   # Device ID
            )

            if result.isError():
                logger.error(f"Error reading registers: {result}")
                break

            # Convert the 2 registers back to float32 value
            temperature = modbus_client.convert_from_registers(
                result.registers,           # List of 2 registers
                data_type=modbus_client.DATATYPE.FLOAT32
            )

            mongo_client.store_modbus_packet({'LON_temperature': temperature})

            logger.info(f"loading value 📊 temp: {temperature:.1f}°C ← from Holding Registers")

            # Wait before next read
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        logger.info("Stopping modbus_client...")
    finally:
        modbus_client.close()
        logger.info("Connection closed")

if __name__ == "__main__":
    run_modbus_client()