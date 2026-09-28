from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: PostgresDsn
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_seconds: int = 900
    health_check_timeout_seconds: float = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
