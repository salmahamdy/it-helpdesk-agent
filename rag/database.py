"""
MongoDB database layer for the IT Helpdesk knowledge base.

Replaces the JSON file store with MongoDB. Supports:
- CRUD operations on cases
- Bulk insert for migration
- Text index for keyword search
- Metadata queries (by category, escalation, etc.)
"""

import os
import json
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, ReturnDocument
from pymongo.collection import Collection
from config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION, KNOWLEDGE_BASE_PATH


_client: MongoClient | None = None
_db = None
_collection: Collection | None = None


def get_collection() -> Collection:
    """Return the cases collection, creating indexes on first call."""
    global _client, _db, _collection
    if _collection is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _client[MONGO_DB_NAME]
        _collection = _db[MONGO_COLLECTION]
        _ensure_indexes(_collection)
    return _collection


def _ensure_indexes(col: Collection) -> None:
    """Create indexes for common query patterns."""
    col.create_index("case_id", unique=True)
    col.create_index("issue_class")
    col.create_index("escalation_required")
    col.create_index("created_at")
    col.create_index(
        [("issue", "text"), ("resolution", "text"), ("tags", "text")],
        name="text_search_index",
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def get_all_cases() -> list[dict]:
    """Return every case (without Mongo's internal _id)."""
    col = get_collection()
    return list(col.find({}, {"_id": 0}))


def get_case(case_id: str) -> dict | None:
    """Fetch a single case by its case_id."""
    col = get_collection()
    return col.find_one({"case_id": case_id}, {"_id": 0})


def _next_case_id(col: Collection) -> str:
    """Return a unique, sequential case_id using an atomic counter.

    Uses find_one_and_update($inc) on a 'counters' collection, which is atomic
    server-side, so concurrent inserts can never receive the same id (the old
    count_documents()+1 approach raced and tripped the unique index).

    The counter is lazily seeded to the current max numeric case_id so it does
    not collide with seed cases created during the JSON->Mongo migration.
    """
    counters = col.database["counters"]

    if counters.find_one({"_id": "case_id"}) is None:
        max_seq = 0
        for cid in col.distinct("case_id"):
            try:
                max_seq = max(max_seq, int(cid))
            except (TypeError, ValueError):
                continue  # ignore non-numeric ids (e.g. legacy UUIDs)
        # $setOnInsert + upsert makes the seed itself atomic: only one writer wins.
        counters.update_one(
            {"_id": "case_id"},
            {"$setOnInsert": {"seq": max_seq}},
            upsert=True,
        )

    doc = counters.find_one_and_update(
        {"_id": "case_id"},
        {"$inc": {"seq": 1}},
        return_document=ReturnDocument.AFTER,
    )
    return str(doc["seq"]).zfill(3)


def insert_case(case: dict) -> str:
    """
    Insert a new case and return its case_id.
    Auto-generates case_id and created_at if missing.
    """
    col = get_collection()

    if "case_id" not in case:
        case["case_id"] = _next_case_id(col)

    case.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    case.setdefault("source", "agent")
    case.setdefault("verified", False)
    case.setdefault("tags", [])

    col.insert_one(case)
    return case["case_id"]


def update_case(case_id: str, updates: dict) -> bool:
    """Update fields on an existing case. Returns True if matched."""
    col = get_collection()
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = col.update_one({"case_id": case_id}, {"$set": updates})
    return result.matched_count > 0


def delete_case(case_id: str) -> bool:
    """Delete a case by case_id. Returns True if deleted."""
    col = get_collection()
    result = col.delete_one({"case_id": case_id})
    return result.deleted_count > 0


def search_by_text(query: str, limit: int = 10) -> list[dict]:
    """Full-text keyword search using MongoDB's text index."""
    col = get_collection()
    cursor = col.find(
        {"$text": {"$search": query}},
        {"_id": 0, "score": {"$meta": "textScore"}},
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)
    return list(cursor)


def search_by_category(issue_class: str) -> list[dict]:
    """Return all cases matching an issue category."""
    col = get_collection()
    return list(col.find({"issue_class": issue_class}, {"_id": 0}))


def count_cases() -> int:
    """Total number of cases in the collection."""
    return get_collection().count_documents({})


# ---------------------------------------------------------------------------
# Migration helper
# ---------------------------------------------------------------------------

def migrate_from_json(json_path: str | None = None) -> int:
    """
    One-time import: read the seed JSON file and bulk-insert into MongoDB.
    Skips cases whose case_id already exists. Returns number inserted.
    """
    path = json_path or KNOWLEDGE_BASE_PATH
    if not os.path.exists(path):
        print(f"[migrate] JSON file not found at {path}")
        return 0

    with open(path, "r") as f:
        cases = json.load(f)

    col = get_collection()
    inserted = 0
    for case in cases:
        # Map the old "id" field to "case_id"
        case_id = case.pop("id", None)
        if case_id:
            case["case_id"] = case_id

        case.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        case.setdefault("source", "seed")
        case.setdefault("verified", True)
        case.setdefault("tags", [])

        if not col.find_one({"case_id": case["case_id"]}):
            col.insert_one(case)
            inserted += 1

    print(f"[migrate] Inserted {inserted}/{len(cases)} cases from {path}")
    return inserted
