from asset_organiser.classification import ClassificationState
from asset_organiser.classification.service import ClassificationService
from asset_organiser.config_models import (
    ClassificationSettings,
    FileTypeDefinition,
    LibraryConfig,
)
from asset_organiser.config_service import ConfigService


def _make_service() -> ClassificationService:
    cfg_service = ConfigService()
    cfg_service.library_config = LibraryConfig(
        FILE_TYPE_DEFINITIONS={
            "MAP_COL": FileTypeDefinition(alias="COL", rule_keywords=["_col"])
        },
        CLASSIFICATION=ClassificationSettings(
            keyword_rules={"readme": "IGNORE"},
        ),
    )
    return ClassificationService(cfg_service)


def test_service_builds_pipeline_and_classifies() -> None:
    service = _make_service()
    state = ClassificationService.from_file_list(
        ["wood_col.png", "readme.txt", "other.txt"]
    )
    result = service.classify(state)
    contents = result.sources["src"].contents
    assert contents["0"].filetype == "MAP_COL"
    assert contents["1"].filetype == "IGNORE"
    assert contents["2"].filetype is None
    assert "LLMModule" in service.pipeline._modules


def test_from_file_list_json_roundtrip() -> None:
    state = ClassificationService.from_file_list(["a.txt"])
    text = state.to_json()
    loaded = ClassificationState.from_json(text)
    assert loaded.sources["src"].contents["0"].filename == "a.txt"
