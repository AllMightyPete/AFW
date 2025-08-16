from __future__ import annotations

from typing import Iterable

from ..config_models import AssetTypeDefinition
from ..config_service import ConfigService
from ..llm import LLMClient, NoOpLLMClient, create_llm_client
from .constants import AssignConstantsModule
from .llm_asset_type import LLMAssetTypeModule
from .llm_filetypes import LLMFiletypeModule
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
        assettype_defs = dict(
            config_service.library_config.ASSET_TYPE_DEFINITIONS
        )
        for atype, keywords in config_service.get_asset_type_keywords().items():
            if atype in assettype_defs:
                assettype_defs[atype].rule_keywords.extend(keywords)
            else:
                assettype_defs[atype] = AssetTypeDefinition(rule_keywords=keywords)
        self.keyword_rules = classification.keyword_rules

        if llm_client is None:
            profile = config_service.get_active_provider_profile()
            if profile:
                try:
                    llm_client = create_llm_client(profile)
                except Exception:
                    llm_client = NoOpLLMClient()
            else:
                llm_client = NoOpLLMClient()

        self.pipeline = ClassificationPipeline()
        const_module = AssignConstantsModule(self.keyword_rules)
        self.pipeline.add_module(const_module)

        prompts = config_service.get_classification_prompts()

        llm_module = LLMFiletypeModule(llm_client, prompts.get("filetype", ""))
        rule_module = RuleBasedFileTypeModule(
            filetype_defs, next_module=llm_module.name
        )
        self.pipeline.add_module(rule_module, after=[const_module.name])
        self.pipeline.add_module(llm_module, after=[rule_module.name])

        # Phase 2: asset grouping
        llm_type_module = LLMAssetTypeModule(llm_client, prompts.get("asset_type", ""))
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
        tagging_module = LLMTaggingModule(llm_client, prompts.get("tagging", ""))
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
