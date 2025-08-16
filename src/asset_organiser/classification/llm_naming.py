from __future__ import annotations

from pathlib import Path

from ..llm.client import LLMClient, NoOpLLMClient
from .models import ClassificationState
from .module import ClassificationModule


class LLMAssetNameModule(ClassificationModule):
    """Assign names to grouped assets using a language model."""

    def __init__(self, client: LLMClient | None = None) -> None:
        super().__init__()
        self.client = client or NoOpLLMClient()

    def run(self, state: ClassificationState) -> ClassificationState:
        for source in state.sources.values():
            for asset in source.assets.values():
                if asset.asset_name:
                    continue
                if not asset.asset_contents:
                    continue
                filenames = []
                for fid in asset.asset_contents:
                    filenames.append(source.contents[fid].filename)
                # invoke client for future expansion / count tracking
                _ = self.client.complete("\n".join(filenames))
                first = filenames[0]
                asset.asset_name = Path(first).stem.split("_")[0]
        return state
