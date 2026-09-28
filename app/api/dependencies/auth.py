import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.api.dependencies.database import DbSession
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    description="Paste the `access_token` returned by `/v1/auth/login`.",
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except jwt.InvalidTokenError, ValueError, TypeError:
        raise credentials_exception

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise credentials_exception

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
