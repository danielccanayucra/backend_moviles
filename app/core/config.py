from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    # ----------------------------------
    # 🔧 Configuración general
    # ----------------------------------
    APP_NAME: str = "EstuRooms API"
    ENVIRONMENT: str = "dev"
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET_32_BYTES_MIN"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200

    # ----------------------------------
    # 🗄️ Base de datos
    # Se obtiene del .env obligatoriamente
    # ----------------------------------
    DB_URL: str

    # ----------------------------------
    # 🌍 URL pública del backend
    # NECESARIA PARA IMÁGENES
    # ----------------------------------
    BASE_URL: str = "http://localhost:8000"

    # ----------------------------------
    # 📧 SMTP
    # ----------------------------------
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_TLS: bool = False
    DEFAULT_FROM_EMAIL: str = "no-reply@esturooms.local"

    # ----------------------------------
    # 🔐 CORS
    # ----------------------------------
    ALLOWED_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"


settings = Settings()
