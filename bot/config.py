"""Configuration management using pydantic-settings."""
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with Railway-compatible defaults."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ========== REQUIRED FIELDS ==========
    # Bot - Must be provided
    bot_token: str = Field(..., alias="BOT_TOKEN")
    bot_username: str = Field(..., alias="BOT_USERNAME")
    
    # Database - Must be provided
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    
    # ========== OPTIONAL FIELDS WITH DEFAULTS ==========
    # Website Integration
    website_url: str = Field(
        default="https://under-people-club.vercel.app",
        alias="WEBSITE_URL"
    )
    website_api_key: str = Field(
        default="dev_api_key_change_in_production",
        alias="WEBSITE_API_KEY"
    )
    website_webhook_secret: str = Field(
        default="dev_webhook_secret_change_in_production",
        alias="WEBSITE_WEBHOOK_SECRET"
    )
    
    # Telegram Login Widget
    telegram_bot_id: int = Field(
        default=8446133461,
        alias="TELEGRAM_BOT_ID"
    )
    telegram_login_callback_url: str = Field(
        default="https://underpeople.club/auth/telegram",
        alias="TELEGRAM_LOGIN_CALLBACK_URL"
    )
    
    # Security
    secret_key: str = Field(
        default="dev_secret_key_change_in_production_32chars",
        alias="SECRET_KEY"
    )
    jwt_secret: str = Field(
        default="dev_jwt_secret_change_in_production_key",
        alias="JWT_SECRET"
    )
    encryption_key: str = Field(
        default="12345678901234567890123456789012",  # Exactly 32 chars
        alias="ENCRYPTION_KEY"
    )
    
    # Admins
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")
    
    # Payment
    payment_provider_token: str = Field(
        default="dev_payment_token",
        alias="PAYMENT_PROVIDER_TOKEN"
    )
    payment_webhook_url: str = Field(
        default="https://example.com/payment-webhook",
        alias="PAYMENT_WEBHOOK_URL"
    )
    
    # Sentry
    sentry_dsn: str | None = Field(None, alias="SENTRY_DSN")
    
    # Feature Flags
    enable_card_game: bool = Field(True, alias="ENABLE_CARD_GAME")
    enable_mini_games: bool = Field(True, alias="ENABLE_MINI_GAMES")
    enable_referral_system: bool = Field(True, alias="ENABLE_REFERRAL_SYSTEM")
    
    # Rate Limiting
    rate_limit_requests: int = Field(30, alias="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(60, alias="RATE_LIMIT_PERIOD")
    
    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_format: str = Field("json", alias="LOG_FORMAT")
    
    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            # Try to parse as JSON list first
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Otherwise parse as comma-separated
            return [int(id.strip()) for id in v.split(",") if id.strip()]
        elif isinstance(v, list):
            return v
        elif isinstance(v, int):
            return [v]
        return v
    
    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v):
        if len(v) != 32:
            raise ValueError("ENCRYPTION_KEY must be exactly 32 characters")
        return v
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in self.admin_ids


# Global settings instance
settings = Settings()
