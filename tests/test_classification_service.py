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


def _make_service(llm_client: CountingLLMClient | None = None) -> ClassificationService:
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
    state = ClassificationService.from_file_list(["wood_col.png", "readme.txt"])
    service.classify(state)
    assert llm.calls == 0


def test_from_file_list_json_roundtrip() -> None:
    state = ClassificationService.from_file_list(["a.txt"])
    text = state.to_json()
    loaded = ClassificationState.from_json(text)
    assert loaded.sources["src"].contents["0"].filename == "a.txt"
