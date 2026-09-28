from fastapi import APIRouter, HTTPException, status

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DbSession
from app.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(data: RegisterRequest, db: DbSession):
    try:
        return await auth_service.register_user(db, data)
    except auth_service.EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(data: LoginRequest, db: DbSession):
    try:
        return await auth_service.login_user(db, data)
    except auth_service.InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


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
):
    try:
        return await auth_service.change_password(
            db, current_user, data.current_password, data.new_password
        )
    except auth_service.IncorrectPasswordError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
