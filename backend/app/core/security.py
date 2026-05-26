from __future__ import annotations

from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_app_api_key(api_key: Optional[str] = Security(api_key_header)) -> None:
    if not settings.app_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APP_API_KEY is not configured.",
        )
    if api_key != settings.app_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


def _fernet() -> Fernet:
    if not settings.token_encryption_key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is not configured.")
    return Fernet(settings.token_encryption_key.encode("utf-8"))


def encrypt_token(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_token(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Stored Plaid token cannot be decrypted.") from exc
