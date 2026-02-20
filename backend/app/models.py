from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    current_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, nullable=False)

    reports: Mapped[list["Report"]] = relationship(
        back_populates="user",
        foreign_keys="Report.user_id",
    )
    accepted_reports: Mapped[list["Report"]] = relationship(
        foreign_keys="Report.accepted_by",
    )
    assigned_reports: Mapped[list["Report"]] = relationship(
        foreign_keys="Report.assigned_worker_id",
    )
    verified_reports: Mapped[list["Report"]] = relationship(
        foreign_keys="Report.completion_verified_by",
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location_accuracy: Mapped[float] = mapped_column(Float, nullable=False)

    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    district: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(120), nullable=False, default="")

    ai_problem: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    ai_causes: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    ai_precautions: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    ai_prevention: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="Low")

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="submitted", index=True)
    accepted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    accepted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    assigned_worker_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    assigned_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    expected_completion_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    completion_image_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    completion_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    completion_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    completion_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    completion_verified_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    completion_verified_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolution_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    cluster_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    qr_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="reports", foreign_keys=[user_id])
    acceptor: Mapped[User | None] = relationship(foreign_keys=[accepted_by])
    worker: Mapped[User | None] = relationship(foreign_keys=[assigned_worker_id])
    verifier: Mapped[User | None] = relationship(foreign_keys=[completion_verified_by])


class Validation(Base):
    __tablename__ = "validations"
    __table_args__ = (UniqueConstraint("report_id", "user_id", name="uq_validation_report_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vote: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=yes, 0=no
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, nullable=False)
