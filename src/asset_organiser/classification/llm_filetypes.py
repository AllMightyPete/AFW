from __future__ import annotations

from ..llm.client import LLMClient
from .models import ClassificationState
from .module import ClassificationModule


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
