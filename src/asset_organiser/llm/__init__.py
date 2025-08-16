from ..config_models import LLMProviderProfile
from .client import LLMClient, NoOpLLMClient
from .ollama import OllamaClient
from .openai import OpenAIClient


def create_llm_client(profile: LLMProviderProfile) -> LLMClient:
    """Instantiate an :class:`LLMClient` for ``profile``."""

    provider = profile.provider.lower()
    if provider == "openai":
        return OpenAIClient(
            profile.api_key,
            profile.model,
            base_url=profile.base_url or None,
            reasoning_effort=profile.reasoning_effort or None,
        )
    if provider == "ollama":
        return OllamaClient(
            profile.base_url,
            profile.model,
            reasoning_effort=profile.reasoning_effort or None,
        )
    raise ValueError(f"Unsupported provider: {profile.provider}")


__all__ = [
    "LLMClient",
    "NoOpLLMClient",
    "OpenAIClient",
    "OllamaClient",
    "create_llm_client",
]
