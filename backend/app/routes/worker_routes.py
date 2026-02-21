from __future__ import annotations

import datetime as dt
import math
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ASCENDING
from pymongo.database import Database

from backend.app.auth import require_role
from backend.app.database import get_db
from backend.app.schemas import WorkerLocationIn, WorkerOut

router = APIRouter(prefix="/workers", tags=["workers"])


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


@router.post("/location")
def update_my_location(
    payload: WorkerLocationIn,
    worker: Annotated[dict, Depends(require_role("worker"))],
    db: Annotated[Database, Depends(get_db)],
):
    # Keep consistent with the rest of the app: reject very low-accuracy GPS.
    if payload.accuracy > 100:
        raise HTTPException(status_code=400, detail="Location accuracy too low (>100m)")

    updated_at = dt.datetime.utcnow()
    db["users"].update_one(
        {"id": int(worker["id"]), "role": "worker"},
        {
            "$set": {
                "current_latitude": float(payload.latitude),
                "current_longitude": float(payload.longitude),
                "current_accuracy": float(payload.accuracy),
                "location_updated_at": updated_at,
            }
        },
    )
    worker.update(
        {
            "current_latitude": float(payload.latitude),
            "current_longitude": float(payload.longitude),
            "current_accuracy": float(payload.accuracy),
            "location_updated_at": updated_at,
        }
    )
    return {"ok": True, "location_updated_at": updated_at}


@router.get("", response_model=list[WorkerOut])
def list_workers(
    supervisor: Annotated[dict, Depends(require_role("supervisor"))],
    db: Annotated[Database, Depends(get_db)],
    district: Optional[str] = None,
    only_available: bool = True,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    max_age_sec: int = 900,
):
    if not supervisor.get("district"):
        raise HTTPException(status_code=400, detail="Supervisor district not set")

    if district is None:
        district = supervisor.get("district")
    elif district != supervisor.get("district"):
        raise HTTPException(status_code=403, detail="Forbidden")

    query: dict = {"role": "worker"}
    if district:
        query["district"] = district
    if only_available:
        query["is_available"] = True

    workers = list(db["users"].find(query).sort("id", ASCENDING))

    now = dt.datetime.utcnow()
    items: list[tuple[dict, Optional[int]]] = []
    for w in workers:
        dist_m: Optional[int] = None
        if lat is not None and lon is not None:
            if (
                w.get("current_latitude") is not None
                and w.get("current_longitude") is not None
                and w.get("location_updated_at") is not None
            ):
                age = (now - w["location_updated_at"]).total_seconds()
                if age <= float(max_age_sec):
                    dist_m = int(
                        _haversine_m(float(lat), float(lon), float(w["current_latitude"]), float(w["current_longitude"]))
                    )
        items.append((w, dist_m))

    # Sort by distance when applicable; unknown/stale locations go last.
    if lat is not None and lon is not None:
        items.sort(
            key=lambda t: (t[1] is None, t[1] if t[1] is not None else 10**12, int(t[0].get("id", 0)))
        )

    return [
        WorkerOut(
            id=int(w.get("id", 0)),
            name=str(w.get("name", "")),
            phone=w.get("phone"),
            district=w.get("district"),
            is_available=bool(w.get("is_available", False)),
            distance_m=dist_m,
            location_updated_at=w.get("location_updated_at"),
        )
        for (w, dist_m) in items
    ]

