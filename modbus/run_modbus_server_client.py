#!/usr/bin/env python3
"""Run Modbus server and client to demonstrate full data flow."""

import asyncio
import logging
import os
import signal
import sys
import threading
from typing import Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modbus.modbus_server import ModbusTCPServer
from modbus.modbus_client import ModbusTCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    if server_instance:
        server_instance.stop()
    if client_instance:
        client_instance.stop()
    sys.exit(0)


# Global instances for signal handling
server_instance: Optional[ModbusTCPServer] = None
client_instance: Optional[ModbusTCPClient] = None


def run_client(client: ModbusTCPClient):
    """Run Modbus client in a separate thread."""
    try:
        logger.info("🚀 Starting Modbus client thread...")
        client.start()
    except Exception as e:
        logger.error(f"✗ Client error: {e}")


def main():
    """Main entry point for running both server and client."""
    global server_instance, client_instance

    # Load configuration from environment
    server_host = os.getenv("MODBUS_SERVER_HOST", "0.0.0.0")
    server_port = int(os.getenv("MODBUS_SERVER_PORT", "5020"))
    server_poll_interval = int(os.getenv("MODBUS_SERVER_POLL_INTERVAL", "5"))
    client_poll_interval = int(os.getenv("MODBUS_CLIENT_POLL_INTERVAL", "10"))

    # Create server instance
    server_instance = ModbusTCPServer(
        host=server_host,
        port=server_port,
        poll_interval=server_poll_interval
    )

    # Create client instance
    client_instance = ModbusTCPClient(
        server_host="localhost",
        server_port=server_port,
        poll_interval=client_poll_interval
    )

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start server in asyncio (main thread)
        logger.info("🎯 Starting Modbus Server + Client system...")

        # Start client in background thread
        client_thread = threading.Thread(
            target=run_client,
            args=(client_instance,),
            daemon=True
        )

        # Give server more time to start before client connects
        logger.info("⏳ Waiting for server to initialize...")
        import time
        time.sleep(5)  # Increased wait time to ensure server is ready

        # Start client thread
        client_thread.start()
        logger.info("✓ Client thread started")

        # Start server (blocking, runs in main thread)
        asyncio.run(server_instance.start())

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"✗ System error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if server_instance:
            server_instance.stop()
        if client_instance:
            client_instance.stop()


if __name__ == "__main__":
    main()
