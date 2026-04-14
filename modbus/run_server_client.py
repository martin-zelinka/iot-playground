#!/usr/bin/env python3
"""Run Modbus server and client to demonstrate full data flow."""
import multiprocessing
import time
import asyncio
import logging

from modbus.modbus_server import run_modbus_server
from modbus.modbus_client import run_modbus_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_server():
    """Run the Modbus server in a separate process"""
    logger.info("Starting Modbus server process...")
    asyncio.run(run_modbus_server())


def run_client():
    """Run the Modbus client in a separate process"""
    # Give the server a moment to start up
    time.sleep(2)
    logger.info("Starting Modbus client process...")
    run_modbus_client()


if __name__ == "__main__":
    logger.info("Starting Modbus server and client...")

    # Create processes for server and client
    server_process = multiprocessing.Process(target=run_server)
    client_process = multiprocessing.Process(target=run_client)

    # Start both processes
    server_process.start()
    client_process.start()

    try:
        # Wait for both processes to complete
        server_process.join()
        client_process.join()
    except KeyboardInterrupt:
        logger.info("Stopping Modbus server and client...")
        server_process.terminate()
        client_process.terminate()
        server_process.join()
        client_process.join()
        logger.info("Stopped")
