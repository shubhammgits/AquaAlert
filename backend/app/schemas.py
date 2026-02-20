from __future__ import annotations

import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


Role = Literal["user", "supervisor", "worker"]
Severity = Literal["Low", "Medium", "High"]
ReportStatus = Literal[
    "submitted",
    "accepted",
    "assigned",
    "completed",
    "closed",
    "rejected",
]


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: Role = "user"
    phone: str = Field(default="", max_length=30)
    district: str = Field(default="", max_length=120)
    state: str = Field(default="", max_length=120)
    city: str = Field(default="", max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    name: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Role
    phone: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    is_available: bool
    created_at: dt.datetime

    class Config:
        from_attributes = True


class AnalysisOut(BaseModel):
    problem: list[str] = []
    causes: list[str] = []
    precautions: list[str] = []
    prevention: list[str] = []
    severity: Severity = "Low"


class ReportCreateIn(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: float = Field(gt=0)
    timestamp: Optional[int] = None
    district: str = Field(min_length=2, max_length=120)
    state: str = Field(default="", max_length=120)
    city: str = Field(default="", max_length=120)
    contact_phone: str = Field(min_length=6, max_length=30)
    description: str = Field(default="", max_length=2000)
    image_base64: str = Field(min_length=50)


class ReportAssignIn(BaseModel):
    worker_id: int
    expected_completion_at: Optional[dt.datetime] = None
    eta_hours: Optional[int] = Field(default=None, ge=1, le=168)


class ReportVerifyIn(BaseModel):
    approved: bool
    message: str = Field(default="", max_length=2000)


class ReportCompleteIn(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: float = Field(gt=0)
    timestamp: Optional[int] = None
    image_base64: str = Field(min_length=50)


class ReportOut(BaseModel):
    id: int
    user_id: int
    latitude: float
    longitude: float
    location_accuracy: float
    image_url: str
    description: str
    contact_phone: str
    district: str
    state: str = ""
    city: str = ""
    ai: AnalysisOut
    severity: Severity
    status: ReportStatus
    cluster_id: str
    qr_url: str
    assigned_worker: Optional[dict] = None
    expected_completion_at: Optional[dt.datetime] = None
    completion_image_url: str = ""
    completed_at: Optional[dt.datetime] = None
    completion_verified_at: Optional[dt.datetime] = None
    resolution_message: str = ""
    created_at: dt.datetime


class WorkerOut(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    district: Optional[str] = None
    is_available: bool
    distance_m: Optional[int] = None
    location_updated_at: Optional[dt.datetime] = None


class WorkerLocationIn(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: float = Field(gt=0)
    timestamp: Optional[int] = None


class ValidationCandidateOut(BaseModel):
    report_id: int
    latitude: float
    longitude: float
    district: str
    description: str
    severity: Severity
    created_at: dt.datetime


class ValidationVoteIn(BaseModel):
    vote: bool


class ClusterOut(BaseModel):
    cluster_id: str
    latitude: float
    longitude: float
    report_count: int
    severity: Severity
    priority: int
