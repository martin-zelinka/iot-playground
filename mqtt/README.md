# MQTT Broker and Clients

This directory contains a local MQTT broker implementation using Mosquitto and Python MQTT clients using paho-mqtt.


### Topics

- `device/sensors/{CLIENT_ID}/{location}/temperature` - Temperature sensor data readings from particular client
- `device/sensors/#` - All sensor data
- `device/control/{CLIENT_ID}` - Device control commands
- `device/status/{CLIENT_ID}` - Device status information

### Run MQTT Client with CLI

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

### Test Complete Example

```bash
# Run the complete test with broker, database service, and multiple publishers
uv run -m mqtt.test.example_db_test
```
