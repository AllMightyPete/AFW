from __future__ import annotations

from typing import Iterable

from ..config_service import ConfigService
from .constants import AssignConstantsModule
from .models import ClassificationState
from .module import ClassificationModule
from .pipeline import ClassificationPipeline
from .rule_based import RuleBasedFileTypeModule


class _LLMPlaceholderModule(ClassificationModule):
    """Placeholder for a future LLM-based classification module."""

    def __init__(self, name: str = "LLMModule") -> None:
        super().__init__(name)

    def run(self, state: ClassificationState) -> ClassificationState:
        return state


class ClassificationService:
    """High level service for executing classification pipelines."""

    def __init__(self, config_service: ConfigService) -> None:
        if config_service.library_config is None:
            raise RuntimeError("Library configuration not loaded")
        classification = config_service.library_config.CLASSIFICATION
        filetype_defs = config_service.library_config.FILE_TYPE_DEFINITIONS
        self.keyword_rules = classification.keyword_rules

        self.pipeline = ClassificationPipeline()
        const_module = AssignConstantsModule(self.keyword_rules)
        self.pipeline.add_module(const_module)
        rule_module = RuleBasedFileTypeModule(filetype_defs)
        self.pipeline.add_module(rule_module, after=[const_module.name])
        self.pipeline.add_module(
            _LLMPlaceholderModule(),
            after=[rule_module.name],
        )

    # ------------------------------------------------------------------
    def classify(self, state: ClassificationState) -> ClassificationState:
        """Run the configured pipeline on ``state``."""
        return self.pipeline.run(state)

    # ------------------------------------------------------------------
    @staticmethod
    def from_file_list(files: Iterable[str]) -> ClassificationState:
        """Create a :class:`ClassificationState` from a list of filenames."""
        contents = {str(i): {"filename": f} for i, f in enumerate(files)}
        data = {"sources": {"src": {"metadata": {}, "contents": contents}}}
        return ClassificationState.model_validate(data)
