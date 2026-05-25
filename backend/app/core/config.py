from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "OrionOS"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_teammate"

    SECRET_KEY: str = "insecure-dev-key-replace-in-production-via-env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    CORS_ORIGINS: list[str] = ["*"]

    MAX_REQUEST_SIZE: int = 110 * 1024 * 1024  # 110 MB (allow ZIP uploads up to 100 MB)
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60  # seconds

    OPENAI_API_KEY: Optional[str] = None

    # Stripe — set these in backend/.env
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRO_PRICE_ID: Optional[str] = None
    STRIPE_TEAM_PRICE_ID: Optional[str] = None

    # Feature flags
    STRIPE_ENABLED: bool = False  # auto-set to True when STRIPE_SECRET_KEY is present


settings = Settings()

# Auto-enable Stripe when key is present
if settings.STRIPE_SECRET_KEY:
    settings.STRIPE_ENABLED = True
