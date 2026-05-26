from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api import health, plaid, sheets
from app.core.config import settings
from app.db.session import init_db

WEB_DIR = Path(__file__).resolve().parent / "web"


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    @app.on_event("startup")
    def startup() -> None:
        init_db()

    app.include_router(health.router)
    app.include_router(plaid.router, prefix="/api/plaid", tags=["plaid"])
    app.include_router(sheets.router, prefix="/api/sheets", tags=["sheets"])

    @app.get("/", include_in_schema=False)
    def web_app() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    return app


app = create_app()
