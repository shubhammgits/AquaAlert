from __future__ import annotations

import datetime as dt
import os
from typing import Annotated, Callable, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User

_bearer = HTTPBearer(auto_error=False)


def _get_secret() -> str:
    return os.getenv("JWT_SECRET", "change-me")


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(*, subject: str, role: str, expires_minutes: int = 60 * 24) -> str:
    now = dt.datetime.utcnow()
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise _unauthorized()

    token = credentials.credentials
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
        user_id = payload.get("sub")
    except JWTError:
        raise _unauthorized("Invalid token")

    if not user_id:
        raise _unauthorized("Invalid token")

    user = db.get(User, int(user_id))
    if not user:
        raise _unauthorized("User not found")
    return user


def require_role(*allowed_roles: str) -> Callable:
    def _dep(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep
