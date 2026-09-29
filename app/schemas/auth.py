import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

type NormalizedEmail = Annotated[EmailStr, AfterValidator(str.lower)]
type Password = Annotated[str, Field(min_length=8, max_length=128)]
type Name = Annotated[str, Field(min_length=1, max_length=255)]


class RegisterRequest(BaseModel):
    email: NormalizedEmail
    password: Password
    first_name: Name
    last_name: Name


class LoginRequest(BaseModel):
    email: NormalizedEmail
    password: str = Field(max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool


class LoginResponse(BaseModel):
    message: str
    access_token: str
    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: Password


class ChangePasswordResponse(BaseModel):
    message: str
    access_token: str
    user: UserResponse
