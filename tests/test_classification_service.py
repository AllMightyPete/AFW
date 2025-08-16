from asset_organiser.classification import ClassificationState
from asset_organiser.classification.service import ClassificationService
from asset_organiser.config_models import (
    AssetTypeDefinition,
    ClassificationSettings,
    FileTypeDefinition,
    LibraryConfig,
)
from asset_organiser.config_service import ConfigService
from asset_organiser.llm.client import NoOpLLMClient


class MockLLMClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if "filetype" in prompt and "other.unknown" in prompt:
            return "MAP_NRM"
        if "asset_type" in prompt and "Asset name: wood" in prompt:
            return "TEXTURE"
        if "tagging" in prompt and "Asset name: wood" in prompt:
            return "wood"
        if "tagging" in prompt and "Asset name: mesh" in prompt:
            return "mesh"
        return ""


def _make_service(
    llm_client: MockLLMClient | None = None,
) -> ClassificationService:
    cfg_service = ConfigService()
    cfg_service.library_config = LibraryConfig(
        FILE_TYPE_DEFINITIONS={
            "MAP_COL": FileTypeDefinition(alias="COL", rule_keywords=["_col"])
        },
        CLASSIFICATION=ClassificationSettings(
            keyword_rules={"readme": "IGNORE"},
            prompts={
                "filetype": "filetype",
                "asset_type": "asset_type",
                "tagging": "tagging",
            },
        ),
    )
    return ClassificationService(cfg_service, llm_client=llm_client)


def test_service_builds_pipeline_and_classifies() -> None:
    llm = MockLLMClient()
    service = _make_service(llm)
    state = ClassificationService.from_file_list(
        ["wood_col.png", "readme.txt", "other.unknown"]
    )
    result = service.classify(state)
    contents = result.sources["src"].contents
    assert contents["0"].filetype == "MAP_COL"
    assert contents["1"].filetype == "IGNORE"
    assert contents["2"].filetype == "MAP_NRM"
    assert "LLMFiletypeModule" in service.pipeline._modules
    assert any("filetype" in p for p in llm.prompts)


def test_llm_skipped_when_all_classified() -> None:
    llm = MockLLMClient()
    service = _make_service(llm)
    state = ClassificationService.from_file_list(
        [
            "wood_col.png",
            "readme.txt",
        ]
    )
    service.classify(state)
    assert not any("filetype" in p for p in llm.prompts)


def test_from_file_list_json_roundtrip() -> None:
    state = ClassificationService.from_file_list(["a.txt"])
    text = state.to_json()
    loaded = ClassificationState.from_json(text)
    assert loaded.sources["src"].contents["0"].filename == "a.txt"


def test_service_separates_and_groups_assets() -> None:
    cfg_service = ConfigService()
    cfg_service.library_config = LibraryConfig(
        FILE_TYPE_DEFINITIONS={
            "FILE_MODEL": FileTypeDefinition(
                alias="MODEL", rule_keywords=["_mdl"], is_standalone=True
            ),
            "MAP_COL": FileTypeDefinition(alias="COL", rule_keywords=["_col"]),
            "MAP_NRM": FileTypeDefinition(alias="NRM", rule_keywords=["_nrm"]),
        },
        CLASSIFICATION=ClassificationSettings(keyword_rules={}),
    )
    service = ClassificationService(cfg_service, llm_client=NoOpLLMClient())
    state = ClassificationService.from_file_list(
        ["mesh_mdl.fbx", "mesh_col.png", "mesh_nrm.png"]
    )
    result = service.classify(state)
    assets = result.sources["src"].assets
    assert len(assets) == 2
    assert any(asset.asset_contents == ["0"] for asset in assets.values())
    contents_sets = [set(a.asset_contents) for a in assets.values()]
    assert {"1", "2"} in contents_sets


def test_service_names_and_types_assets() -> None:
    cfg_service = ConfigService()
    cfg_service.library_config = LibraryConfig(
        FILE_TYPE_DEFINITIONS={
            "FILE_MODEL": FileTypeDefinition(
                alias="MODEL", rule_keywords=["_mdl"], is_standalone=True
            ),
            "MAP_COL": FileTypeDefinition(alias="COL", rule_keywords=["_col"]),
            "MAP_NRM": FileTypeDefinition(alias="NRM", rule_keywords=["_nrm"]),
        },
        ASSET_TYPE_DEFINITIONS={
            "MODEL": AssetTypeDefinition(rule_keywords=["mesh"]),
        },
        CLASSIFICATION=ClassificationSettings(
            keyword_rules={},
            prompts={
                "filetype": "filetype",
                "asset_type": "asset_type",
                "tagging": "tagging",
            },
        ),
    )
    llm = MockLLMClient()
    service = ClassificationService(cfg_service, llm_client=llm)
    state = ClassificationService.from_file_list(
        ["mesh_mdl.fbx", "wood_col.png", "wood_nrm.png"]
    )
    result = service.classify(state)
    assets = result.sources["src"].assets
    names = {a.asset_name for a in assets.values()}
    types = {a.asset_type for a in assets.values()}
    assert names == {"mesh", "wood"}
    assert types == {"MODEL", "TEXTURE"}
    tags = {a.asset_name: a.asset_tags for a in assets.values()}
    assert tags["mesh"] == ["mesh"]
    assert tags["wood"] == ["wood"]
    assert any("asset_type" in p for p in llm.prompts)
