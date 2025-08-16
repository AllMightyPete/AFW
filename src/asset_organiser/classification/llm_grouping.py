from __future__ import annotations

from pathlib import Path
from typing import Dict

from .llm_filetypes import LLMClient, NoOpLLMClient
from .models import AssetEntry, ClassificationState
from .module import ClassificationModule


class LLMGroupFilesModule(ClassificationModule):
    """Group unassigned files into assets based on filename patterns.

    This module is a lightweight stand-in for an LLM powered grouping system.
    It analyses remaining files (those not already referenced by an asset) and
    groups them by a simple heuristic: files sharing the same directory and the
    same prefix before the first underscore are considered part of the same
    asset.  The heuristic keeps the implementation deterministic for testing
    while exposing a hook for future LLM assistance via ``LLMClient``.
    """

    def __init__(self, client: LLMClient | None = None) -> None:
        super().__init__()
        self.client = client or NoOpLLMClient()

    # ------------------------------------------------------------------
    def _new_asset_id(self, existing: Dict[str, AssetEntry]) -> str:
        i = 0
        while str(i) in existing:
            i += 1
        return str(i)

    # ------------------------------------------------------------------
    def run(self, state: ClassificationState) -> ClassificationState:
        for source in state.sources.values():
            assigned = {
                file_id
                for asset in source.assets.values()
                for file_id in asset.asset_contents
            }
            groups: Dict[str, str] = {}
            for file_id, entry in source.contents.items():
                if file_id in assigned:
                    continue
                path = Path(entry.filename)
                prefix = path.stem.split("_")[0]
                key = str(path.parent / prefix)
                if key not in groups:
                    asset_id = self._new_asset_id(source.assets)
                    groups[key] = asset_id
                    source.assets[asset_id] = AssetEntry(asset_contents=[])
                asset_id = groups[key]
                source.assets[asset_id].asset_contents.append(file_id)
        return state
