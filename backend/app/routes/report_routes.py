from __future__ import annotations

import base64
import datetime as dt
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import DESCENDING
from pymongo.database import Database

from backend.app.auth import get_current_user, require_role
from backend.app.database import get_db, get_next_id
from backend.app.schemas import (
    ReportAssignIn,
    ReportCompleteIn,
    ReportCreateIn,
    ReportOut,
    ReportVerifyIn,
)
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


def _to_report_out(report: dict, assigned_worker: dict | None = None) -> ReportOut:
    worker_out = None
    if assigned_worker is not None:
        worker_out = {
            "id": assigned_worker.get("id"),
            "name": assigned_worker.get("name"),
            "phone": assigned_worker.get("phone"),
            "district": assigned_worker.get("district"),
        }

    return ReportOut(
        id=int(report.get("id", 0)),
        user_id=int(report.get("user_id", 0)),
        latitude=float(report.get("latitude", 0.0)),
        longitude=float(report.get("longitude", 0.0)),
        location_accuracy=float(report.get("location_accuracy", 0.0)),
        image_url=f"/static/{report.get('image_path','')}",
        description=str(report.get("description") or ""),
        contact_phone=str(report.get("contact_phone") or ""),
        district=str(report.get("district") or ""),
        state=str(report.get("state") or ""),
        city=str(report.get("city") or ""),
        severity=report.get("severity", "Low"),
        status=report.get("status", "submitted"),
        cluster_id=str(report.get("cluster_id") or ""),
        qr_url=f"/static/{report.get('qr_path','')}" if report.get("qr_path") else "",
        assigned_worker=worker_out,
        expected_completion_at=report.get("expected_completion_at"),
        completion_image_url=f"/static/{report.get('completion_image_path','')}" if report.get("completion_image_path") else "",
        completed_at=report.get("completed_at"),
        completion_verified_at=report.get("completion_verified_at"),
        resolution_message=str(report.get("resolution_message") or ""),
        created_at=report.get("created_at") or dt.datetime.utcnow(),
    )


