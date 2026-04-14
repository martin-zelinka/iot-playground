"""
MongoDB client for devices app.
Simple client for querying device_data collection.
"""

import logging
from typing import Any

from django.conf import settings
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, PyMongoError

logger = logging.getLogger(__name__)


class MongoDBClient:
    """Singleton MongoDB client for device_data collection."""

    _instance = None
    _client = None
    _db = None
    _collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> Collection | None:
        """Establish connection to MongoDB."""
        if self._client is not None:
            return self._collection

        try:
            mongo_config = settings.MONGODB_DATABASES["default"]
            host = mongo_config["HOST"]
            port = mongo_config["PORT"]
            db_name = mongo_config["NAME"]
            username = mongo_config.get("USER")
            password = mongo_config.get("PASSWORD")

            if username and password:
                connection_string = (
                    f"mongodb://{username}:{password}@{host}:{port}/{db_name}"
                )
            else:
                connection_string = f"mongodb://{host}:{port}/{db_name}"

            self._client = MongoClient(connection_string)
            self._client.admin.command("ping")
            self._db = self._client[db_name]
            self._collection = self._db["device_data"]
            logger.info(f"Connected to MongoDB: {db_name}.device_data")

            return self._collection

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_collection(self) -> Collection:
        """Get the device_data collection."""
        if self._collection is None:
            self.connect()
        return self._collection

    def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            self._collection = None
            logger.info("MongoDB connection closed")


def get_device_data(
    source: str | None = None, limit: int | None = None, skip: int | None = None
) -> list[dict[str, Any]]:
    """Get device data documents, optionally filtered by source."""
    try:
        client = MongoDBClient()
        collection = client.get_collection()

        query = {}
        if source:
            query["source"] = source

        cursor = collection.find(query).sort("received_at", -1)

        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        return list(cursor)

    except PyMongoError as e:
        logger.error(f"Error querying device_data: {e}")
        raise


def get_latest_by_source(source: str) -> dict[str, Any] | None:
    """Get the latest document for a specific source."""
    try:
        client = MongoDBClient()
        collection = client.get_collection()
        return collection.find_one({"source": source}, sort=[("received_at", -1)])

    except PyMongoError as e:
        logger.error(f"Error getting latest data for source {source}: {e}")
        raise
