#!/usr/bin/env python3
"""
One-time migration: load seed data from knowledge_base.json into MongoDB.

Usage:
    python migrate_to_mongo.py                          # uses default path
    python migrate_to_mongo.py /path/to/custom.json     # custom JSON file
"""

import sys
from rag.database import migrate_from_json, count_cases


def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 50)
    print("  IT Helpdesk — JSON → MongoDB Migration")
    print("=" * 50)

    inserted = migrate_from_json(json_path)

    total = count_cases()
    print(f"\nDone. Total cases in MongoDB: {total}")
    print(f"New cases inserted this run:  {inserted}")
    print("\nYou can now safely remove the JSON file or keep it as backup.")


if __name__ == "__main__":
    main()