@router.post("", response_model=ReportOut)
def create_report(
    payload: ReportCreateIn,
    user: Annotated[dict, Depends(require_role("user", "supervisor"))],
    db: Database = Depends(get_db),
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

    report_id = get_next_id(db, "reports")
    created_at = dt.datetime.utcnow()

    report = {
        "id": report_id,
        "user_id": int(user["id"]),
        "latitude": float(payload.latitude),
        "longitude": float(payload.longitude),
        "location_accuracy": float(payload.accuracy),
        "image_path": f"images/{filename}",
        "description": payload.description,
        "contact_phone": payload.contact_phone.strip(),
        "district": payload.district.strip(),
        "state": (payload.state or "").strip(),
        "city": (payload.city or "").strip(),
        "severity": "Low",
        "status": "submitted",
        "accepted_at": None,
        "accepted_by": None,
        "assigned_worker_id": None,
        "assigned_at": None,
        "expected_completion_at": None,
        "completion_image_path": "",
        "completion_latitude": None,
        "completion_longitude": None,
        "completion_accuracy": None,
        "completed_at": None,
        "completion_verified_at": None,
        "completion_verified_by": None,
        "resolution_message": "",
        "cluster_id": cluster_id,
        "qr_path": "",
        "created_at": created_at,
    }
    db["reports"].insert_one(report)

    qr_rel_path = generate_qr_for_report(report_id=report_id, latitude=report["latitude"], longitude=report["longitude"])
    report["qr_path"] = qr_rel_path
    db["reports"].update_one({"id": report_id}, {"$set": {"qr_path": qr_rel_path}})

    # Annotate the saved image with an auto geotag footer for supervisor review.
    # Best-effort: if reverse geocoding is unavailable, still keep the report.
    try:
        annotate_report_image(
            image_file=file_path,
            qr_file=STATIC_DIR / qr_rel_path,
            latitude=report["latitude"],
            longitude=report["longitude"],
            accuracy_m=report["location_accuracy"],
            created_at=created_at,
            reported_timestamp=payload.timestamp,
        )
    except Exception:
        pass

    return _to_report_out(report)


@router.patch("/{report_id}/accept", response_model=ReportOut)
def accept_report(
    report_id: int,
    supervisor: Annotated[dict, Depends(require_role("supervisor"))],
    db: Database = Depends(get_db),
):
    report = db["reports"].find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not supervisor.get("district"):
        raise HTTPException(status_code=400, detail="Supervisor district not set")
    if (report.get("district") or "") != (supervisor.get("district") or ""):
        raise HTTPException(status_code=403, detail="Forbidden")
    if report.get("status") not in {"submitted"}:
        raise HTTPException(status_code=400, detail=f"Cannot accept report in status {report.get('status')}")

    now = dt.datetime.utcnow()
    db["reports"].update_one(
        {"id": report_id},
        {"$set": {"status": "accepted", "accepted_at": now, "accepted_by": int(supervisor["id"])}} ,
    )
    report.update({"status": "accepted", "accepted_at": now, "accepted_by": int(supervisor["id"])})
    return _to_report_out(report)


@router.patch("/{report_id}/assign", response_model=ReportOut)
def assign_report(
    report_id: int,
    payload: ReportAssignIn,
    supervisor: Annotated[dict, Depends(require_role("supervisor"))],
    db: Database = Depends(get_db),
):
    report = db["reports"].find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not supervisor.get("district"):
        raise HTTPException(status_code=400, detail="Supervisor district not set")
    if (report.get("district") or "") != (supervisor.get("district") or ""):
        raise HTTPException(status_code=403, detail="Forbidden")
    if report.get("status") not in {"accepted", "assigned"}:
        raise HTTPException(status_code=400, detail=f"Cannot assign report in status {report.get('status')}")

    worker = db["users"].find_one({"id": int(payload.worker_id)})
    if not worker or worker.get("role") != "worker":
        raise HTTPException(status_code=400, detail="Invalid worker")

    # Atomically reserve the worker if available.
    reserved = db["users"].update_one(
        {"id": int(payload.worker_id), "role": "worker", "is_available": True},
        {"$set": {"is_available": False}},
    )
    if reserved.matched_count == 0:
        raise HTTPException(status_code=400, detail="Worker is not available")

    now = dt.datetime.utcnow()
    expected = payload.expected_completion_at
    if expected is None and payload.eta_hours:
        expected = now + dt.timedelta(hours=int(payload.eta_hours))

    upd = db["reports"].update_one(
        {"id": report_id},
        {
            "$set": {
                "assigned_worker_id": int(payload.worker_id),
                "assigned_at": now,
                "status": "assigned",
                "expected_completion_at": expected,
            }
        },
    )
    if upd.matched_count == 0:
        # Best-effort rollback
        db["users"].update_one({"id": int(payload.worker_id)}, {"$set": {"is_available": True}})
        raise HTTPException(status_code=404, detail="Report not found")

    report.update(
        {
            "assigned_worker_id": int(payload.worker_id),
            "assigned_at": now,
            "status": "assigned",
            "expected_completion_at": expected,
        }
    )
    worker = db["users"].find_one({"id": int(payload.worker_id)})
    return _to_report_out(report, assigned_worker=worker)


@router.get("/assigned", response_model=list[ReportOut])
def worker_assigned_reports(
    worker: Annotated[dict, Depends(require_role("worker"))],
    db: Database = Depends(get_db),
):
    cursor = (
        db["reports"]
        .find({"assigned_worker_id": int(worker["id"]), "status": {"$in": ["assigned", "completed"]}})
        .sort("assigned_at", DESCENDING)
    )
    rows = list(cursor)
    return [_to_report_out(r, assigned_worker=worker) for r in rows]


@router.get("/history", response_model=list[ReportOut])
def worker_history(
    worker: Annotated[dict, Depends(require_role("worker"))],
    db: Database = Depends(get_db),
):
    cursor = db["reports"].find({"assigned_worker_id": int(worker["id"]), "status": "closed"}).sort(
        [
            ("completion_verified_at", DESCENDING),
            ("completed_at", DESCENDING),
            ("assigned_at", DESCENDING),
        ]
    )
    rows = list(cursor)
    return [_to_report_out(r, assigned_worker=worker) for r in rows]


@router.post("/{report_id}/complete", response_model=ReportOut)
def complete_report(
    report_id: int,
    payload: ReportCompleteIn,
    worker: Annotated[dict, Depends(require_role("worker"))],
    db: Database = Depends(get_db),
):
    if payload.accuracy > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location accuracy too low (>100m)")

    report = db["reports"].find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.get("assigned_worker_id") != int(worker["id"]):
        raise HTTPException(status_code=403, detail="Not assigned to this report")
    if report.get("status") != "assigned":
        raise HTTPException(status_code=400, detail=f"Cannot complete report in status {report.get('status')}")

    image_bytes = _decode_data_url(payload.image_base64)
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 2MB)")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"completion_{uuid.uuid4().hex}.jpg"
    (IMAGES_DIR / filename).write_bytes(image_bytes)

    now = dt.datetime.utcnow()
    updates = {
        "completion_image_path": f"images/{filename}",
        "completion_latitude": float(payload.latitude),
        "completion_longitude": float(payload.longitude),
        "completion_accuracy": float(payload.accuracy),
        "completed_at": now,
        "status": "completed",
    }

    db["reports"].update_one({"id": report_id}, {"$set": updates})
    report.update(updates)
    return _to_report_out(report, assigned_worker=worker)


