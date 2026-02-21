from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pymongo.database import Database

from backend.app.auth import get_current_user
from backend.app.database import get_db
from backend.app.schemas import ClusterOut
from backend.app.services.cluster_service import get_clusters

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=list[ClusterOut])
def clusters(
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Database, Depends(get_db)],
):
    if user.get("role") == "supervisor":
        if not user.get("district"):
            return []
        return get_clusters(db, district=user.get("district"))
    return get_clusters(db)
