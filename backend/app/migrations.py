from __future__ import annotations

from sqlalchemy import Engine, text


def ensure_sqlite_schema(engine: Engine) -> None:
    """Best-effort dev migration for SQLite.

    This keeps the project runnable after schema changes without introducing Alembic.
    """

    def _has_column(table: str, column: str) -> bool:
        with engine.connect() as conn:
            rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        return any(r[1] == column for r in rows)

    def _add_column(table: str, ddl: str) -> None:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))

    # users
    if _table_exists(engine, "users"):
        if not _has_column("users", "phone"):
            _add_column("users", "phone VARCHAR(30)")
        if not _has_column("users", "district"):
            _add_column("users", "district VARCHAR(120)")
        if not _has_column("users", "state"):
            _add_column("users", "state VARCHAR(120)")
        if not _has_column("users", "city"):
            _add_column("users", "city VARCHAR(120)")
        if not _has_column("users", "is_available"):
            _add_column("users", "is_available BOOLEAN NOT NULL DEFAULT 1")
        if not _has_column("users", "current_latitude"):
            _add_column("users", "current_latitude FLOAT")
        if not _has_column("users", "current_longitude"):
            _add_column("users", "current_longitude FLOAT")
        if not _has_column("users", "current_accuracy"):
            _add_column("users", "current_accuracy FLOAT")
        if not _has_column("users", "location_updated_at"):
            _add_column("users", "location_updated_at DATETIME")

    # reports
    if _table_exists(engine, "reports"):
        additions = [
            ("contact_phone", "contact_phone VARCHAR(30) NOT NULL DEFAULT ''"),
            ("district", "district VARCHAR(120) NOT NULL DEFAULT ''"),
            ("state", "state VARCHAR(120) NOT NULL DEFAULT ''"),
            ("city", "city VARCHAR(120) NOT NULL DEFAULT ''"),
            ("status", "status VARCHAR(30) NOT NULL DEFAULT 'submitted'"),
            ("accepted_at", "accepted_at DATETIME"),
            ("accepted_by", "accepted_by INTEGER"),
            ("assigned_worker_id", "assigned_worker_id INTEGER"),
            ("assigned_at", "assigned_at DATETIME"),
            ("expected_completion_at", "expected_completion_at DATETIME"),
            ("completion_image_path", "completion_image_path VARCHAR(500) NOT NULL DEFAULT ''"),
            ("completion_latitude", "completion_latitude FLOAT"),
            ("completion_longitude", "completion_longitude FLOAT"),
            ("completion_accuracy", "completion_accuracy FLOAT"),
            ("completed_at", "completed_at DATETIME"),
            ("completion_verified_at", "completion_verified_at DATETIME"),
            ("completion_verified_by", "completion_verified_by INTEGER"),
            ("resolution_message", "resolution_message TEXT NOT NULL DEFAULT ''"),
        ]
        for col, ddl in additions:
            if not _has_column("reports", col):
                _add_column("reports", ddl)

    # validations table
    if not _table_exists(engine, "validations"):
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE validations (
                        id INTEGER PRIMARY KEY,
                        report_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        vote INTEGER NOT NULL,
                        created_at DATETIME NOT NULL,
                        CONSTRAINT uq_validation_report_user UNIQUE (report_id, user_id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX ix_validations_report_id ON validations (report_id)"))
            conn.execute(text("CREATE INDEX ix_validations_user_id ON validations (user_id)"))


def _table_exists(engine: Engine, table: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": table},
        ).fetchone()
    return row is not None
