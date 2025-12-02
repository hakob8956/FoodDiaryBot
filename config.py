import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Telegram
    telegram_bot_token: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")

    # OpenAI
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", validation_alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, validation_alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.3, validation_alias="OPENAI_TEMPERATURE")

    # Database
    database_path: str = Field(default="./data/foodgpt.db", validation_alias="DATABASE_PATH")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # GrowthBook Feature Flags
    growthbook_client_key: str = Field(default="", validation_alias="GROWTHBOOK_CLIENT_KEY")
    growthbook_api_host: str = Field(default="https://cdn.growthbook.io", validation_alias="GROWTHBOOK_API_HOST")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Create singleton instance
settings = Settings()
