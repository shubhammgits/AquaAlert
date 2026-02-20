from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.database import engine
from backend.app.models import Base
from backend.app.routes.auth_routes import router as auth_router
from backend.app.routes.cluster_routes import router as cluster_router
from backend.app.routes.report_routes import router as report_router

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_STATIC_DIR = Path(__file__).resolve().parent / "static"


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

    app.mount("/static", StaticFiles(directory=str(BACKEND_STATIC_DIR)), name="static")
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/login.html")
    def login_page() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "login.html"))

    @app.get("/register.html")
    def register_page() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "register.html"))

    @app.get("/user_dashboard.html")
    def user_dashboard_page() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "user_dashboard.html"))

    @app.get("/supervisor_dashboard.html")
    def supervisor_dashboard_page() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "supervisor_dashboard.html"))

    @app.get("/manifest.json")
    def manifest() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "manifest.json"), media_type="application/json")

    @app.get("/service-worker.js")
    def sw() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "service-worker.js"), media_type="application/javascript")

    return app


app = create_app()
