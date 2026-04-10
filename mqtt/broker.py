#!/usr/bin/env python3
"""
MQTT Broker implementation using Mosquitto.
This script manages a local Mosquitto broker for development/testing.
"""

import subprocess
import time
import signal
import sys
from pathlib import Path


class MQTTBroker:
    """Manages a local Mosquitto MQTT broker."""

    def __init__(self, port: int = 1883, host: str = "localhost", config_file: str = None):
        self.port = port
        self.host = host
        self.process = None
        # Use provided config file or default to mosquitto.conf in mqtt folder
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = Path(__file__).parent / "mosquitto.conf"

    def _validate_config(self) -> bool:
        """Validate that the configuration file exists."""
        if not self.config_file.exists():
            print(f"✗ Configuration file not found: {self.config_file}")
            return False
        return True

    def start(self):
        """Start the Mosquitto broker."""
        if self.is_running():
            print(f"MQTT Broker is already running on port {self.port}")
            return

        if not self._validate_config():
            return

        print(f"Starting MQTT Broker on {self.host}:{self.port}")
        print(f"Using configuration: {self.config_file}")

        try:
            # Start mosquitto with configuration
            self.process = subprocess.Popen(
                ["mosquitto", "-c", str(self.config_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait a bit for broker to start
            time.sleep(1)

            if self.process.poll() is None:
                print(f"✓ MQTT Broker started successfully on port {self.port}")
                print(f"  Process ID: {self.process.pid}")
            else:
                stdout, stderr = self.process.communicate()
                print(f"✗ Failed to start MQTT Broker")
                print(f"  stdout: {stdout}")
                print(f"  stderr: {stderr}")
                self.process = None

        except FileNotFoundError:
            print("✗ Mosquitto not found. Please install it:")
            print("  macOS: brew install mosquitto")
            print("  Ubuntu: sudo apt-get install mosquitto mosquitto-clients")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Error starting broker: {e}")
            self.process = None

    def stop(self):
        """Stop the Mosquitto broker."""
        if self.process:
            print(f"Stopping MQTT Broker (PID: {self.process.pid})")
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
                print("✓ MQTT Broker stopped")
            except subprocess.TimeoutExpired:
                print("Broker didn't stop gracefully, forcing...")
                self.process.kill()
                self.process.wait()
                print("✓ MQTT Broker force stopped")

            self.process = None
        else:
            print("MQTT Broker is not running")

    def is_running(self) -> bool:
        """Check if the broker is running."""
        if self.process:
            return self.process.poll() is None
        return False

    def restart(self):
        """Restart the broker."""
        self.stop()
        time.sleep(1)
        self.start()


def main():
    """Main entry point for running the broker."""
    import argparse

    parser = argparse.ArgumentParser(description="MQTT Broker for easycon")
    parser.add_argument("--port", type=int, default=1883, help="Port number (default: 1883)")
    parser.add_argument("--host", type=str, default="localhost", help="Host address (default: localhost)")
    parser.add_argument("--config", type=str, default=None, help="Path to mosquitto configuration file")
    parser.add_argument("--action", type=str, default="start",
                       choices=["start", "stop", "restart"], help="Action to perform")

    args = parser.parse_args()

    broker = MQTTBroker(port=args.port, host=args.host, config_file=args.config)

    # Handle graceful shutdown
    def signal_handler(_signum, _frame):
        broker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Execute action
    if args.action == "start":
        broker.start()
        # Keep running
        try:
            while broker.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            broker.stop()
    elif args.action == "stop":
        broker.stop()
    elif args.action == "restart":
        broker.restart()


if __name__ == "__main__":
    main()
