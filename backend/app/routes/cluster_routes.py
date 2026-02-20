from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.database import get_db
from backend.app.models import User
from backend.app.schemas import ClusterOut
from backend.app.services.cluster_service import get_clusters

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=list[ClusterOut])
def clusters(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    if user.role == "supervisor":
        if not user.district:
            return []
        return get_clusters(db, district=user.district)
    return get_clusters(db)
