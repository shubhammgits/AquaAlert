from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.database import ensure_indexes, get_mongo_database
from backend.app.routes.auth_routes import router as auth_router
from backend.app.routes.cluster_routes import router as cluster_router
from backend.app.routes.report_routes import router as report_router
from backend.app.routes.validation_routes import router as validation_router
from backend.app.routes.worker_routes import router as worker_router

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_STATIC_DIR = Path(__file__).resolve().parent / "static"
FRONTEND_DIST_DIR = ROOT_DIR / "frontend" / "dist"
LEGACY_DIR = BACKEND_STATIC_DIR / "legacy"
LANDING_DIR = BACKEND_STATIC_DIR / "landing"

# Load local environment variables (e.g. JWT_SECRET) from `.env` if present.
# This keeps secrets out of source code.
def _load_dotenv_fallback(env_path: Path) -> None:
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        return


try:  # pragma: no cover
    from dotenv import load_dotenv

    load_dotenv(ROOT_DIR / ".env")
except Exception:
    _load_dotenv_fallback(ROOT_DIR / ".env")


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
        ensure_indexes(get_mongo_database())

    @app.get("/health")
    def health() -> dict:
        return {
            "ok": True,
            "jwt_secret_configured": bool(os.getenv("JWT_SECRET")) and os.getenv("JWT_SECRET") != "change-me",
        }

    @app.get("/")
    def index() -> FileResponse:
        if (LANDING_DIR / "landing.html").exists():
            return FileResponse(str(LANDING_DIR / "landing.html"))
        if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
            return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))
        return FileResponse(str(LEGACY_DIR / "index.html"))

    @app.get("/index.html")
    def index_html() -> FileResponse:
        if (LANDING_DIR / "landing.html").exists():
            return FileResponse(str(LANDING_DIR / "landing.html"))
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
