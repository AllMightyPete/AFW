from __future__ import annotations

from typing import Iterable

from ..config_service import ConfigService
from .models import ClassificationState
from .pipeline import ClassificationPipeline
from .rule_based import RuleBasedFileTypeModule
from .llm_filetypes import LLMFiletypeModule, LLMClient


class _DummyLLMClient:
    """Fallback LLM client that performs no classification."""

    def classify_filetype(self, filename: str, prompt: str | None = None) -> str | None:
        return None


class ClassificationService:
    """High level service for executing classification pipelines."""

    def __init__(
        self, config_service: ConfigService, llm_client: LLMClient | None = None
    ) -> None:
        if config_service.library_config is None:
            raise RuntimeError("Library configuration not loaded")
        classification = config_service.library_config.CLASSIFICATION
        self.keyword_rules = classification.keyword_rules
        # ``rule_keywords`` may not be present in older configs
        self.rule_keywords = getattr(classification, "rule_keywords", {})

        client = llm_client or _DummyLLMClient()
        llm_module = LLMFiletypeModule(client, classification.llm_prompt)
        rule_module = RuleBasedFileTypeModule(
            self.keyword_rules, next_module=llm_module.name
        )

        self.pipeline = ClassificationPipeline()
        self.pipeline.add_module(rule_module)
        self.pipeline.add_module(llm_module, after=[rule_module.name])

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
