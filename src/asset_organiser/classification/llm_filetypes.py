from __future__ import annotations

from typing import Protocol

from .models import ClassificationState
from .module import ClassificationModule


class LLMClient(Protocol):
    """Protocol for LLM clients used by :class:`LLMFiletypeModule`."""

    def complete(self, prompt: str) -> str:
        """Return the model's textual completion for ``prompt``."""


class NoOpLLMClient:
    """Fallback LLM client that performs no classification."""

    def complete(self, prompt: str) -> str:  # pragma: no cover - trivial
        return ""


class LLMFiletypeModule(ClassificationModule):
    """Classify filetypes using a language model."""

    def __init__(self, client: LLMClient, prompt: str) -> None:
        super().__init__()
        self.client = client
        self.prompt = prompt

    def run(self, state: ClassificationState) -> ClassificationState:
        for source in state.sources.values():
            for entry in source.contents.values():
                if entry.filetype:
                    continue
                full_prompt = f"{self.prompt}\nFilename: {entry.filename}"
                result = self.client.complete(full_prompt).strip()
                if result:
                    entry.filetype = result
        return state
