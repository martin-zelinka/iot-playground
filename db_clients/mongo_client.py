#!/usr/bin/env python3
"""MongoDB client for storing MQTT, ModbusTCP packets."""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client for MQTT data storage with connection management."""

    def __init__(self):
        """Initialize MongoDB client with credentials from .env file."""
        self.host = os.getenv("MONGODB_HOST", "localhost")
        self.port = int(os.getenv("MONGODB_PORT", "27017"))
        self.database_name = os.getenv("MONGODB_DB", "iot_platform")
        self.username = os.getenv("MONGODB_USER", "")
        self.password = os.getenv("MONGODB_PASSWORD", "")

        self.client: Optional[MongoClient] = None
        self.db = None
        self.connected = False

        # Collection names
        self.device_data_collection = "device_data"

    def connect(self) -> bool:
        """Establish MongoDB connection with retry logic."""
        try:
            # Build connection string
            if self.username and self.password:
                connection_string = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
            else:
                connection_string = f"mongodb://{self.host}:{self.port}/"

            # Create client with connection settings
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10,
            )

            # Test connection
            self.client.admin.command('ping')

            # Get database
            self.db = self.client[self.database_name]
            self.connected = True

            # Create indexes
            self._create_indexes()

            logger.info(f"✓ Connected to MongoDB at {self.host}:{self.port}/{self.database_name}")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"✗ Failed to connect to MongoDB: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("MongoDB connection closed")

    def _create_indexes(self):
        """Create indexes for better query performance."""
        try:
            # Device data indexes
            self.db[self.device_data_collection].create_index([("topic", 1), ("received_at", -1)])
            self.db[self.device_data_collection].create_index([("received_at", -1)])
            self.db[self.device_data_collection].create_index([("topic", 1)])

            logger.info("✓ MongoDB indexes created")

        except Exception as e:
            logger.warning(f"Warning: Could not create indexes: {e}")

    def store_mqtt_packet(self, topic: str, payload: Dict[str, Any]) -> Optional[str]:
        """Store an MQTT packet in MongoDB device_data collection."""
        if not self.connected:
            logger.warning("Cannot store packet: Not connected to MongoDB")
            return None

        try:
            document = {
                "source": topic.split('/')[2],
                "protocol": "mqtt",
                "payload":
                    {
                        "topic": topic,
                        "message": payload
                    },
                "received_at": datetime.now(),
            }

            result = self.db[self.device_data_collection].insert_one(document)
            logger.debug(f"Stored packet in MongoDB with ID: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error storing packet in MongoDB: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.connected:
            return {}

        try:
            stats = {
                "device_data_count": self.db[self.device_data_collection].count_documents({}),
                "database_size": self.db.command("dbstats")["dataSize"],
                "collections": self.db.list_collection_names(),
            }
            return stats

        except Exception as e:
            logger.error(f"Error getting MongoDB stats: {e}")
            return {}


def create_mongo_client() -> MongoDBClient:
    """Factory function to create and connect MongoDB client."""
    client = MongoDBClient()
    if not client.connect():
        raise ConnectionError("Failed to connect to MongoDB")
    return client