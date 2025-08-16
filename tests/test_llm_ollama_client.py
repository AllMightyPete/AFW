from asset_organiser.config_models import ClassificationSettings
from asset_organiser.llm.ollama import OllamaClient


def test_default_profile_and_client(monkeypatch):
    """Ollama client uses the default profile from settings."""

    class FakeResponse:
        def __init__(self) -> None:
            self._data = b'{"response": "ok"}'

        def read(self) -> bytes:  # pragma: no cover - simple helper
            return self._data

        def __enter__(self):  # pragma: no cover - simple helper
            return self

        def __exit__(
            self, exc_type, exc, tb
        ) -> None:  # pragma: no cover - simple helper
            pass

    def fake_urlopen(req):  # noqa: D401 - simple stub
        return FakeResponse()

    monkeypatch.setattr(
        "asset_organiser.llm.ollama.request.urlopen",
        fake_urlopen,
    )

    settings = ClassificationSettings()
    client = OllamaClient.from_settings(settings)
    assert client.complete("hi") == "ok"

    profile = settings.providers[0]
    assert profile.profile_name == "mistral small"
    assert profile.base_url == "https://api.llm.gestaltservers.com"
    assert profile.model == "deepseek-r1:1.5b"
    assert profile.reasoning_effort == "Low"
