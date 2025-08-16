from __future__ import annotations

from .llm_filetypes import LLMClient, NoOpLLMClient
from .models import ClassificationState
from .module import ClassificationModule


class LLMAssetTypeModule(ClassificationModule):
    """Classify unresolved asset types using a language model."""

    def __init__(self, client: LLMClient | None, prompt: str) -> None:
        super().__init__()
        self.client = client or NoOpLLMClient()
        self.prompt = prompt

    def run(self, state: ClassificationState) -> ClassificationState:
        for source in state.sources.values():
            for asset in source.assets.values():
                if asset.asset_type:
                    continue
                name = asset.asset_name or ""
                full_prompt = f"{self.prompt}\nAsset name: {name}"
                result = self.client.complete(full_prompt).strip()
                if result:
                    asset.asset_type = result
        return state
