from __future__ import annotations

"""Concrete :class:`LLMClient` implementation for the Ollama API."""

import json
from typing import List
from urllib import request

from ..config_models import ClassificationSettings, LLMProviderProfile
from .client import LLMClient  # noqa: F401


class OllamaClient:
    """Simple client that talks to an Ollama server."""

    def __init__(
        self, base_url: str, model: str, reasoning_effort: str | None = None
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._reasoning_effort = reasoning_effort

    # ------------------------------------------------------------------
    def complete(self, prompt: str, **kwargs: object) -> str:
        payload = {"model": self._model, "prompt": prompt}
        if self._reasoning_effort:
            payload["reasoning"] = {"effort": self._reasoning_effort}
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self._base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req) as resp:  # nosec - API call
                body = resp.read().decode("utf-8")
                result = json.loads(body)
                return result.get("response") or result.get("data", "")
        except Exception:  # pragma: no cover - defensive
            return ""

    # ------------------------------------------------------------------
    @classmethod
    def from_settings(
        cls, settings: ClassificationSettings, provider: str = "ollama"
    ) -> "OllamaClient":
        profile = cls._get_profile(settings.providers, provider)
        return cls(
            profile.base_url,
            profile.model,
            reasoning_effort=profile.reasoning_effort or None,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _get_profile(
        providers: List[LLMProviderProfile],
        provider: str,
    ) -> LLMProviderProfile:
        for profile in providers:
            if profile.provider.lower() == provider:
                return profile
        raise ValueError(f"No {provider} provider profile configured")
