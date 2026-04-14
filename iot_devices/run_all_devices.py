#!/usr/bin/env python3
"""Run Modbus and MQTT systems together."""

import asyncio
import multiprocessing
import random
import threading
import time

from iot_devices.modbus.modbus_client import run_modbus_client
from iot_devices.modbus.modbus_server import run_modbus_server
from iot_devices.mqtt.broker import MQTTBroker
from iot_devices.mqtt.client import MQTTClient
from iot_devices.mqtt.client_subscribe import MQTTDatabaseBridge


def modbus_server_process():
    """Run Modbus server in a separate process."""
    asyncio.run(run_modbus_server())


def modbus_client_process():
    """Run Modbus client in a separate process."""
    time.sleep(2)
    run_modbus_client()


def run_database_service():
    """Run MQTT database service."""
    bridge = MQTTDatabaseBridge(broker_host="localhost", broker_port=1883)
    bridge.run()


def run_weather_publisher(city):
    """Run MQTT weather publisher for a city."""
    publisher = MQTTClient(
        client_id=f"weather_publisher_{random.randint(1000, 9999)}", enable_lwt=True
    )

    if not publisher.connect():
        print(f"Failed to connect publisher for {city}")
        return

    try:
        for _ in range(15):
            publisher.publish_sensor_data(city)
            if not publisher.running:
                break
            time.sleep(3)
    finally:
        publisher.disconnect()


def main():
    """Run combined Modbus and MQTT systems."""
    print("Starting Modbus and MQTT systems...")

    # Start Modbus processes
    server_process = multiprocessing.Process(target=modbus_server_process)
    client_process = multiprocessing.Process(target=modbus_client_process)
    server_process.start()
    client_process.start()

    time.sleep(2)  # Let Modbus initialize

    # Start MQTT broker
    broker = MQTTBroker(port=1883)
    broker.start()
    time.sleep(2)

    # Start MQTT services
    db_thread = threading.Thread(target=run_database_service, daemon=True)
    db_thread.start()
    time.sleep(2)

    # Start weather publishers
    lon_thread = threading.Thread(
        target=run_weather_publisher, args=("LON",), daemon=True
    )
    prg_thread = threading.Thread(
        target=run_weather_publisher, args=("PRG",), daemon=True
    )
    lon_thread.start()
    prg_thread.start()

    print("All systems running. Press Ctrl+C to stop.")

    try:
        # Wait for publishers to finish
        lon_thread.join()
        prg_thread.join()

        # Keep running until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping systems...")

    finally:
        # Stop MQTT broker
        broker.stop()

        # Stop Modbus processes
        server_process.terminate()
        client_process.terminate()
        server_process.join()
        client_process.join()

        print("Stopped")


if __name__ == "__main__":
    main()
