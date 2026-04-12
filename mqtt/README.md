# MQTT Broker and Clients

This directory contains a local MQTT broker implementation using Mosquitto and Python MQTT clients using paho-mqtt.

## Prerequisites

Install Mosquitto broker:

**macOS:**
```bash
brew install mosquitto
```

**Ubuntu/Debian:**
```bash
sudo apt-get install mosquitto mosquitto-clients
```

## Usage

### 1. Start the Broker

```bash
uv run mqtt/broker.py
```

Or with custom port:

```bash
uv run mqtt/broker.py --port 8883
```

Or with custom configuration file:

```bash
uv run mqtt/broker.py --config /path/to/custom.conf
```

**Configuration:** The broker uses [mosquitto.conf](mosquitto.conf) in this directory by default. You can modify this file to customize broker settings like authentication, TLS, persistence, etc.

## Topics

- `device/sensors/{CLIENT_ID}/{location}/temperature` - Temperature sensor data readings from particular client
- `device/sensors/#` - All sensor data
- `device/control/{CLIENT_ID}` - Device control commands
- `device/status/{CLIENT_ID}` - Device status information

### 2. Run MQTT Client

```bash
# Subscribe to device topics (listens for control commands and sensor data)
uv run -m mqtt.client_cli

# Subscribe to specific topic
uv run -m mqtt.client_cli --topic "device/sensors/#"

# Publish a message
uv run -m mqtt.client_cli --publish "test/topic" --message "Hello World"
uv run -m mqtt.client_cli --publish "device/control/{CLIENT_ID}" --message "shutdown"

# Publish weather data for cities (LON, PRG, BRN)
uv run -m mqtt.client_cli --city LON
uv run -m mqtt.client_cli --city PRG
uv run -m mqtt.client_cli --city BRN

# Custom client ID with subscription
uv run -m mqtt.client_cli --client-id "my_device" --topic "device/sensors/#"
```

### 4. Run Complete Example

```bash
uv run mqtt/test/example.py
```

## Python API

### Broker

```python
from mqtt.broker import MQTTBroker

broker = MQTTBroker(port=1883)
broker.start()

# Later...
broker.stop()
```

### Publisher

```python
from mqtt.client import MQTTClient
from mqtt.weather import City

publisher = MQTTClient(client_id="my_publisher")
publisher.connect()

# Publish simple message
publisher.publish("my/topic", "Hello MQTT")

# Publish weather data for cities
publisher.publish_sensor_data("LON")  # London
publisher.publish_sensor_data("PRG")  # Prague
publisher.publish_sensor_data("BRN")  # Brno

publisher.disconnect()
```

### Subscriber

```python
from mqtt.client import MQTTSubscriber

def on_message(topic, payload):
    print(f"Received: {topic} -> {payload}")

subscriber = MQTTSubscriber(client_id="my_subscriber")
subscriber.set_message_callback(on_message)
subscriber.connect()
subscriber.subscribe("my/topic")

# Keep running...
```

## MQTT to Database Integration

**📥 Store MQTT messages in PostgreSQL automatically!**

This project includes a bridge service that stores MQTT messages in PostgreSQL:

### Quick Start

```bash
# 1. Run database migrations
cd backend
uv run python manage.py migrate

# 2. Start the MQTT broker (in one terminal)
uv run mqtt/broker.py

# 3. Start the database service (in another terminal)
uv run mqtt/client_subscribe.py

# 4. Publish data (automatically stored in database)
uv run -m mqtt.client_cli --city LON
```

### Test Complete Example

```bash
# Run the complete test with broker, database service, and multiple publishers
uv run mqtt/test/example_db_test.py
```
