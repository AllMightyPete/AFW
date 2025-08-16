from __future__ import annotations

from typing import Dict, List

from ..config_models import AssetTypeDefinition, FileTypeDefinition
from .models import ClassificationState
from .module import ClassificationModule

FileTypeDefs = Dict[str, FileTypeDefinition]
AssetTypeDefs = Dict[str, AssetTypeDefinition]


class RuleBasedFileTypeModule(ClassificationModule):
    """Assign filetypes based on ``rule_keywords`` in configuration."""

    def __init__(
        self,
        filetype_definitions: FileTypeDefs,
        *,
        next_module: str | None = None,
    ) -> None:
        super().__init__()
        keyword_rules: Dict[str, str] = {}
        for filetype, definition in filetype_definitions.items():
            for keyword in definition.rule_keywords:
                keyword_rules[keyword.lower()] = filetype
        self.keyword_rules = keyword_rules
        self._next_module = next_module

    def run(
        self, state: ClassificationState
    ) -> ClassificationState | tuple[ClassificationState, List[str]]:
        route = False
        for source in state.sources.values():
            for entry in source.contents.values():
                if entry.filetype:
                    continue
                name = entry.filename.lower()
                matched = False
                for keyword, filetype in self.keyword_rules.items():
                    if keyword in name:
                        entry.filetype = filetype
                        matched = True
                        break
                if not matched:
                    route = True
        if self._next_module and route:
            return state, [self._next_module]
        return state


class KeywordAssetTypeModule(ClassificationModule):
    """Assign asset types based on ``rule_keywords`` of asset definitions."""

    def __init__(
        self,
        assettype_definitions: AssetTypeDefs,
        *,
        next_module: str | None = None,
    ) -> None:
        super().__init__()
        keyword_rules: Dict[str, str] = {}
        for asset_type, definition in assettype_definitions.items():
            for keyword in definition.rule_keywords:
                keyword_rules[keyword.lower()] = asset_type
        self.keyword_rules = keyword_rules
        self._next_module = next_module

    def run(
        self, state: ClassificationState
    ) -> ClassificationState | tuple[ClassificationState, List[str]]:
        route = False
        for source in state.sources.values():
            for asset in source.assets.values():
                if asset.asset_type:
                    continue
                name = (asset.asset_name or "").lower()
                matched = False
                for keyword, asset_type in self.keyword_rules.items():
                    if keyword in name:
                        asset.asset_type = asset_type
                        matched = True
                        break
                if not matched:
                    route = True
        if self._next_module and route:
            return state, [self._next_module]
        return state
