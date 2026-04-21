from __future__ import annotations

import os
from typing import Generator
from urllib.parse import quote_plus

from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import InvalidURI
from pymongo.database import Database


def _mongo_uri() -> str:
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017")


def _mongo_db_name() -> str:
    return os.getenv("MONGODB_DB", "aquaalert")


def _mongo_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _encode_mongo_uri_credentials(uri: str) -> str:
    """Best-effort fix for URIs with raw usernames/passwords containing reserved chars."""
    if "://" not in uri or "@" not in uri:
        return uri

    scheme, rest = uri.split("://", 1)
    userinfo, hostpart = rest.rsplit("@", 1)
    if ":" not in userinfo:
        return uri

    username, password = userinfo.split(":", 1)
    return f"{scheme}://{quote_plus(username)}:{quote_plus(password)}@{hostpart}"


_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        uri = _mongo_uri()
        client_kwargs = {
            "serverSelectionTimeoutMS": _mongo_int_env("MONGO_SERVER_SELECTION_TIMEOUT_MS", 5000),
            "connectTimeoutMS": _mongo_int_env("MONGO_CONNECT_TIMEOUT_MS", 5000),
            "socketTimeoutMS": _mongo_int_env("MONGO_SOCKET_TIMEOUT_MS", 20000),
            "maxPoolSize": _mongo_int_env("MONGO_MAX_POOL_SIZE", 50),
            "minPoolSize": _mongo_int_env("MONGO_MIN_POOL_SIZE", 0),
            "retryWrites": True,
        }
        try:
            _client = MongoClient(uri, **client_kwargs)
        except InvalidURI:
            _client = MongoClient(_encode_mongo_uri_credentials(uri), **client_kwargs)
    return _client


def get_mongo_database() -> Database:
    return get_mongo_client()[_mongo_db_name()]


def get_db() -> Generator[Database, None, None]:
    # Keep the dependency name `get_db` so routes/auth don't need to change.
    yield get_mongo_database()


def get_next_id(db: Database, sequence: str) -> int:
    """Atomic, auto-incrementing integer ids (to keep existing API stable)."""
    doc = db["counters"].find_one_and_update(
        {"_id": sequence},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc.get("seq", 1))


def ensure_indexes(db: Database) -> None:
    """Create required indexes (safe to call repeatedly)."""
    users = db["users"]
    reports = db["reports"]
    validations = db["validations"]

    users.create_index([("id", ASCENDING)], unique=True)
    users.create_index([("email", ASCENDING)], unique=True)
    users.create_index([("role", ASCENDING)])
    users.create_index([("district", ASCENDING)])
    users.create_index([("is_available", ASCENDING)])

    reports.create_index([("id", ASCENDING)], unique=True)
    reports.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    reports.create_index([("district", ASCENDING), ("created_at", DESCENDING)])
    reports.create_index([("status", ASCENDING)])
    reports.create_index([("cluster_id", ASCENDING)])
    reports.create_index([("assigned_worker_id", ASCENDING), ("assigned_at", DESCENDING)])

    validations.create_index([("id", ASCENDING)], unique=True)
    validations.create_index([("user_id", ASCENDING)])
    validations.create_index([("report_id", ASCENDING)])
    validations.create_index([("report_id", ASCENDING), ("user_id", ASCENDING)], unique=True)

