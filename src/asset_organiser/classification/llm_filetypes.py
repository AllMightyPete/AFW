from __future__ import annotations

"""LLM-assisted filetype classification module."""

from typing import Protocol

from .models import ClassificationState
from .module import ClassificationModule


class LLMClient(Protocol):
    """Protocol for pluggable LLM clients."""

    def classify_filetype(self, filename: str, prompt: str | None = None) -> str | None:
        """Return a predicted filetype for ``filename``."""
        ...


class LLMFiletypeModule(ClassificationModule):
    """Classify filetypes using an LLM client for remaining files."""

    def __init__(self, client: LLMClient, prompt: str | None = None) -> None:
        super().__init__()
        self.client = client
        self.prompt = prompt

    def run(self, state: ClassificationState) -> ClassificationState:
        for source in state.sources.values():
            for entry in source.contents.values():
                if entry.filetype:
                    continue
                result = self.client.classify_filetype(entry.filename, self.prompt)
                if result:
                    entry.filetype = result
        return state
