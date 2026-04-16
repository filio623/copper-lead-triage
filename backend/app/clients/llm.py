from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.gateway import gateway_provider

from backend.app.core.config import get_settings


# This is the default model name for the first triage task.
# Keeping it as a module constant makes it easy to find and change later
# without hunting through service files.
DEFAULT_TRIAGE_MODEL = "gpt-5.4-nano"


def get_triage_model(model_name: str = DEFAULT_TRIAGE_MODEL) -> OpenAIChatModel:
    # This centralizes provider and API-key setup so `services/triage.py`
    # can focus on task behavior instead of wiring.
    settings = get_settings()
    provider = gateway_provider(
        "openai",
        api_key=settings.pydantic_ai_gateway_api_key.get_secret_value(),
    )
    return OpenAIChatModel(model_name, provider=provider)


def get_triage_model_metadata(model_name: str = DEFAULT_TRIAGE_MODEL) -> dict[str, str]:
    # This gives the triage layer a simple way to expose model metadata now,
    # even before persistence is built.
    return {
        "provider": "openai",
        "model": model_name,
    }
