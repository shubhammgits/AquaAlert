from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.database import get_db
from backend.app.models import Report, Validation
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
    user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    radius_m: int = 3000,
):
    # Pull recent reports; filter by distance in Python to keep SQLite simple.
    rows = (
        db.execute(
            select(Report)
            .where(Report.status.in_(["submitted", "accepted", "assigned"]))
            .order_by(desc(Report.created_at))
            .limit(200)
        )
        .scalars()
        .all()
    )

    voted_report_ids = set(
        db.execute(select(Validation.report_id).where(Validation.user_id == user.id)).scalars().all()
    )

    out: list[ValidationCandidateOut] = []
    for r in rows:
        if r.user_id == user.id:
            continue
        if r.id in voted_report_ids:
            continue
        if _haversine_m(lat, lon, r.latitude, r.longitude) <= float(radius_m):
            out.append(
                ValidationCandidateOut(
                    report_id=r.id,
                    latitude=r.latitude,
                    longitude=r.longitude,
                    district=r.district or "",
                    description=r.description or "",
                    severity=r.severity,  # type: ignore[arg-type]
                    created_at=r.created_at,
                )
            )
    return out[:20]


@router.post("/{report_id}/vote")
def vote(
    report_id: int,
    payload: ValidationVoteIn,
    user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot vote on your own report")

    v = Validation(report_id=report_id, user_id=user.id, vote=1 if payload.vote else 0)
    db.add(v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Already voted")

    return {"ok": True}
