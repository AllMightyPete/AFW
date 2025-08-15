from __future__ import annotations

from typing import Dict, List, Tuple

from .models import ClassificationState
from .module import ClassificationModule


class RuleBasedFileTypeModule(ClassificationModule):
    """Assign filetypes based on keyword rules from configuration."""

    def __init__(self, keyword_rules: Dict[str, str], next_module: str | None = None) -> None:
        super().__init__()
        self.keyword_rules = {k.lower(): v for k, v in keyword_rules.items()}
        self._next_module = next_module

    def run(
        self, state: ClassificationState
    ) -> ClassificationState | Tuple[ClassificationState, List[str]]:
        for source in state.sources.values():
            for entry in source.contents.values():
                if entry.filetype:
                    continue
                name = entry.filename.lower()
                for keyword, filetype in self.keyword_rules.items():
                    if keyword in name:
                        entry.filetype = filetype
                        break

        if self._next_module is not None:
            has_unclassified = any(
                entry.filetype is None
                for source in state.sources.values()
                for entry in source.contents.values()
            )
            next_mods = [self._next_module] if has_unclassified else []
            return state, next_mods

        return state
