from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Yash Technology Outreach Hub"
    app_env: str = "development"
    database_url: str = Field(
        default="postgresql+psycopg://postgres:root@localhost:5432/yash_outreach",
        alias="DATABASE_URL",
    )
    cors_origins: str = Field(default="http://localhost:8501,http://localhost:3000", alias="CORS_ORIGINS")
    frontend_base_url: str = Field(default="http://localhost:8501", alias="FRONTEND_BASE_URL")
    default_daily_send_limit: int = Field(default=30, alias="DEFAULT_DAILY_SEND_LIMIT")
    write_api_key: str = Field(default="", alias="WRITE_API_KEY")
    apollo_base_url: str = Field(default="https://api.apollo.io/api/v1", alias="APOLLO_BASE_URL")
    apollo_daily_call_limit: int = Field(default=500, alias="APOLLO_DAILY_CALL_LIMIT")
    apollo_max_companies_per_run: int = Field(default=50, alias="APOLLO_MAX_COMPANIES_PER_RUN")
    apollo_max_contacts_per_company: int = Field(default=10, alias="APOLLO_MAX_CONTACTS_PER_COMPANY")
    apollo_min_seconds_between_calls: float = Field(default=1.0, alias="APOLLO_MIN_SECONDS_BETWEEN_CALLS")
    apollo_retry_limit: int = Field(default=3, alias="APOLLO_RETRY_LIMIT")
    discovery_enabled_providers: str = Field(default="apollo", alias="DISCOVERY_ENABLED_PROVIDERS")
    discovery_schedule_hour_utc: int = Field(default=2, alias="DISCOVERY_SCHEDULE_HOUR_UTC")
    discovery_schedule_minute_utc: int = Field(default=0, alias="DISCOVERY_SCHEDULE_MINUTE_UTC")
    enable_automation_scheduler: bool = Field(default=False, alias="ENABLE_AUTOMATION_SCHEDULER")

    apollo_api_key: str = Field(default="", alias="APOLLO_API_KEY")
    hunter_api_key: str = Field(default="", alias="HUNTER_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_draft_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_DRAFT_MODEL")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="", alias="SMTP_FROM")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND")

    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str):
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
