#!/usr/bin/env python3
"""MQTT to Database Bridge - Subscribes to topics and stores messages in PostgreSQL."""

import json
import logging
import signal
import sys
import time
from datetime import datetime

import django
import os

# Add project root and backend to path
project_root = os.path.join(os.path.dirname(__file__), '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

backend_path = os.path.join(project_root, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_api.settings')
django.setup()

from django.db import transaction
from mqtt.client import MQTTClient
from mqtt_storage.models import MQTTPacket, MQTTClientStatus

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MQTTDatabaseBridge:
    """Bridge between MQTT broker and PostgreSQL database."""

    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.subscriber = None
        self.running = False
        self.stats = {'messages_received': 0, 'messages_processed': 0, 'errors': 0, 'start_time': None}



    def update_device_status(self, topic: str, packet: MQTTPacket):
        """Update device status based on received message."""
        try:
            _, client_id, _, _ = topic.split('/')
            client, created = MQTTClientStatus.objects.get_or_create(
                client_id=client_id,
                defaults={
                    'status': 'online',
                    'first_seen': datetime.now(),
                    'total_packets': 1  # Start at 1 since we just received a message
                }
            )

            if not created:
                client.status = 'online'
                client.last_seen = datetime.now()
                client.total_packets += 1
                client.save(update_fields=['status', 'last_seen', 'total_packets'])

        except Exception as e:
            logger.error(f"Error updating device status: {e}")

    def handle_message(self, topic: str, payload):
        """Main message handler - processes incoming MQTT messages."""
        self.stats['messages_received'] += 1

        try:
            # Convert payload to JSON if possible, otherwise store as string
            if isinstance(payload, (bytes, bytearray)):
                payload_str = payload.decode('utf-8')
            elif not isinstance(payload, str):
                payload_str = str(payload)
            else:
                payload_str = payload

            # Try to parse as JSON
            try:
                payload_json = json.loads(payload_str)
            except json.JSONDecodeError:
                payload_json = {"data": payload_str}

            logger.info(f"📩 {topic}: {str(payload_json)[:100]}...")

            # Save all received messages
            with transaction.atomic():
                packet = MQTTPacket.objects.create(topic=topic, payload=payload_json, qos=0, retain=False)
                self.update_device_status(topic, packet)
                self.stats['messages_processed'] += 1
                logger.info(f"✓ Saved to database (ID: {packet.id})")

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"✗ Error processing message: {e}")

    def start(self):
        """Start the MQTT to database bridge."""
        logger.info("Starting MQTT to Database Bridge...")

        # Create and connect subscriber
        self.subscriber = MQTTClient(client_id="mqtt_db_bridge", host=self.broker_host, port=self.broker_port)
        self.subscriber.set_message_callback(self.handle_message)

        # Connect first, then subscribe
        if not self.subscriber.connect():
            logger.error("Failed to connect to MQTT broker")
            return False

        # Subscribe to sensor topics
        self.subscriber.subscribe("sensors/#")

        self.running = True
        self.stats['start_time'] = datetime.now()
        logger.info(f"✓ Bridge running on {self.broker_host}:{self.broker_port}, monitoring `sensors/#` topics")
        return True

    def stop(self):
        """Stop the bridge."""
        logger.info("Stopping MQTT to Database Bridge...")
        self.running = False

        if self.subscriber:
            self.subscriber.disconnect()

        # Print statistics
        if self.stats['start_time']:
            runtime = datetime.now() - self.stats['start_time']
            logger.info(f"Stats: runtime={runtime}, received={self.stats['messages_received']}, "
                       f"processed={self.stats['messages_processed']}, errors={self.stats['errors']}")

    def run(self):
        """Run the bridge until interrupted."""
        if not self.start():
            return

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MQTT to Database Bridge Service")
    parser.add_argument("--host", type=str, default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")

    args = parser.parse_args()
    bridge = MQTTDatabaseBridge(broker_host=args.host, broker_port=args.port)

    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda *_: (bridge.stop(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda *_: (bridge.stop(), sys.exit(0)))

    bridge.run()


if __name__ == "__main__":
    main()
