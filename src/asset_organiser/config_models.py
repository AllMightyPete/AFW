from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GeneralSettings(BaseModel):
    """Application-wide settings stored in ``config/settings.json``."""

    OUTPUT_BASE_DIR: str = "../Asset_Library"
    OUTPUT_DIRECTORY_PATTERN: str = "[supplier]/[assettype]/[assetname]"
    OUTPUT_FILENAME_PATTERN: str = "[assetname]_[filetype]_[resolution]"
    METADATA_FILENAME: str = "metadata.json"
    RESOLUTION_THRESHOLD_FOR_LOSSY: int = 4096
    IMAGE_RESOLUTIONS: Dict[str, int] = Field(default_factory=dict)
    DEFAULT_EXPORT_PROFILES: Dict[str, str] = Field(default_factory=dict)
    CALCULATE_STATS_RESOLUTION: Optional[str] = None
    DEFAULT_ASSET_TYPE: Optional[str] = None
    MERGE_DIMENSION_MISMATCH_STRATEGY: Optional[str] = None


class FileTypeDefinition(BaseModel):
    alias: str
    bit_depth_policy: Optional[str] = "preserve"
    is_grayscale: bool = False
    is_standalone: bool = False
    rule_keywords: List[str] = Field(default_factory=list)
    UI_color: Optional[str] = Field(None, alias="UI-color")
    UI_keybind: Optional[str] = Field(None, alias="UI-keybind")
    LLM_description: Optional[str] = Field(None, alias="LLM-description")
    LLM_examples: List[str] = Field(default_factory=list, alias="LLM-examples")
    override_export_profiles: Dict[str, str] = Field(
        default_factory=dict, alias="OVERRIDE_EXPORT_PROFILES"
    )

    model_config = ConfigDict(populate_by_name=True)


class AssetTypeDefinition(BaseModel):
    color: Optional[str] = None
    rule_keywords: List[str] = Field(default_factory=list)
    LLM_description: Optional[str] = Field(None, alias="LLM-description")
    LLM_examples: List[str] = Field(default_factory=list, alias="LLM-examples")

    model_config = ConfigDict(populate_by_name=True)


class SupplierDefinition(BaseModel):
    default_normal_format: Optional[str] = None


class LLMProviderProfile(BaseModel):
    profile_name: str = Field(alias="Profile Name")
    provider: str = Field(alias="Provider")
    api_key: str = Field("", alias="API Key")
    base_url: str = Field("", alias="Provider-Accesspoint")
    model: str = Field("", alias="Model")
    reasoning_effort: str = Field("Low", alias="Reasoning Effort")

    model_config = ConfigDict(populate_by_name=True)


def _default_provider_profiles() -> List[LLMProviderProfile]:
    return [
        LLMProviderProfile(
            profile_name="mistral small",
            provider="Ollama",
            api_key="",
            base_url="https://api.llm.gestaltservers.com",
            model="deepseek-r1:1.5b",
            reasoning_effort="Low",
        )
    ]


class ClassificationSettings(BaseModel):
    provider: Optional[str] = Field("Ollama", alias="LLM Provider")
    prompt: str = Field("", alias="LLM Prompt")
    providers: List[LLMProviderProfile] = Field(
        default_factory=_default_provider_profiles,
        alias="Providers",
    )
    keyword_rules: Dict[str, str] = Field(
        default_factory=dict,
        alias="Keyword Rules",
    )

    model_config = ConfigDict(populate_by_name=True)


class ChannelInput(BaseModel):
    file_type: str
    channel: str


class ChannelPackingRule(BaseModel):
    output_file_type: str
    inputs: Dict[str, ChannelInput]
    defaults: Dict[str, int] = Field(default_factory=dict)
    output_bit_depth: str


class ExportProfile(BaseModel):
    module: str
    settings: Dict[str, object] = Field(default_factory=dict)


class ProcessingSettings(BaseModel):
    channel_packing: List[ChannelPackingRule] = Field(
        default_factory=list, alias="MAP_MERGE_RULES"
    )
    export_profiles: Dict[str, ExportProfile] = Field(
        default_factory=dict, alias="FILE_EXPORT_PROFILES"
    )
    image_resolutions: Dict[str, int] = Field(
        default_factory=dict, alias="IMAGE_RESOLUTIONS"
    )

    model_config = ConfigDict(populate_by_name=True)


class IndexingSettings(BaseModel):
    enable_semantic_search: bool = Field(
        False,
        alias="Enable Semantic Search",
    )
    embedding_model: Optional[str] = Field(
        None,
        alias="Embedding Model",
    )
    rendering_engine: Optional[str] = Field(
        None,
        alias="Rendering Engine",
    )

    model_config = ConfigDict(populate_by_name=True)


class LibraryConfig(BaseModel):
    FILE_TYPE_DEFINITIONS: Dict[str, FileTypeDefinition] = Field(
        default_factory=dict,
    )
    ASSET_TYPE_DEFINITIONS: Dict[str, AssetTypeDefinition] = Field(
        default_factory=dict,
    )
    SUPPLIERS: Dict[str, SupplierDefinition] = Field(default_factory=dict)
    CLASSIFICATION: ClassificationSettings = Field(
        default_factory=ClassificationSettings,
    )
    PROCESSING: ProcessingSettings = Field(
        default_factory=ProcessingSettings,
    )
    INDEXING: IndexingSettings = Field(default_factory=IndexingSettings)
