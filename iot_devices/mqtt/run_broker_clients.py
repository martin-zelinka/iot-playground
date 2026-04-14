#!/usr/bin/env python3
"""
Complete Example: MQTT Broker + Database Service + Weather Publisher
Demonstrates the full data flow from publisher to database storage.
"""

import random
import time
import threading
from iot_devices.mqtt.broker import MQTTBroker
from iot_devices.mqtt.client import MQTTClient
from iot_devices.mqtt.client_subscribe import MQTTDatabaseBridge


def database_service_example():
    """Start the database service to store sensor data."""
    print("🗄️  Starting Database Service...")
    bridge = MQTTDatabaseBridge(broker_host="localhost", broker_port=1883)
    bridge.run()


def publisher_example(city):
    """Publish weather data that will be stored in the database."""
    print("📡 Starting Weather Publisher...")
    publisher = MQTTClient(client_id=f"weather_publisher_{random.randint(1000, 9999)}", enable_lwt=True)

    if not publisher.connect():
        print("❌ Failed to connect to MQTT broker")
        return

    # Publish weather data for particular city
    print(f"\n🌍 Publishing weather data for {city}...")
    for _ in range(15):
        try:
            publisher.publish_sensor_data(city)

            # check if device was not shutdown
            if not publisher.running:
                return

        except Exception as e:
            print(f"❌ Error getting weather for {city}: {e}")

        time.sleep(3)  # Wait between messages


    publisher.disconnect()
    print("✅ Publisher finished")


def main():
    """Run the complete database integration example."""
    print("=" * 70)
    print("MQTT Broker + Database Service + Weather Publisher Example")
    print("=" * 70)

    # Start the broker
    print("\n 1️⃣  Starting MQTT Broker...")
    broker = MQTTBroker(port=1883)
    broker.start()

    # Give broker time to start
    time.sleep(2)

    try:
        # Start database service in a separate thread
        print("\n2️⃣  Starting Database Service in background thread...")
        db_thread = threading.Thread(target=database_service_example, daemon=True)
        db_thread.start()

        # Give database service time to connect and subscribe
        time.sleep(3)

        # Run both publishers simultaneously
        print("\n3️⃣  Starting Weather Publishers for LON and PRG...")
        lon_thread = threading.Thread(target=publisher_example, args=("LON",), daemon=True)
        prg_thread = threading.Thread(target=publisher_example, args=("PRG",), daemon=True)

        # Start both publishers at the same time
        lon_thread.start()
        prg_thread.start()

        # Wait for both publishers to finish
        lon_thread.join()
        prg_thread.join()

        # Give database service time to process all messages
        print("\n⏳ Waiting for database to finish processing...")
        time.sleep(3)

        print("\n" + "=" * 70)
        print("✅ Example completed successfully!")
        print("   Check your Django admin or database for the stored sensor readings")
        print("=" * 70)

        print("\nPress Ctrl+C to stop...")

        # Keep running until user interrupts
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n⏹️  Example interrupted by user")

    finally:
        # Stop the broker
        print("\n🛑 Stopping MQTT Broker...")
        broker.stop()

        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
