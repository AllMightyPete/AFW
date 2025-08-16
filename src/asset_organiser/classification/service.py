from __future__ import annotations

from typing import Iterable

from ..config_service import ConfigService
from .constants import AssignConstantsModule
from .llm_filetypes import LLMClient, LLMFiletypeModule, NoOpLLMClient
from .llm_grouping import LLMGroupFilesModule
from .models import ClassificationState
from .pipeline import ClassificationPipeline
from .rule_based import RuleBasedFileTypeModule
from .standalone import SeparateStandaloneModule


class ClassificationService:
    """High level service for executing classification pipelines."""

    def __init__(
        self,
        config_service: ConfigService,
        llm_client: LLMClient | None = None,
    ) -> None:
        if config_service.library_config is None:
            raise RuntimeError("Library configuration not loaded")
        classification = config_service.library_config.CLASSIFICATION
        filetype_defs = config_service.library_config.FILE_TYPE_DEFINITIONS
        self.keyword_rules = classification.keyword_rules

        if llm_client is None:
            llm_client = NoOpLLMClient()

        self.pipeline = ClassificationPipeline()
        const_module = AssignConstantsModule(self.keyword_rules)
        self.pipeline.add_module(const_module)

        llm_module = LLMFiletypeModule(llm_client, classification.prompt)
        rule_module = RuleBasedFileTypeModule(
            filetype_defs, next_module=llm_module.name
        )
        self.pipeline.add_module(rule_module, after=[const_module.name])
        self.pipeline.add_module(llm_module, after=[rule_module.name])

        # Phase 2: asset grouping
        group_module = LLMGroupFilesModule(llm_client)
        separate_module = SeparateStandaloneModule(
            filetype_defs, grouping_next=group_module.name
        )
        self.pipeline.add_module(separate_module, after=[llm_module.name])
        self.pipeline.add_module(group_module, after=[separate_module.name])

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
