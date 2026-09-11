"""Single MongoDB connection shared by the whole application."""
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError(
                "MONGODB_URI is missing. Copy .env.example to .env and fill it in."
            )
        _client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    return _client


def get_db():
    return get_client()[os.getenv("DB_NAME", "campus_events")]


def users():
    return get_db()["users"]


def events():
    return get_db()["events"]
