"""Classification service module framework."""

from .constants import AssignConstantsModule
from .llm_asset_type import LLMAssetTypeModule
from .llm_filetypes import LLMFiletypeModule
from .llm_grouping import LLMGroupFilesModule
from .llm_naming import LLMAssetNameModule
from .llm_tagging import LLMTaggingModule
from .models import ClassificationState
from .module import ClassificationModule
from .output import OutputModule
from .pipeline import ClassificationPipeline
from .rule_based import KeywordAssetTypeModule, RuleBasedFileTypeModule
from .service import ClassificationService
from .standalone import AssignStandaloneNameModule, SeparateStandaloneModule

__all__ = [
    "ClassificationState",
    "ClassificationModule",
    "ClassificationPipeline",
    "RuleBasedFileTypeModule",
    "LLMFiletypeModule",
    "AssignConstantsModule",
    "ClassificationService",
    "SeparateStandaloneModule",
    "LLMGroupFilesModule",
    "AssignStandaloneNameModule",
    "LLMAssetNameModule",
    "KeywordAssetTypeModule",
    "LLMAssetTypeModule",
    "LLMTaggingModule",
    "OutputModule",
]
