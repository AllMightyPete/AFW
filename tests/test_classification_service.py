from asset_organiser.classification import ClassificationState
from asset_organiser.classification.service import ClassificationService
from asset_organiser.config_models import (
    ClassificationSettings,
    FileTypeDefinition,
    LibraryConfig,
)
from asset_organiser.config_service import ConfigService


class CountingLLMClient:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return ""


def _make_service(
    llm_client: CountingLLMClient | None = None,
) -> ClassificationService:
    cfg_service = ConfigService()
    cfg_service.library_config = LibraryConfig(
        FILE_TYPE_DEFINITIONS={
            "MAP_COL": FileTypeDefinition(alias="COL", rule_keywords=["_col"])
        },
        CLASSIFICATION=ClassificationSettings(
            keyword_rules={"readme": "IGNORE"},
        ),
    )
    return ClassificationService(cfg_service, llm_client=llm_client)


def test_service_builds_pipeline_and_classifies() -> None:
    llm = CountingLLMClient()
    service = _make_service(llm)
    state = ClassificationService.from_file_list(
        ["wood_col.png", "readme.txt", "other.txt"]
    )
    result = service.classify(state)
    contents = result.sources["src"].contents
    assert contents["0"].filetype == "MAP_COL"
    assert contents["1"].filetype == "IGNORE"
    assert contents["2"].filetype is None
    assert "LLMFiletypeModule" in service.pipeline._modules
    assert llm.calls == 1


def test_llm_skipped_when_all_classified() -> None:
    llm = CountingLLMClient()
    service = _make_service(llm)
    state = ClassificationService.from_file_list(
        [
            "wood_col.png",
            "readme.txt",
        ]
    )
    service.classify(state)
    assert llm.calls == 0


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
    service = ClassificationService(cfg_service)
    state = ClassificationService.from_file_list(
        ["mesh_mdl.fbx", "mesh_col.png", "mesh_nrm.png"]
    )
    result = service.classify(state)
    assets = result.sources["src"].assets
    assert len(assets) == 2
    assert any(asset.asset_contents == ["0"] for asset in assets.values())
    contents_sets = [set(a.asset_contents) for a in assets.values()]
    assert {"1", "2"} in contents_sets
