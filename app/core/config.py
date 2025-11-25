from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
import os


class Settings(BaseSettings):
    APP_NAME: str = "EstuRooms API"
    ENVIRONMENT: str = "dev"
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET_32_BYTES_MIN"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200
    DB_URL: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_TLS: bool = False
    DEFAULT_FROM_EMAIL: str = "no-reply@esturooms.local"
    ALLOWED_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"

settings = Settings()
