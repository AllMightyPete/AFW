from __future__ import annotations

"""Client protocol for language model integrations."""

from typing import Protocol


class LLMClient(Protocol):
    """Protocol for language model clients."""

    def complete(self, prompt: str, **kwargs: object) -> str:
        """Return the model's textual completion for ``prompt``."""


class NoOpLLMClient:
    """Fallback LLM client that returns an empty response."""

    def complete(
        self, prompt: str, **kwargs: object
    ) -> str:  # pragma: no cover - trivial
        return ""
