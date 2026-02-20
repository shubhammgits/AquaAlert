from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.database import engine
from backend.app.models import Base
from backend.app.migrations import ensure_sqlite_schema
from backend.app.routes.auth_routes import router as auth_router
from backend.app.routes.cluster_routes import router as cluster_router
from backend.app.routes.report_routes import router as report_router
from backend.app.routes.validation_routes import router as validation_router
from backend.app.routes.worker_routes import router as worker_router

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_STATIC_DIR = Path(__file__).resolve().parent / "static"
FRONTEND_DIST_DIR = ROOT_DIR / "frontend" / "dist"
LEGACY_DIR = BACKEND_STATIC_DIR / "legacy"

# Load local environment variables (e.g. GEMINI_API_KEY, JWT_SECRET) from `.env` if present.
# This keeps secrets out of source code.
try:  # pragma: no cover
    from dotenv import load_dotenv

    load_dotenv(ROOT_DIR / ".env")
except Exception:
    pass


def create_app() -> FastAPI:
    app = FastAPI(title="AquaAlert", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(report_router)
    app.include_router(cluster_router)
    app.include_router(validation_router)
    app.include_router(worker_router)

    app.mount("/static", StaticFiles(directory=str(BACKEND_STATIC_DIR)), name="static")
    if (LEGACY_DIR / "css").exists():
        app.mount("/css", StaticFiles(directory=str(LEGACY_DIR / "css")), name="css")
    if (LEGACY_DIR / "js").exists():
        app.mount("/js", StaticFiles(directory=str(LEGACY_DIR / "js")), name="js")

    if FRONTEND_DIST_DIR.exists():
        assets_dir = FRONTEND_DIST_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="landing_assets")

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)
        ensure_sqlite_schema(engine)

    @app.get("/health")
    def health() -> dict:
        return {
            "ok": True,
            "ai_configured": bool(os.getenv("GEMINI_API_KEY")),
            "jwt_secret_configured": bool(os.getenv("JWT_SECRET")) and os.getenv("JWT_SECRET") != "change-me",
        }

    @app.get("/")
    def index() -> FileResponse:
        if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
            return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))
        return FileResponse(str(LEGACY_DIR / "index.html"))

    @app.get("/index.html")
    def index_html() -> FileResponse:
        if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
            return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))
        return FileResponse(str(LEGACY_DIR / "index.html"))

    @app.get("/login.html")
    def login_page() -> FileResponse:
        return FileResponse(str(LEGACY_DIR / "login.html"))

    @app.get("/register.html")
    def register_page() -> FileResponse:
        return FileResponse(str(LEGACY_DIR / "register.html"))

    @app.get("/user_dashboard.html")
    def user_dashboard_page() -> FileResponse:
        return FileResponse(str(LEGACY_DIR / "user_dashboard.html"))

    @app.get("/supervisor_dashboard.html")
    def supervisor_dashboard_page() -> FileResponse:
        return FileResponse(str(LEGACY_DIR / "supervisor_dashboard.html"))

    @app.get("/worker_dashboard.html")
    def worker_dashboard_page() -> FileResponse:
        return FileResponse(str(LEGACY_DIR / "worker_dashboard.html"))

    @app.get("/manifest.json")
    def manifest() -> FileResponse:
        return FileResponse(str(LEGACY_DIR / "manifest.json"), media_type="application/json")

    @app.get("/service-worker.js")
    def sw() -> FileResponse:
        return FileResponse(str(LEGACY_DIR / "service-worker.js"), media_type="application/javascript")

    return app


app = create_app()
