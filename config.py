"""
Application configuration.

Uses pydantic-settings to load configuration from environment variables.
Provides sensible defaults from constants.py while allowing override via .env.
"""

from pydantic_settings import BaseSettings
from pydantic import Field

from constants import (
    DEFAULT_CALORIE_TARGET,
    MIN_CALORIES_FEMALE,
    MIN_CALORIES_MALE,
    CONFIDENCE_WARNING_THRESHOLD,
    REMINDER_CHECK_INTERVAL_SECONDS,
    REMINDER_FIRST_RUN_DELAY_SECONDS,
    DEFAULT_REMINDER_HOUR,
)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # =========================================================================
    # TELEGRAM
    # =========================================================================
    telegram_bot_token: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")

    # =========================================================================
    # OPENAI
    # =========================================================================
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", validation_alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, validation_alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.3, validation_alias="OPENAI_TEMPERATURE")

    # =========================================================================
    # DATABASE
    # =========================================================================
    # SQLite (local fallback)
    database_path: str = Field(
        default="./data/foodgpt.db",
        validation_alias="DATABASE_PATH"
    )

    # Turso (cloud)
    use_turso: bool = Field(default=False, validation_alias="USE_TURSO")
    turso_db_url: str = Field(default="", validation_alias="TURSO_DB_URL")
    turso_auth_token: str = Field(default="", validation_alias="TURSO_AUTH_TOKEN")

    # =========================================================================
    # CALORIE CALCULATION (can override constants)
    # =========================================================================
    min_calories_female: int = Field(
        default=MIN_CALORIES_FEMALE,
        validation_alias="MIN_CALORIES_FEMALE"
    )
    min_calories_male: int = Field(
        default=MIN_CALORIES_MALE,
        validation_alias="MIN_CALORIES_MALE"
    )
    default_calorie_target: int = Field(
        default=DEFAULT_CALORIE_TARGET,
        validation_alias="DEFAULT_CALORIE_TARGET"
    )

    # =========================================================================
    # CONFIDENCE THRESHOLDS
    # =========================================================================
    confidence_warning_threshold: float = Field(
        default=CONFIDENCE_WARNING_THRESHOLD,
        validation_alias="CONFIDENCE_WARNING_THRESHOLD"
    )

    # =========================================================================
    # JOB SCHEDULING
    # =========================================================================
    reminder_interval_seconds: int = Field(
        default=REMINDER_CHECK_INTERVAL_SECONDS,
        validation_alias="REMINDER_INTERVAL_SECONDS"
    )
    reminder_first_run_delay: int = Field(
        default=REMINDER_FIRST_RUN_DELAY_SECONDS,
        validation_alias="REMINDER_FIRST_RUN_DELAY"
    )
    default_reminder_hour: int = Field(
        default=DEFAULT_REMINDER_HOUR,
        validation_alias="DEFAULT_REMINDER_HOUR"
    )

    # =========================================================================
    # LOGGING
    # =========================================================================
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # =========================================================================
    # FEATURE FLAGS (GROWTHBOOK)
    # =========================================================================
    growthbook_client_key: str = Field(
        default="",
        validation_alias="GROWTHBOOK_CLIENT_KEY"
    )
    growthbook_api_host: str = Field(
        default="https://cdn.growthbook.io",
        validation_alias="GROWTHBOOK_API_HOST"
    )

    # =========================================================================
    # ADMIN
    # =========================================================================
    admin_user_id: int = Field(default=0, validation_alias="ADMIN_USER_ID")

    # =========================================================================
    # MINI APP / WEBAPP
    # =========================================================================
    webapp_enabled: bool = Field(default=True, validation_alias="WEBAPP_ENABLED")
    webapp_port: int = Field(default=8080, validation_alias="WEBAPP_PORT")
    webapp_url: str = Field(default="", validation_alias="WEBAPP_URL")

    @property
    def telegram_token(self) -> str:
        """Alias for telegram_bot_token for convenience."""
        return self.telegram_bot_token

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Create singleton instance
settings = Settings()
