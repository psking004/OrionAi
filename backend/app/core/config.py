from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "AI Teammate"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_teammate"

    # Must be set in .env — no auto-generated default so JWTs survive restarts
    SECRET_KEY: str = "insecure-dev-key-replace-in-production-via-env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Comma-separated or JSON list of allowed origins. Use "*" for dev.
    CORS_ORIGINS: list[str] = ["*"]

    MAX_REQUEST_SIZE: int = 1024 * 1024  # 1 MB
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60  # seconds

    OPENAI_API_KEY: Optional[str] = None


settings = Settings()
