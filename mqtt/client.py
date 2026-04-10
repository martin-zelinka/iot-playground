#!/usr/bin/env python3
"""
Simplified MQTT Client with control topic support.
Listens on device/{CLIENT_ID}/control for shutdown commands.
"""

import json
import logging
import sys
import time
from typing import Any, Callable
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from mqtt.weather import City, get_weather

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MQTTClient:
    """Unified MQTT Client with publish, subscribe, and control topic support."""

    def __init__(
        self,
        client_id: str,
        host: str = "localhost",
        port: int = 1883,
        keepalive: int = 60,
        listen_for_control: bool = True
    ):
        self.client_id = client_id
        self.host = host
        self.port = port
        self.keepalive = keepalive
        self.listen_for_control = listen_for_control
        self.running = True
        self.message_callback = None

        # Create client
        self.client = mqtt.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=client_id
        )
        self._setup_callbacks()

    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        try:
            self.client.connect(self.host, self.port, self.keepalive)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

    def _setup_callbacks(self):
        """Setup MQTT client callbacks."""
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_message = self._on_message

    def _on_connect(self, _client, _userdata, _flags, reason_code, _properties):
        """Called when the client connects to the broker."""
        if reason_code == 0:
            logger.info(f"✓ Client '{self.client_id}' connected to broker")

            # Auto-subscribe to control topic
            if self.listen_for_control:
                control_topic = f"device/{self.client_id}/control"
                self.client.subscribe(control_topic)
                logger.info(f"✓ Listening on control topic: {control_topic}")
        else:
            logger.error(f"✗ Connection failed with code {reason_code}")

    def _on_disconnect(self, _client, _userdata, _flags, reason_code, _properties):
        """Called when the client disconnects from the broker."""
        if reason_code == 0:
            logger.info(f"Client '{self.client_id}' disconnected")
        else:
            logger.warning(f"Unexpected disconnect: {reason_code}")

    def _on_publish(self, _client, _userdata, mid, reason_code, _properties):
        """Called when a message is published."""
        logger.debug(f"Message published with ID: {mid}, code: {reason_code}")

    def _on_message(self, _client, _userdata, msg):
        """Called when a message is received."""
        try:
            payload = msg.payload.decode()

            # Try to parse as JSON
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                pass

            logger.info(f"📩 {self.client_id} -> Received on '{msg.topic}': {payload}")

            # Handle control messages
            if msg.topic == f"device/{self.client_id}/control":
                self._handle_control_message(payload)
                return

            # Call custom callback if set
            if self.message_callback:
                self.message_callback(msg.topic, payload)

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _handle_control_message(self, payload: Any):
        """Handle control messages on the device control topic."""
        try:
            # Handle both string and JSON payloads
            if isinstance(payload, dict):
                command = payload.get('command', payload)
            else:
                command = str(payload).lower()

            logger.info(f"🎛️  Control command received: {command}")

            if command in ['shutdown', 'stop', 'exit', 'quit']:
                logger.info("🛑 Shutdown command received, stopping client...")
                self.running = False
                self.disconnect()
                sys.exit(0)

            elif command == 'restart':
                logger.info("🔄 Restart command received...")
                self.disconnect()
                time.sleep(2)
                self.connect()

            elif command == 'status':
                status = {
                    "client_id": self.client_id,
                    "status": "running",
                    "host": self.host,
                    "port": self.port
                }
                self.publish(f"device/{self.client_id}/status", status)
                logger.info(f"📊 Status: {status}")

            else:
                logger.warning(f"❓ Unknown control command: {command}")

        except Exception as e:
            logger.error(f"Error handling control message: {e}")

    def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False):
        """
        Publish a message to a topic.

        Args:
            topic: MQTT topic to publish to
            payload: Message payload (will be JSON serialized if dict/list)
            qos: Quality of Service (0, 1, or 2)
            retain: Whether to retain the message on the broker
        """
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)

        result = self.client.publish(topic, payload, qos=qos, retain=retain)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"📤 {self.client_id} -> Published to '{topic}': {payload[:100]}...")
        else:
            logger.error(f"✗ Failed to publish to '{topic}'")

    def subscribe(self, topic: str, qos: int = 0):
        """Subscribe to a topic."""
        result = self.client.subscribe(topic, qos=qos)

        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"✓ Subscribed to '{topic}'")
        else:
            logger.error(f"✗ Failed to subscribe to '{topic}'")

    def set_message_callback(self, callback: Callable[[str, Any], None]):
        """Set a custom callback for received messages."""
        self.message_callback = callback

    def publish_sensor_data(self, location: City):
        """Publish sensor data in a standardized format."""
        payload = {
            "client_id": self.client_id,
            "location": location,
            "temperature": get_weather(location),
            "unit": "°C",
            "timestamp": time.time()
        }
        self.publish(f"sensors/{self.client_id}/{location}/temperature", payload)

    def run_forever(self):
        """Keep the client running and listening for messages."""
        try:
            logger.info("🔄 Client running... (Press Ctrl+C to stop)")
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️  Interrupted by user")
        finally:
            self.disconnect()

