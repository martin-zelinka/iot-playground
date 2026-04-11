# Devices - MongoDB Integration

Simple Django app to store and retrieve MQTT device data from MongoDB.

## Document Structure

The `device_data` collection stores documents like:

```json
{
  "source": "weather_publisher_5096",
  "protocol": "mqtt",
  "payload": {
    "topic": "sensors/weather_publisher_5096/PRG/temperature",
    "message": {
      "data": "{'client_id': 'weather_publisher_5096', 'location': 'PRG', 'temperature': 7.9, 'unit': '°C', 'timestamp': 1775940005.525998}"
    }
  },
  "received_at": {
    "$date": "2026-04-11T20:40:05.560Z"
  }
}
```

## Setup

### Environment Variables

```env
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=iot_platform
MONGODB_USER=
MONGODB_PASSWORD=
```

## API Endpoints

### List Device Data
```
GET /api/devices/?source=weather_publisher_5096&limit=50&skip=0
```

### Get Latest by Source
```
GET /api/devices/weather_publisher_5096/latest/
```

### Create Device Data
```
POST /api/devices/create/
Content-Type: application/json

{
  "source": "weather_publisher_5096",
  "protocol": "mqtt",
  "payload": {
    "topic": "sensors/weather_publisher_5096/PRG/temperature",
    "message": {
      "data": "{'temperature': 8.5}"
    }
  }
}
```

## Files

- `django_api/mongo/mongodb_client.py`: MongoDB connection and query functions
- `devices/views.py`: Django views for API endpoints
- `devices/urls.py`: URL routing configuration

## Usage

```python
from django_api.mongo.mongodb_client import get_device_data, get_latest_by_source, insert_device_data

# Get all data (with optional filtering)
data = get_device_data(source="weather_publisher_5096", limit=10)

# Get latest for a source
latest = get_latest_by_source("weather_publisher_5096")

# Insert new data
insert_device_data({
    "source": "weather_publisher_5096",
    "protocol": "mqtt",
    "payload": {...}
})
```
