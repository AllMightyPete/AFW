from __future__ import annotations

from typing import Dict

from ..config_models import FileTypeDefinition
from .models import ClassificationState
from .module import ClassificationModule

FileTypeDefs = Dict[str, FileTypeDefinition]


class RuleBasedFileTypeModule(ClassificationModule):
    """Assign filetypes based on ``rule_keywords`` in configuration."""

    def __init__(self, filetype_definitions: FileTypeDefs) -> None:
        super().__init__()
        keyword_rules: Dict[str, str] = {}
        for filetype, definition in filetype_definitions.items():
            for keyword in definition.rule_keywords:
                keyword_rules[keyword.lower()] = filetype
        self.keyword_rules = keyword_rules

    def run(self, state: ClassificationState) -> ClassificationState:
        for source in state.sources.values():
            for entry in source.contents.values():
                if entry.filetype:
                    continue
                name = entry.filename.lower()
                for keyword, filetype in self.keyword_rules.items():
                    if keyword in name:
                        entry.filetype = filetype
                        break
        return state
