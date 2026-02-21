from __future__ import annotations

import os
from pathlib import Path

from pymongo import MongoClient

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass

uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DB", "aquaalert")

print("MONGODB_URI=", uri)
print("MONGODB_DB =", db_name)

client = MongoClient(uri, serverSelectionTimeoutMS=8000)
db = client[db_name]

print("ping:", client.admin.command("ping"))

users = db["users"]
reports = db["reports"]

print("total users:", users.count_documents({}))
print("workers:", users.count_documents({"role": "worker"}))
print("workers available:", users.count_documents({"role": "worker", "is_available": True}))

print("distinct worker districts:", users.distinct("district", {"role": "worker"}))

supervisors = list(users.find({"role": "supervisor"}, {"_id": 0, "id": 1, "name": 1, "district": 1}))
print("supervisors:", supervisors)

print("\ndistinct report districts:", reports.distinct("district", {}))
print("accepted report districts:", reports.distinct("district", {"status": "accepted"}))

sample_reports = list(
    reports.find({"status": {"$in": ["submitted", "accepted", "assigned"]}}, {"_id": 0, "id": 1, "status": 1, "district": 1})
    .sort("id", -1)
    .limit(10)
)
print("sample reports:", sample_reports)

for d in ["North", "north", "NORTH", "North ", " North"]:
    q = {"role": "worker", "district": d, "is_available": True}
    print("query", q, "=>", users.count_documents(q))

print("\nSample workers (up to 10):")
for w in users.find({"role": "worker"}, {"_id": 0, "id": 1, "name": 1, "district": 1, "is_available": 1}).limit(10):
    print(w)
