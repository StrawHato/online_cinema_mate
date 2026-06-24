import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///online_cinema.db"

    BASE_DIR: Path = Path(__file__).parent.parent

    PATH_TO_EMAIL_TEMPLATES_DIR: str = str(
        BASE_DIR / "notifications" / "templates"
    )
    ACTIVATION_EMAIL_TEMPLATE_NAME: str = "activation_request.html"
    ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME: str = "activation_complete.html"
    PASSWORD_RESET_TEMPLATE_NAME: str = "password_reset_request.html"
    PASSWORD_RESET_COMPLETE_TEMPLATE_NAME: str = "password_reset_complete.html"

    EMAIL_HOST: str = os.getenv("EMAIL_HOST")
    EMAIL_PORT: int = os.getenv("EMAIL_PORT")
    EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD: str = os.getenv("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS").lower() == "true"

    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS")
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH")
    JWT_SIGNING_ALGORITHM: str = os.getenv("JWT_SIGNING_ALGORITHM", "HS256")


@lru_cache
def get_settings() -> Settings:
    return Settings()
