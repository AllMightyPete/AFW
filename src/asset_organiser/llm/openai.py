from __future__ import annotations

"""Concrete :class:`LLMClient` implementation for OpenAI compatible APIs."""

from typing import List

from ..config_models import ClassificationSettings, LLMProviderProfile
from .client import LLMClient  # noqa: F401


class OpenAIClient:
    """LLM client that communicates with OpenAI's chat completion API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        try:  # defer import so that tests can run without the dependency
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - import guarded
            raise RuntimeError(
                "The 'openai' package is required to use OpenAIClient",
            ) from exc
        self._client = OpenAI(api_key=api_key, base_url=base_url or None)
        self._model = model
        self._reasoning_effort = reasoning_effort

    # ------------------------------------------------------------------
    def complete(self, prompt: str, **kwargs: object) -> str:
        """Return the completion text for ``prompt``."""

        if self._reasoning_effort and "reasoning" not in kwargs:
            kwargs["reasoning"] = {"effort": self._reasoning_effort}
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        try:  # support both dict-like and attribute access styles
            choice = response.choices[0]
            message = getattr(choice, "message", None) or choice.get("message")
            content = getattr(message, "content", None)
            if content is None:
                content = message.get("content")
            return content or ""
        except Exception:  # pragma: no cover - defensive
            return ""

    # ------------------------------------------------------------------
    @classmethod
    def from_settings(
        cls, settings: ClassificationSettings, provider: str = "openai"
    ) -> "OpenAIClient":
        """Initialise the client from :class:`ClassificationSettings`."""

        profile = cls._get_profile(settings.providers, provider)
        return cls(
            profile.api_key,
            profile.model,
            base_url=profile.base_url or None,
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
