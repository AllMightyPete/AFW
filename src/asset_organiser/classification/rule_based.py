from __future__ import annotations

from typing import Dict

from .models import ClassificationState
from .module import ClassificationModule


class RuleBasedFileTypeModule(ClassificationModule):
    """Assign filetypes based on keyword rules from configuration."""

    def __init__(self, keyword_rules: Dict[str, str]) -> None:
        super().__init__()
        self.keyword_rules = {k.lower(): v for k, v in keyword_rules.items()}

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
