from __future__ import annotations

"""LLM assisted tagging module."""

import re

from .llm_filetypes import LLMClient, NoOpLLMClient
from .models import ClassificationState
from .module import ClassificationModule


class LLMTaggingModule(ClassificationModule):
    """Populate ``asset_tags`` for assets using a language model.

    The module accepts an :class:`LLMClient` but falls back to a
    :class:`NoOpLLMClient` to keep behaviour deterministic for tests.  When
    the client returns an empty response, simple heuristics based on the
    ``asset_name`` are used to generate tags.
    """

    def __init__(
        self, client: LLMClient | None = None, prompt: str | None = None
    ) -> None:
        super().__init__()
        self.client = client or NoOpLLMClient()
        self.prompt = prompt or ""

    def run(self, state: ClassificationState) -> ClassificationState:
        for source in state.sources.values():
            for asset in source.assets.values():
                if asset.asset_tags:
                    continue
                name = asset.asset_name or ""
                full_prompt = f"{self.prompt}\nAsset name: {name}".strip()
                result = self.client.complete(full_prompt).strip()
                if result:
                    tags = [t.strip() for t in result.split(",") if t.strip()]
                else:
                    tags = [t for t in re.split(r"[\W_]+", name.lower()) if t]
                asset.asset_tags.extend(tags)
        return state
