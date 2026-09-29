from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Response, status

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DbSession
from app.core.config import settings
from app.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_TOKEN_COOKIE_PATH = "/v1/auth"

RefreshTokenCookie = Annotated[
    str | None, Cookie(alias=REFRESH_TOKEN_COOKIE, max_length=256)
]


def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=settings.refresh_token_expire_seconds,
        path=REFRESH_TOKEN_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,
    )


def clear_refresh_token_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        path=REFRESH_TOKEN_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,
    )


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(data: RegisterRequest, db: DbSession):
    try:
        return await auth_service.register_user(db, data)
    except auth_service.EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(data: LoginRequest, db: DbSession, response: Response):
    try:
        login_response, refresh_token = await auth_service.login_user(db, data)
    except auth_service.InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    set_refresh_token_cookie(response, refresh_token)
    return login_response


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(
    db: DbSession, response: Response, refresh_token: RefreshTokenCookie = None
):
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )

    try:
        token_response, new_refresh_token = await auth_service.refresh_access_token(
            db, refresh_token
        )
    except auth_service.InvalidRefreshTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    set_refresh_token_cookie(response, new_refresh_token)
    return token_response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    db: DbSession, response: Response, refresh_token: RefreshTokenCookie = None
):
    if refresh_token is not None:
        await auth_service.logout_user(db, refresh_token)
    clear_refresh_token_cookie(response)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def me(current_user: CurrentUser):
    return current_user


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DbSession,
    response: Response,
):
    try:
        change_response, refresh_token = await auth_service.change_password(
            db, current_user, data.current_password, data.new_password
        )
    except auth_service.IncorrectPasswordError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    set_refresh_token_cookie(response, refresh_token)
    return change_response
