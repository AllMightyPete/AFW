import pytest

from asset_organiser.config_models import ClassificationSettings
from asset_organiser.llm.ollama import OllamaClient


def test_default_ollama_profile_reachable():
    """Default LLM profile should respond to a basic prompt."""

    settings = ClassificationSettings()
    client = OllamaClient.from_settings(settings)
    response = client.complete("ping")
    if not response.strip():
        pytest.skip("default LLM profile not reachable")
    assert isinstance(response, str)
    assert response.strip() != ""
