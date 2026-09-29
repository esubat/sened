import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi.concurrency import run_in_threadpool
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()

DUMMY_HASHED_PASSWORD = password_hash.hash("dummy_password")


async def hash_password(password: str) -> str:
    return await run_in_threadpool(password_hash.hash, password)


async def verify_password(password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(password_hash.verify, password, hashed_password)


def create_access_token(data: dict, expires_delta: int | None = None) -> str:
    if expires_delta is None:
        expires_delta = settings.access_token_expire_seconds

    to_encode = data.copy()
    now = datetime.now(UTC)
    to_encode.update({"iat": now, "exp": now + timedelta(seconds=expires_delta)})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub"]},
    )


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
