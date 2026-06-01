from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/config")
def public_config() -> dict[str, str]:
    return {
        "app_env": settings.app_env,
        "plaid_env": settings.plaid_env,
    }
