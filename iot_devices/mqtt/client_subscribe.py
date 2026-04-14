#!/usr/bin/env python3
"""MQTT to Database Bridge - Subscribes to device topics and stores in databases."""

import logging
import os
import signal
import sys
import time

import django
from django.utils import timezone

# Add project root and backend to path
# When running from devices/mqtt/, we need to go up two levels to reach project root
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
backend_path = os.path.join(project_root, "backend")

# Add backend first to avoid conflicts with root-level devices folder
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_api.settings")
django.setup()

from devices.models import MQTTClientStatus  # noqa: E402
from django.db import transaction  # noqa: E402

from iot_devices.db_clients.mongo_client import MongoDBClient  # noqa: E402
from iot_devices.mqtt.client import MQTTClient  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MQTTDatabaseBridge:
    """Bridge between MQTT broker and PostgreSQL/MongoDB databases."""

    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.subscriber = None
        self.mongo_client = None
        self.running = False

    def update_device_status_table(self, topic: str):
        """Update device status based on received message."""
        try:
            # Extract client_id from topic: device/sensors/{client_id}/{location}/temperature
            _, _, client_id, _, _ = topic.split("/")
            client, new_row_created = MQTTClientStatus.objects.get_or_create(
                client_id=client_id,
                defaults={
                    "status": "online",
                    "first_seen": timezone.now(),
                    "total_packets": 1,  # Start at 1 since we just received a message
                },
            )

            if not new_row_created:
                client.status = "online"
                client.last_seen = timezone.now()
                client.total_packets += 1
                client.save(update_fields=["status", "last_seen", "total_packets"])

        except Exception as e:
            logger.error(f"Error updating device status: {e}")

    def handle_message(self, topic: str, payload: dict):
        """Main message handler - processes incoming MQTT messages."""
        try:
            # Handle status messages (LWT) `device/status/{CLIENT_ID}`
            if topic.startswith("device/status/"):
                self.handle_status_message(topic, payload)
                return

            # Handle sensor data message `device/sensors/{CLIENT_ID}/*`

            logger.debug(f"📩 {topic}: {str(payload)[:100]}...")

            # Save to PostgreSQL with transaction
            with transaction.atomic():
                self.update_device_status_table(topic)

            # Save to MongoDB asynchronously (non-blocking)
            if self.mongo_client:
                try:
                    mongo_id = self.mongo_client.store_mqtt_packet(
                        topic=topic,
                        payload=payload,
                    )
                    if mongo_id:
                        logger.debug(f"✓ Also stored in MongoDB (ID: {mongo_id})")

                except Exception as mongo_error:
                    logger.warning(f"⚠ MongoDB storage failed: {mongo_error}")

        except Exception as e:
            logger.error(f"✗ Error processing message: {e}")

    def handle_status_message(self, topic: str, payload: dict):
        """Handle client status messages from LWT."""
        try:
            # Extract client_id from topic: device/status/{client_id}
            _, _, client_id = topic.split("/")

            status = payload.get("status", "unknown")

            # Update or create client status entry
            client, created = MQTTClientStatus.objects.get_or_create(
                client_id=client_id,
                defaults={
                    "status": status,
                    "first_seen": timezone.now(),
                    "total_packets": 0,
                },
            )

            if not created:
                client.status = status
                client.last_seen = timezone.now()
                client.save(update_fields=["status", "last_seen"])

            status_icon = "🟢" if status == "online" else "🔴"
            logger.info(f"{status_icon} Client '{client_id}' status: {status}")

        except Exception as e:
            logger.error(f"✗ Error processing status message: {e}")

    def start(self):
        """Start the MQTT to database bridge."""
        logger.info("Starting MQTT to Database Bridge...")

        # Initialize MongoDB connection
        try:
            self.mongo_client = MongoDBClient()
            if not self.mongo_client.connect():
                logger.warning(
                    "⚠ Failed to connect to MongoDB - continuing with PostgreSQL only"
                )
                self.mongo_client = None
            else:
                logger.info("✓ Connected to MongoDB")
        except Exception as e:
            logger.warning(
                f"⚠ MongoDB connection failed: {e} - continuing with PostgreSQL only"
            )
            self.mongo_client = None

        # Create and connect subscriber
        self.subscriber = MQTTClient(
            client_id="mqtt_db_bridge", host=self.broker_host, port=self.broker_port
        )
        self.subscriber.set_message_callback(self.handle_message)

        # Connect first, then subscribe
        if not self.subscriber.connect():
            logger.error("Failed to connect to MQTT broker")
            return False

        # Subscribe to sensor and status topics
        self.subscriber.subscribe("device/sensors/#")
        self.subscriber.subscribe("device/status/#")
        logger.info("✓ Listening for device sensors and status topics")

        self.running = True

        db_info = []
        db_info.append("PostgreSQL")
        if self.mongo_client:
            db_info.append("MongoDB")

        logger.info(
            f"✓ Bridge running on {self.broker_host}:{self.broker_port}, "
            f"monitoring `device/sensors/#` and `device/status/#`"
        )
        logger.info(f"✓ Storing data in: {', '.join(db_info)}")
        return True

    def stop(self):
        """Stop the bridge."""
        logger.info("Stopping MQTT to Database Bridge...")
        self.running = False

        if self.subscriber:
            self.subscriber.disconnect()

        # Close MongoDB connection
        if self.mongo_client:
            self.mongo_client.disconnect()

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
    parser.add_argument(
        "--host", type=str, default="localhost", help="MQTT broker host"
    )
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")

    args = parser.parse_args()
    bridge = MQTTDatabaseBridge(broker_host=args.host, broker_port=args.port)

    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda *_: (bridge.stop(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda *_: (bridge.stop(), sys.exit(0)))

    bridge.run()


if __name__ == "__main__":
    main()
