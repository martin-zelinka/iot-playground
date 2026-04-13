# IoT playground

### MQTT Topics Architecture

![MQTT Schema](mqtt_schema.png)

### MQTT Clients:

**Sensor** connect with LWT (Last Will and Testament) enabled
- Automatically publish `online` status to `device/status/{CLIENT_ID}` on connect
- Publish sensor data `device/sensors/{CLIENT_ID}/{location}/temperature`
    - Temperature data from weather APIs (Open-Meteo)
    - Locations: LON (London), PRG (Prague), BRN (Brno)
- Subscribe to `device/control/{CLIENT_ID}` where we listen for shutdown event

**Database Bridge** dumping data from sensors clients:
- subscribe to `device/sensors/#` and stores data to **MongoDB** (iot_platform collection)
- subscribe to `device/status/#` and stores data to **PostgreSQL** (MQTTClientStatus model)

**Django mqtt client**:
- publish data to `device/control/{CLIENT_ID}` with `shutdown` msg for client we want to kill

---

### Setup & Run

**MacOS:**
```bash
brew install mosquitto

brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0

uv sync

uv run backend/manage.py runserver
uv run -m mqtt.test.example_db_test
```

**Docker:**
```bash
docker-compose build --no-cache
docker-compose up

docker run -it -p 8000:8000 mqtt-playground-web bash
docker run -it -p 1883:1883 mqtt-playground-mqtt bash
uv run backend/manage.py runserver 0.0.0.0:8000
```