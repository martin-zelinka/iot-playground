## MQTT + DJANGO project



**macOS:**
```bash


brew install mosquitto

brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0

uv sync

uv run backend/manage.py runserver
uv run -m mqtt.test.example_db_test
```


**Docker commands**
```bash
docker-compose build --no-cache
docker-compose up

docker run -it -p 8000:8000 mqtt-playground-web bash
docker run -it -p 1883:1883 mqtt-playground-mqtt bash
uv run backend/manage.py runserver 0.0.0.0:8000
```