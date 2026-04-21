from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from pymongo.errors import PyMongoError

from backend.app.auth import create_access_token, hash_password, verify_password
from backend.app.database import get_db, get_next_id
from backend.app.schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_district(value: str) -> str:
    return " ".join(str(value or "").strip().split())


@router.post("/register", response_model=UserOut)
def register(payload: RegisterIn, db: Database = Depends(get_db)):
    try:
        email = str(payload.email).strip().lower()
        role = "user" if payload.role == "public" else payload.role
        existing = db["users"].find_one({"email": email})
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        if role in {"supervisor", "worker"} and not payload.district.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="District is required for this role")

        user_doc = {
            "id": get_next_id(db, "users"),
            "name": str(payload.name).strip(),
            "email": email,
            "password_hash": hash_password(payload.password),
            "role": role,
            "phone": str(payload.phone).strip() or None,
            "district": _normalize_district(payload.district) or None,
            "state": str(payload.state).strip() or None,
            "city": str(payload.city).strip() or None,
            "is_available": True,
            "current_latitude": None,
            "current_longitude": None,
            "current_accuracy": None,
            "location_updated_at": None,
            "created_at": dt.datetime.utcnow(),
        }

        db["users"].insert_one(user_doc)
        return user_doc
    except HTTPException:
        raise
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database is unavailable right now: {exc.__class__.__name__}: {exc}",
        )


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Database = Depends(get_db)):
    try:
        email = str(payload.email).strip().lower()
        user = db["users"].find_one({"email": email})
        password_raw = str(payload.password)
        password_try = password_raw.strip()
        ok = bool(user) and (
            verify_password(password_raw, user.get("password_hash", ""))
            or (password_try != password_raw and verify_password(password_try, user.get("password_hash", "")))
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token(subject=str(int(user["id"])), role=str(user.get("role", "user")))
        return TokenOut(access_token=token, role=user.get("role", "user"), name=user.get("name", ""))
    except HTTPException:
        raise
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database is unavailable right now: {exc.__class__.__name__}: {exc}",
        )
