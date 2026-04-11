import time
import logfire
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pprint import pprint
import httpx
from typing import Dict

from backend.app.core.config import get_settings

settings = get_settings()
anthropic_api_key = settings.anthropic_api_key.get_secret_value()

provider = AnthropicProvider(api_key=anthropic_api_key)
model = AnthropicModel("claude-haiku-4-5", provider=provider)
my_agent = Agent(model)


result = my_agent.run_sync(user_prompt="tell me a funny joke")


print(result.output)