from __future__ import annotations

import base64
import datetime as dt
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
from backend.app.schemas import (
    AnalysisOut,
    ReportAssignIn,
    ReportCompleteIn,
    ReportCreateIn,
    ReportOut,
    ReportVerifyIn,
)
from backend.app.services.ai_service import analyze_image
from backend.app.services.cluster_service import compute_cluster_id
from backend.app.services.geotag_service import annotate_report_image
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

    assigned_worker = None
    if report.worker is not None:
        assigned_worker = {
            "id": report.worker.id,
            "name": report.worker.name,
            "phone": report.worker.phone,
            "district": report.worker.district,
        }

    return ReportOut(
        id=report.id,
        user_id=report.user_id,
        latitude=report.latitude,
        longitude=report.longitude,
        location_accuracy=report.location_accuracy,
        image_url=f"/static/{report.image_path}",
        description=report.description or "",
        contact_phone=report.contact_phone or "",
        district=report.district or "",
        state=getattr(report, "state", "") or "",
        city=getattr(report, "city", "") or "",
        ai=ai,
        severity=report.severity,  # type: ignore[arg-type]
        status=report.status,  # type: ignore[arg-type]
        cluster_id=report.cluster_id,
        qr_url=f"/static/{report.qr_path}" if report.qr_path else "",
        assigned_worker=assigned_worker,
        expected_completion_at=report.expected_completion_at,
        completion_image_url=f"/static/{report.completion_image_path}" if report.completion_image_path else "",
        completed_at=report.completed_at,
        completion_verified_at=report.completion_verified_at,
        resolution_message=report.resolution_message or "",
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
        contact_phone=payload.contact_phone.strip(),
        district=payload.district.strip(),
        state=(payload.state or "").strip(),
        city=(payload.city or "").strip(),
        ai_problem=json.dumps(analysis["problem"], ensure_ascii=False),
        ai_causes=json.dumps(analysis["causes"], ensure_ascii=False),
        ai_precautions=json.dumps(analysis["precautions"], ensure_ascii=False),
        ai_prevention=json.dumps(analysis["prevention"], ensure_ascii=False),
        severity=analysis["severity"],
        cluster_id=cluster_id,
        status="submitted",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    qr_rel_path = generate_qr_for_report(report_id=report.id, latitude=report.latitude, longitude=report.longitude)
    report.qr_path = qr_rel_path
    db.add(report)
    db.commit()
    db.refresh(report)

    # Annotate the saved image with an auto geotag footer for supervisor review.
    # Best-effort: if reverse geocoding is unavailable, still keep the report.
    try:
        annotate_report_image(
            image_file=file_path,
            qr_file=STATIC_DIR / qr_rel_path,
            latitude=report.latitude,
            longitude=report.longitude,
            accuracy_m=report.location_accuracy,
            created_at=report.created_at,
            reported_timestamp=payload.timestamp,
        )
    except Exception:
        pass

    return _to_report_out(report)


@router.patch("/{report_id}/accept", response_model=ReportOut)
def accept_report(
    report_id: int,
    supervisor: Annotated[User, Depends(require_role("supervisor"))],
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not supervisor.district:
        raise HTTPException(status_code=400, detail="Supervisor district not set")
    if (report.district or "") != (supervisor.district or ""):
        raise HTTPException(status_code=403, detail="Forbidden")
    if report.status not in {"submitted"}:
        raise HTTPException(status_code=400, detail=f"Cannot accept report in status {report.status}")

    report.status = "accepted"
    report.accepted_at = dt.datetime.utcnow()
    report.accepted_by = supervisor.id
    db.add(report)
    db.commit()
    db.refresh(report)
    return _to_report_out(report)


@router.patch("/{report_id}/assign", response_model=ReportOut)
def assign_report(
    report_id: int,
    payload: ReportAssignIn,
    supervisor: Annotated[User, Depends(require_role("supervisor"))],
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not supervisor.district:
        raise HTTPException(status_code=400, detail="Supervisor district not set")
    if (report.district or "") != (supervisor.district or ""):
        raise HTTPException(status_code=403, detail="Forbidden")
    if report.status not in {"accepted", "assigned"}:
        raise HTTPException(status_code=400, detail=f"Cannot assign report in status {report.status}")

    worker = db.get(User, payload.worker_id)
    if not worker or worker.role != "worker":
        raise HTTPException(status_code=400, detail="Invalid worker")
    if not worker.is_available:
        raise HTTPException(status_code=400, detail="Worker is not available")

    report.assigned_worker_id = worker.id
    report.assigned_at = dt.datetime.utcnow()
    report.status = "assigned"

    expected = payload.expected_completion_at
    if expected is None and payload.eta_hours:
        expected = dt.datetime.utcnow() + dt.timedelta(hours=int(payload.eta_hours))
    report.expected_completion_at = expected

    worker.is_available = False
    db.add(worker)
    db.add(report)
    db.commit()
    db.refresh(report)
    return _to_report_out(report)


@router.get("/assigned", response_model=list[ReportOut])
def worker_assigned_reports(
    worker: Annotated[User, Depends(require_role("worker"))],
    db: Session = Depends(get_db),
):
    rows = (
        db.execute(
            select(Report)
            .where(Report.assigned_worker_id == worker.id)
            .where(Report.status.in_(["assigned", "completed"]))
            .order_by(desc(Report.assigned_at))
        )
        .scalars()
        .all()
    )
    return [_to_report_out(r) for r in rows]


@router.get("/history", response_model=list[ReportOut])
def worker_history(
    worker: Annotated[User, Depends(require_role("worker"))],
    db: Session = Depends(get_db),
):
    rows = (
        db.execute(
            select(Report)
            .where(Report.assigned_worker_id == worker.id)
            .where(Report.status == "closed")
            .order_by(
                desc(Report.completion_verified_at),
                desc(Report.completed_at),
                desc(Report.assigned_at),
            )
        )
        .scalars()
        .all()
    )
    return [_to_report_out(r) for r in rows]


@router.post("/{report_id}/complete", response_model=ReportOut)
def complete_report(
    report_id: int,
    payload: ReportCompleteIn,
    worker: Annotated[User, Depends(require_role("worker"))],
    db: Session = Depends(get_db),
):
    if payload.accuracy > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location accuracy too low (>100m)")

    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.assigned_worker_id != worker.id:
        raise HTTPException(status_code=403, detail="Not assigned to this report")
    if report.status != "assigned":
        raise HTTPException(status_code=400, detail=f"Cannot complete report in status {report.status}")

    image_bytes = _decode_data_url(payload.image_base64)
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 2MB)")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"completion_{uuid.uuid4().hex}.jpg"
    (IMAGES_DIR / filename).write_bytes(image_bytes)

    report.completion_image_path = f"images/{filename}"
    report.completion_latitude = payload.latitude
    report.completion_longitude = payload.longitude
    report.completion_accuracy = payload.accuracy
    report.completed_at = dt.datetime.utcnow()
    report.status = "completed"

    db.add(report)
    db.commit()
    db.refresh(report)
    return _to_report_out(report)


@router.patch("/{report_id}/verify", response_model=ReportOut)
def verify_completion(
    report_id: int,
    payload: ReportVerifyIn,
    supervisor: Annotated[User, Depends(require_role("supervisor"))],
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not supervisor.district:
        raise HTTPException(status_code=400, detail="Supervisor district not set")
    if (report.district or "") != (supervisor.district or ""):
        raise HTTPException(status_code=403, detail="Forbidden")
    if report.status != "completed":
        raise HTTPException(status_code=400, detail=f"Cannot verify report in status {report.status}")

    if payload.approved:
        report.status = "closed"
        report.completion_verified_at = dt.datetime.utcnow()
        report.completion_verified_by = supervisor.id
        report.resolution_message = payload.message.strip() or "Work completed and verified. Thank you for coordinating."

        if report.assigned_worker_id:
            worker = db.get(User, report.assigned_worker_id)
            if worker:
                worker.is_available = True
                db.add(worker)
    else:
        report.status = "assigned"
        report.resolution_message = payload.message.strip() or "Completion rejected. Please re-check and resubmit." 

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
    supervisor: Annotated[User, Depends(require_role("supervisor"))],
    db: Session = Depends(get_db),
):
    if not supervisor.district:
        raise HTTPException(status_code=400, detail="Supervisor district not set")

    rows = (
        db.execute(
            select(Report).where(Report.district == supervisor.district).order_by(desc(Report.created_at))
        )
        .scalars()
        .all()
    )
    return [_to_report_out(r) for r in rows]
