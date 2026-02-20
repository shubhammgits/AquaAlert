from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user, require_role
from backend.app.database import get_db
from backend.app.models import Report, User
from backend.app.schemas import AnalysisOut, ReportCreateIn, ReportOut
from backend.app.services.ai_service import analyze_image
from backend.app.services.cluster_service import compute_cluster_id
from backend.app.services.qr_service import generate_qr_for_report

router = APIRouter(prefix="/reports", tags=["reports"])

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
IMAGES_DIR = STATIC_DIR / "images"
MAX_IMAGE_BYTES = 2 * 1024 * 1024


def _decode_data_url(data_url_or_b64: str) -> bytes:
    raw = data_url_or_b64.strip()
    if raw.startswith("data:"):
        try:
            raw = raw.split(",", 1)[1]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image data")
    try:
        return base64.b64decode(raw, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image")


def _to_report_out(report: Report) -> ReportOut:
    def _loads(val: str) -> list[str]:
        try:
            parsed = json.loads(val or "[]")
            return [str(x) for x in parsed] if isinstance(parsed, list) else []
        except Exception:
            return []

    ai = AnalysisOut(
        problem=_loads(report.ai_problem),
        causes=_loads(report.ai_causes),
        precautions=_loads(report.ai_precautions),
        prevention=_loads(report.ai_prevention),
        severity=report.severity,  # type: ignore[arg-type]
    )
    return ReportOut(
        id=report.id,
        user_id=report.user_id,
        latitude=report.latitude,
        longitude=report.longitude,
        location_accuracy=report.location_accuracy,
        image_url=f"/static/{report.image_path}",
        description=report.description or "",
        ai=ai,
        severity=report.severity,  # type: ignore[arg-type]
        cluster_id=report.cluster_id,
        qr_url=f"/static/{report.qr_path}" if report.qr_path else "",
        created_at=report.created_at,
    )


@router.post("", response_model=ReportOut)
def create_report(
    payload: ReportCreateIn,
    user: Annotated[User, Depends(require_role("user", "supervisor"))],
    db: Session = Depends(get_db),
):
    if payload.accuracy > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location accuracy too low (>100m)")

    image_bytes = _decode_data_url(payload.image_base64)
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 2MB)")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    file_path = IMAGES_DIR / filename
    file_path.write_bytes(image_bytes)

    cluster_id = compute_cluster_id(payload.latitude, payload.longitude)
    analysis = analyze_image(image_bytes=image_bytes, description=payload.description)

    report = Report(
        user_id=user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_accuracy=payload.accuracy,
        image_path=f"images/{filename}",
        description=payload.description,
        ai_problem=json.dumps(analysis["problem"], ensure_ascii=False),
        ai_causes=json.dumps(analysis["causes"], ensure_ascii=False),
        ai_precautions=json.dumps(analysis["precautions"], ensure_ascii=False),
        ai_prevention=json.dumps(analysis["prevention"], ensure_ascii=False),
        severity=analysis["severity"],
        cluster_id=cluster_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    qr_rel_path = generate_qr_for_report(report_id=report.id, latitude=report.latitude, longitude=report.longitude)
    report.qr_path = qr_rel_path
    db.add(report)
    db.commit()
    db.refresh(report)

    return _to_report_out(report)


@router.get("/me", response_model=list[ReportOut])
def my_reports(
    user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    rows = db.execute(select(Report).where(Report.user_id == user.id).order_by(desc(Report.created_at))).scalars().all()
    return [_to_report_out(r) for r in rows]


@router.get("", response_model=list[ReportOut])
def all_reports(
    _supervisor: Annotated[User, Depends(require_role("supervisor"))],
    db: Session = Depends(get_db),
):
    rows = db.execute(select(Report).order_by(desc(Report.created_at))).scalars().all()
    return [_to_report_out(r) for r in rows]
