from __future__ import annotations

import datetime as dt
import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pymongo import DESCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from backend.app.auth import get_current_user
from backend.app.database import get_db, get_next_id
from backend.app.schemas import ValidationCandidateOut, ValidationVoteIn

router = APIRouter(prefix="/validation", tags=["validation"])


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Approx Earth radius in meters
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


@router.get("/nearby", response_model=list[ValidationCandidateOut])
def nearby_candidates(
    lat: float,
    lon: float,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Database, Depends(get_db)],
    radius_m: int = 3000,
):
    # Pull recent reports; filter by distance in Python to keep SQLite simple.
    rows = list(
        db["reports"]
        .find({"status": {"$in": ["submitted", "accepted", "assigned"]}})
        .sort("created_at", DESCENDING)
        .limit(200)
    )

    voted_report_ids = set(
        int(v["report_id"]) for v in db["validations"].find({"user_id": int(user["id"])}, {"report_id": 1})
    )

    out: list[ValidationCandidateOut] = []
    for r in rows:
        if int(r.get("user_id", 0)) == int(user["id"]):
            continue
        rid = int(r.get("id", 0))
        if rid in voted_report_ids:
            continue
        if _haversine_m(lat, lon, float(r.get("latitude", 0.0)), float(r.get("longitude", 0.0))) <= float(radius_m):
            out.append(
                ValidationCandidateOut(
                    report_id=rid,
                    latitude=float(r.get("latitude", 0.0)),
                    longitude=float(r.get("longitude", 0.0)),
                    district=str(r.get("district") or ""),
                    description=str(r.get("description") or ""),
                    severity=r.get("severity", "Low"),
                    created_at=r.get("created_at"),
                )
            )
    return out[:20]


@router.post("/{report_id}/vote")
def vote(
    report_id: int,
    payload: ValidationVoteIn,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Database, Depends(get_db)],
):
    report = db["reports"].find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if int(report.get("user_id", 0)) == int(user["id"]):
        raise HTTPException(status_code=400, detail="Cannot vote on your own report")

    vdoc = {
        "id": get_next_id(db, "validations"),
        "report_id": int(report_id),
        "user_id": int(user["id"]),
        "vote": 1 if payload.vote else 0,
        "created_at": dt.datetime.utcnow(),
    }
    try:
        db["validations"].insert_one(vdoc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Already voted")

    return {"ok": True}
