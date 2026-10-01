from typing import Literal

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: PostgresDsn
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_seconds: int = 900
    refresh_token_expire_seconds: int = 60 * 60 * 24 * 30
    refresh_token_cookie_secure: bool = True
    refresh_token_cookie_samesite: Literal["lax", "strict", "none"] = "strict"
    health_check_timeout_seconds: float = 2
    s3_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str
    s3_secret_access_key: SecretStr
    s3_bucket: str = "sened-storage"
    s3_presigned_url_expire_seconds: int = 900

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
