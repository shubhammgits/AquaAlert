from __future__ import annotations

import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


Role = Literal["user", "supervisor"]
Severity = Literal["Low", "Medium", "High"]


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: Role = "user"


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
    description: str = Field(default="", max_length=2000)
    image_base64: str = Field(min_length=50)


class ReportOut(BaseModel):
    id: int
    user_id: int
    latitude: float
    longitude: float
    location_accuracy: float
    image_url: str
    description: str
    ai: AnalysisOut
    severity: Severity
    cluster_id: str
    qr_url: str
    created_at: dt.datetime


class ClusterOut(BaseModel):
    cluster_id: str
    latitude: float
    longitude: float
    report_count: int
    severity: Severity
    priority: int
