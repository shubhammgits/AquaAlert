from __future__ import annotations

import datetime as dt
import math
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.auth import require_role
from backend.app.database import get_db
from backend.app.models import User
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
    worker: Annotated[User, Depends(require_role("worker"))],
    db: Annotated[Session, Depends(get_db)],
):
    # Keep consistent with the rest of the app: reject very low-accuracy GPS.
    if payload.accuracy > 100:
        raise HTTPException(status_code=400, detail="Location accuracy too low (>100m)")

    worker.current_latitude = float(payload.latitude)
    worker.current_longitude = float(payload.longitude)
    worker.current_accuracy = float(payload.accuracy)
    worker.location_updated_at = dt.datetime.utcnow()
    db.add(worker)
    db.commit()
    return {"ok": True, "location_updated_at": worker.location_updated_at}


@router.get("", response_model=list[WorkerOut])
def list_workers(
    supervisor: Annotated[User, Depends(require_role("supervisor"))],
    db: Annotated[Session, Depends(get_db)],
    district: Optional[str] = None,
    only_available: bool = True,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    max_age_sec: int = 900,
):
    if not supervisor.district:
        raise HTTPException(status_code=400, detail="Supervisor district not set")

    if district is None:
        district = supervisor.district
    elif district != supervisor.district:
        raise HTTPException(status_code=403, detail="Forbidden")

    q = select(User).where(User.role == "worker")
    if district:
        q = q.where(User.district == district)
    if only_available:
        q = q.where(User.is_available == True)  # noqa: E712
    workers = db.execute(q).scalars().all()

    now = dt.datetime.utcnow()
    items: list[tuple[User, Optional[int]]] = []
    for w in workers:
        dist_m: Optional[int] = None
        if lat is not None and lon is not None:
            if (
                w.current_latitude is not None
                and w.current_longitude is not None
                and w.location_updated_at is not None
            ):
                age = (now - w.location_updated_at).total_seconds()
                if age <= float(max_age_sec):
                    dist_m = int(_haversine_m(float(lat), float(lon), float(w.current_latitude), float(w.current_longitude)))
        items.append((w, dist_m))

    # Sort by distance when applicable; unknown/stale locations go last.
    if lat is not None and lon is not None:
        items.sort(key=lambda t: (t[1] is None, t[1] if t[1] is not None else 10**12, t[0].id))

    return [
        WorkerOut(
            id=w.id,
            name=w.name,
            phone=w.phone,
            district=w.district,
            is_available=w.is_available,
            distance_m=dist_m,
            location_updated_at=w.location_updated_at,
        )
        for (w, dist_m) in items
    ]

