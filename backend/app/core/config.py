from pydantic import (BaseModel, Field, SecretStr)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = PROJECT_ROOT / '.env',
        env_file_encoding = 'utf-8',
        extra="ignore",
    )

    app_name: str = "copper-lead-triage"
    version: str = "0.1.0"
    description: str = "An addon to copper CRM which fills out missing data for leads"
    database_path: Path = Field(
        default=PROJECT_ROOT / "data" / "lead_triage.sqlite3",
        alias="DATABASE_PATH",
        description="Local SQLite database path for saved analysis data",
    )
    database_url: str = Field(
        default=f"sqlite:///{(PROJECT_ROOT / 'data' / 'lead_triage.sqlite3').as_posix()}",
        alias="DATABASE_URL",
        description="SQLAlchemy database URL for saved analysis data",
    )

# Copper CRM API credentials
    copper_api_key: SecretStr = Field(description="API Key for Copper CRM")
    copper_email: str = Field(default="codi@stepandrepeatla.com", description="Email address of API key owner")

# LLM API credentials
    zai_api_key: SecretStr = Field(alias="CEREBRAS_API_KEY", description="API Key for GLM LLM")
    anthropic_api_key: SecretStr = Field(validation_alias="ANTHROPIC_API_KEY", description="API Key for Claude LLM")
    pydantic_ai_gateway_api_key: SecretStr = Field(alias="PYDANTIC_AI_GATEWAY_API_KEY", description="API Key for Pydantic AI Gateway")


@lru_cache()
def get_settings():
    return Settings()
