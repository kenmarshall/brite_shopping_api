from pymongo import MongoClient
from pymongo.database import Database
import certifi
import os


# Load MongoDB URI and database name from environment variables
# Use `or` to handle empty strings from render.yaml placeholders
MONGO_URI = os.getenv("MONGO_URI") or "mongodb://localhost:27017/brite_shopping"
MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME") or "brite_shopping"

_client = None
_db = None


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where(),
        )
    return _client


def get_db() -> Database:
    global _db
    if _db is None:
        _db = _get_client()[MONGO_DATABASE_NAME]
    return _db


class _LazyDB:
    """Proxy that defers MongoClient creation until first attribute access."""

    def __getattr__(self, name):
        return getattr(get_db(), name)

    def __getitem__(self, name):
        return get_db()[name]


# Backwards-compatible module-level `db` — lazy, no connection at import time
db = _LazyDB()