from pydantic import (BaseModel, Field, SecretStr)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = '.env',
        env_file_encoding = 'utf-8',
        extra="ignore",
    )

    app_name: str = "copper-lead-triage"
    version: str = "0.1.0"
    description: str = "An addon to copper CRM which fills out missing data for leads"

# Copper CRM API credentials
    copper_api_key: SecretStr = Field(description="API Key for Copper CRM")
    copper_email: str = Field(default="codi@stepandrepeatla.com", description="Email address of API key owner")

# LLM API credentials
    zai_api_key: SecretStr = Field(alias="CEREBRAS_API_KEY", description="API Key for GLM LLM")
    anthropic_api_key: SecretStr = Field(validation_alias="ANTHROPIC_API_KEY", description="API Key for Claude LLM")


@lru_cache()
def get_settings():
    return Settings()