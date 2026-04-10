#!/usr/bin/env python3
"""
Example demonstration of MQTT broker and weather data client.
Run this script to see a complete example of publishing weather data.
"""

import time
import threading
from mqtt.broker import MQTTBroker
from mqtt.client import MQTTClient
from mqtt.weather import City


def subscriber_example():
    """Example subscriber that listens for weather data."""
    def on_message(topic, payload):
        print(f"📩 Subscriber received: {topic} -> {payload}")

    subscriber = MQTTClient(client_id="example_subscriber")
    subscriber.set_message_callback(on_message)

    if subscriber.connect():
        subscriber.subscribe("sensors/#")
        subscriber.subscribe("test/#")

        # Keep subscriber running for 30 seconds
        print("Subscriber running for 30 seconds...")
        time.sleep(30)
        subscriber.disconnect()


def publisher_example():
    """Example publisher that sends weather data for different cities."""
    publisher = MQTTClient(client_id="example_publisher")

    if publisher.connect():
        # Publish test messages
        publisher.publish("test/message", "Hello from publisher!")

        # Publish weather data for different cities
        cities = ["LON", "PRG", "BRN"]
        for city in cities:
            print(f"\n🌍 Publishing weather data for {city}...")

            try:
                publisher.publish_sensor_data(city)
            except Exception as e:
                print(f"Error getting weather for {city}: {e}")

            time.sleep(2)

        publisher.disconnect()


def main():
    """Run the complete example."""
    print("=" * 60)
    print("MQTT Broker and Weather Client Example")
    print("=" * 60)

    # Start the broker
    print("\n1. Starting MQTT Broker...")
    broker = MQTTBroker(port=1883)
    broker.start()

    # Give broker time to start
    time.sleep(2)

    try:
        # Start subscriber in a separate thread
        print("\n2. Starting Subscriber...")
        subscriber_thread = threading.Thread(target=subscriber_example)
        subscriber_thread.daemon = True
        subscriber_thread.start()

        # Give subscriber time to connect
        time.sleep(1)

        # Run publisher
        print("\n3. Starting Weather Publisher...")
        publisher_example()

        # Wait for subscriber to finish
        subscriber_thread.join()

        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\nExample interrupted by user")

    finally:
        # Stop the broker
        print("\n4. Stopping MQTT Broker...")
        broker.stop()


if __name__ == "__main__":
    main()
