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

- `sensors/{self.client_id}/{location}/temperature` - Temperature/weather readings
- `sensors/#` - All sensor data
- `device/{CLIENT_ID}/control` - Device control commands
- `device/{CLIENT_ID}/status` - Device status information

### 2. Run MQTT Client

```bash
# Subscribe to topics (listens for control commands)
uv run mqtt/client_cli.py --topic "sensors/#"

# Publish a message
uv run mqtt/client_cli.py --publish "test/topic" --message "Hello World"
uv run mqtt/client_cli.py --publish "device/{CLIENT_ID}/control" --message "shutdown"

# Publish weather data for cities (LON, PRG, BRN)
uv run mqtt/client_cli.py --city LON
uv run mqtt/client_cli.py --city PRG
uv run mqtt/client_cli.py --city BRN

# Custom client ID with subscription
uv run mqtt/client_cli.py --client-id "my_device" --topic "sensors/#"
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
uv run mqtt/client_cli.py --city LON
```

### Test Complete Example

```bash
# Run the complete test with broker, database service, and multiple publishers
uv run mqtt/test/example_db_test.py
```
