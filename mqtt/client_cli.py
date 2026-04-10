#!/usr/bin/env python3
"""CLI interface for MQTT Client."""

import argparse
import logging
import sys

from mqtt.client import MQTTClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """CLI interface for MQTT Client."""
    parser = argparse.ArgumentParser(description="MQTT Client for easycon")
    parser.add_argument("--client-id", type=str, default="mqtt_client", help="Client ID")
    parser.add_argument("--host", type=str, default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", type=str, help="Topic to subscribe to")
    parser.add_argument("--publish", type=str, help="Topic to publish to")
    parser.add_argument("--message", type=str, help="Message to publish")
    parser.add_argument("--city", type=str, help="Publish sensor data (format: LON, PRG, BRN)")
    parser.add_argument("--no-control", action="store_true", help="Disable control topic listening")

    args = parser.parse_args()

    # Create client
    client = MQTTClient(
        client_id=args.client_id,
        host=args.host,
        port=args.port,
        listen_for_control=not args.no_control
    )

    # Connect
    if not client.connect():
        logger.error("Failed to connect to MQTT broker")
        sys.exit(1)

    # Subscribe to topic if specified
    if args.topic:
        client.subscribe(args.topic)

    # Publish message if specified
    if args.publish and args.message:
        client.publish(args.publish, args.message)

    # Publish sensor data if specified
    if args.city:
        try:
            client.publish_sensor_data(args.city)
        except ValueError:
            logger.error("Invalid city. Use: LON, PRG, BRN")

    # Run forever if subscribing or listening for control
    if args.topic or not args.no_control:
        client.run_forever()
    else:
        # Disconnect if just publishing
        import time
        time.sleep(1)
        client.disconnect()


if __name__ == "__main__":
    main()
