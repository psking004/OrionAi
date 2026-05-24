from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    APP_NAME: str = "AI Teammate"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_teammate"

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    CORS_ORIGINS: list[str] = ["*"]

    MAX_REQUEST_SIZE: int = 1024 * 1024  # 1 MB
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60  # seconds

    OPENAI_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
