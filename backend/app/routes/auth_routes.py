from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from backend.app.auth import create_access_token, hash_password, verify_password
from backend.app.database import get_db, get_next_id
from backend.app.schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: RegisterIn, db: Database = Depends(get_db)):
    email = str(payload.email).lower()
    existing = db["users"].find_one({"email": email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if payload.role in {"supervisor", "worker"} and not payload.district.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="District is required for this role")

    user_doc = {
        "id": get_next_id(db, "users"),
        "name": payload.name,
        "email": email,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
        "phone": payload.phone.strip() or None,
        "district": payload.district.strip() or None,
        "state": payload.state.strip() or None,
        "city": payload.city.strip() or None,
        "is_available": True,
        "current_latitude": None,
        "current_longitude": None,
        "current_accuracy": None,
        "location_updated_at": None,
        "created_at": dt.datetime.utcnow(),
    }

    db["users"].insert_one(user_doc)
    return user_doc


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Database = Depends(get_db)):
    email = str(payload.email).lower()
    user = db["users"].find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(int(user["id"])), role=str(user.get("role", "user")))
    return TokenOut(access_token=token, role=user.get("role", "user"), name=user.get("name", ""))
