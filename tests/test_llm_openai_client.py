import sys
import types

from asset_organiser.config_models import (  # noqa: E501
    ClassificationSettings,
    LLMProviderProfile,
)
from asset_organiser.llm.openai import OpenAIClient


def test_openai_client_from_settings(monkeypatch):
    """OpenAI client retrieves credentials from configuration."""

    class FakeCompletions:
        def __init__(self) -> None:
            self.calls = []

        def create(
            self,
            model,
            messages,
            **kwargs,
        ):  # noqa: D401 - simple stub
            self.calls.append((model, messages, kwargs))
            choice = types.SimpleNamespace(
                message=types.SimpleNamespace(content="response")
            )
            return types.SimpleNamespace(choices=[choice])

    class FakeOpenAI:
        def __init__(
            self, api_key: str, base_url: str | None = None
        ) -> None:  # noqa: D401 - simple stub
            self.api_key = api_key
            self.base_url = base_url
            self.chat = types.SimpleNamespace(completions=FakeCompletions())

    fake_module = types.SimpleNamespace(OpenAI=FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_module)

    settings = ClassificationSettings(
        provider="OpenAI",
        providers=[
            LLMProviderProfile(
                profile_name="default",
                provider="OpenAI",
                api_key="KEY",
                base_url="http://example",
                model="gpt-test",
            )
        ],
    )

    client = OpenAIClient.from_settings(settings)
    result = client.complete("prompt")
    assert result == "response"