@router.patch("/{report_id}/verify", response_model=ReportOut)
def verify_completion(
    report_id: int,
    payload: ReportVerifyIn,
    supervisor: Annotated[dict, Depends(require_role("supervisor"))],
    db: Database = Depends(get_db),
):
    report = db["reports"].find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not supervisor.get("district"):
        raise HTTPException(status_code=400, detail="Supervisor district not set")
    if (report.get("district") or "") != (supervisor.get("district") or ""):
        raise HTTPException(status_code=403, detail="Forbidden")
    if report.get("status") != "completed":
        raise HTTPException(status_code=400, detail=f"Cannot verify report in status {report.get('status')}")

    if payload.approved:
        now = dt.datetime.utcnow()
        updates = {
            "status": "closed",
            "completion_verified_at": now,
            "completion_verified_by": int(supervisor["id"]),
            "resolution_message": payload.message.strip()
            or "Work completed and verified. Thank you for coordinating.",
        }

        if report.get("assigned_worker_id"):
            db["users"].update_one(
                {"id": int(report["assigned_worker_id"]), "role": "worker"},
                {"$set": {"is_available": True}},
            )
    else:
        updates = {
            "status": "assigned",
            "resolution_message": payload.message.strip() or "Completion rejected. Please re-check and resubmit.",
        }

    db["reports"].update_one({"id": report_id}, {"$set": updates})
    report.update(updates)
    assigned_worker = None
    if report.get("assigned_worker_id"):
        assigned_worker = db["users"].find_one({"id": int(report["assigned_worker_id"])})
    return _to_report_out(report, assigned_worker=assigned_worker)


@router.get("/me", response_model=list[ReportOut])
def my_reports(
    user: Annotated[dict, Depends(get_current_user)],
    db: Database = Depends(get_db),
):
    cursor = db["reports"].find({"user_id": int(user["id"])}).sort("created_at", DESCENDING)
    rows = list(cursor)
    return [_to_report_out(r) for r in rows]


@router.get("", response_model=list[ReportOut])
def all_reports(
    supervisor: Annotated[dict, Depends(require_role("supervisor"))],
    db: Database = Depends(get_db),
):
    if not supervisor.get("district"):
        raise HTTPException(status_code=400, detail="Supervisor district not set")

    cursor = db["reports"].find({"district": supervisor.get("district")}).sort("created_at", DESCENDING)
    rows = list(cursor)
    # Attach worker details when assigned
    out: list[ReportOut] = []
    for r in rows:
        assigned_worker = None
        if r.get("assigned_worker_id"):
            assigned_worker = db["users"].find_one({"id": int(r["assigned_worker_id"])})
        out.append(_to_report_out(r, assigned_worker=assigned_worker))
    return out
