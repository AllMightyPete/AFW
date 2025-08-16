from __future__ import annotations

from typing import Iterable

from ..config_service import ConfigService
from .constants import AssignConstantsModule
from .llm_asset_type import LLMAssetTypeModule
from .llm_filetypes import LLMClient, LLMFiletypeModule, NoOpLLMClient
from .llm_grouping import LLMGroupFilesModule
from .llm_naming import LLMAssetNameModule
from .llm_tagging import LLMTaggingModule
from .models import ClassificationState
from .output import OutputModule
from .pipeline import ClassificationPipeline
from .rule_based import KeywordAssetTypeModule, RuleBasedFileTypeModule
from .standalone import AssignStandaloneNameModule, SeparateStandaloneModule


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
        assettype_defs = config_service.library_config.ASSET_TYPE_DEFINITIONS
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
        llm_type_module = LLMAssetTypeModule(llm_client, classification.prompt)
        keyword_type_module = KeywordAssetTypeModule(
            assettype_defs, next_module=llm_type_module.name
        )
        assign_name_module = AssignStandaloneNameModule(
            next_module=keyword_type_module.name
        )
        group_module = LLMGroupFilesModule(llm_client)
        llm_name_module = LLMAssetNameModule(llm_client)
        separate_module = SeparateStandaloneModule(
            filetype_defs,
            standalone_next=assign_name_module.name,
            grouping_next=group_module.name,
        )
        self.pipeline.add_module(separate_module, after=[llm_module.name])
        after_sep = [separate_module.name]
        self.pipeline.add_module(assign_name_module, after=after_sep)
        self.pipeline.add_module(group_module, after=after_sep)
        self.pipeline.add_module(llm_name_module, after=[group_module.name])
        self.pipeline.add_module(
            keyword_type_module,
            after=[llm_name_module.name],
        )
        self.pipeline.add_module(
            llm_type_module,
            after=[keyword_type_module.name],
        )
        tagging_module = LLMTaggingModule(llm_client, classification.prompt)
        self.pipeline.add_module(tagging_module, after=[llm_type_module.name])
        output_module = OutputModule()
        self.pipeline.add_module(output_module, after=[tagging_module.name])

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
