from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
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
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, nullable=False)

    reports: Mapped[list["Report"]] = relationship(back_populates="user")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location_accuracy: Mapped[float] = mapped_column(Float, nullable=False)

    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    ai_problem: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    ai_causes: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    ai_precautions: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    ai_prevention: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="Low")

    cluster_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    qr_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="reports")
