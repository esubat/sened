from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    DUMMY_HASHED_PASSWORD,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
)


class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class IncorrectPasswordError(Exception):
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


async def login_user(db: AsyncSession, data: LoginRequest) -> LoginResponse:
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

    return LoginResponse(
        message="Login successful",
        access_token=access_token,
        user=user,
    )


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> ChangePasswordResponse:
    if not await verify_password(current_password, user.password_hash):
        raise IncorrectPasswordError("Current password is incorrect")

    user.password_hash = await hash_password(new_password)
    await db.commit()
    await db.refresh(user)

    return ChangePasswordResponse(message="Password changed successfully", user=user)
