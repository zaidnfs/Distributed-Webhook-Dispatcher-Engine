from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    DATABASE_URL: str = "sqlite:///./webhooks.db"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"

    MAX_RETRIES: int = 3
    BACKOFF_BASE_SECONDS: int = 2

    RATE_LIMIT_PER_DOMAIN: int = 5

    DELIVERY_TIMEOUT_SECONDS: int = 10


settings = Settings()
