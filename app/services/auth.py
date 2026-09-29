import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    DUMMY_HASHED_PASSWORD,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
)


class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class IncorrectPasswordError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    stmt = select(User).where(User.email == data.email)
    existing_user = await db.scalar(stmt)
    if existing_user:
        raise EmailAlreadyExistsError("User with this email already exists")

    new_user = User(
        email=data.email,
        password_hash=await hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
    )
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise EmailAlreadyExistsError("User with this email already exists")
    await db.refresh(new_user)
    return new_user


async def login_user(db: AsyncSession, data: LoginRequest) -> tuple[LoginResponse, str]:
    stmt = select(User).where(User.email == data.email)
    user = await db.scalar(stmt)
    if not user:
        await verify_password(data.password, DUMMY_HASHED_PASSWORD)
        raise InvalidCredentialsError("Invalid email or password")

    if not await verify_password(data.password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password")

    if not user.is_active:
        raise InvalidCredentialsError("Invalid email or password")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token, _ = _issue_refresh_token(db, user.id)
    await db.commit()

    response = LoginResponse(
        message="Login successful",
        access_token=access_token,
        user=user,
    )
    return response, refresh_token


async def refresh_access_token(
    db: AsyncSession, refresh_token: str
) -> tuple[TokenResponse, str]:
    stmt = (
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(refresh_token))
        .with_for_update()
    )
    stored_token = await db.scalar(stmt)
    if stored_token is None:
        raise InvalidRefreshTokenError("Invalid refresh token")

    now = datetime.now(UTC)

    if stored_token.revoked_at is not None:
        if stored_token.replaced_by_id is not None:
            await _revoke_all_refresh_tokens(db, stored_token.user_id, now)
            await db.commit()
        raise InvalidRefreshTokenError("Invalid refresh token")

    if stored_token.expires_at <= now:
        raise InvalidRefreshTokenError("Invalid refresh token")

    user = await db.get(User, stored_token.user_id)
    if user is None or not user.is_active:
        raise InvalidRefreshTokenError("Invalid refresh token")

    new_refresh_token, new_stored_token = _issue_refresh_token(db, user.id)
    await db.flush()
    stored_token.revoked_at = now
    stored_token.replaced_by_id = new_stored_token.id
    await db.commit()

    response = TokenResponse(access_token=create_access_token({"sub": str(user.id)}))
    return response, new_refresh_token


async def logout_user(db: AsyncSession, refresh_token: str) -> None:
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == hash_refresh_token(refresh_token),
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> tuple[ChangePasswordResponse, str]:
    if not await verify_password(current_password, user.password_hash):
        raise IncorrectPasswordError("Current password is incorrect")

    user.password_hash = await hash_password(new_password)

    await _revoke_all_refresh_tokens(db, user.id, datetime.now(UTC))

    refresh_token, _ = _issue_refresh_token(db, user.id)

    await db.commit()
    await db.refresh(user)

    response = ChangePasswordResponse(
        message="Password changed successfully",
        access_token=create_access_token({"sub": str(user.id)}),
        user=user,
    )
    return response, refresh_token


def _issue_refresh_token(
    db: AsyncSession, user_id: uuid.UUID
) -> tuple[str, RefreshToken]:
    raw_token = generate_refresh_token()
    stored_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(UTC)
        + timedelta(seconds=settings.refresh_token_expire_seconds),
    )
    db.add(stored_token)
    return raw_token, stored_token


async def _revoke_all_refresh_tokens(
    db: AsyncSession, user_id: uuid.UUID, revoked_at: datetime
) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=revoked_at)
    )
