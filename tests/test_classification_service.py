from asset_organiser.classification import ClassificationState
from asset_organiser.classification.service import ClassificationService
from asset_organiser.config_models import ClassificationSettings, LibraryConfig
from asset_organiser.config_service import ConfigService


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def classify_filetype(self, filename: str, prompt: str | None = None) -> str | None:
        self.calls.append(filename)
        return "MAP_LLM"


def _make_service(client: DummyClient) -> ClassificationService:
    cfg_service = ConfigService()
    cfg_service.library_config = LibraryConfig(
        CLASSIFICATION=ClassificationSettings(
            keyword_rules={"_col": "MAP_COL"},
            rule_keywords={"dummy": ["keyword"]},
        )
    )
    return ClassificationService(cfg_service, llm_client=client)


def test_service_builds_pipeline_and_classifies() -> None:
    client = DummyClient()
    service = _make_service(client)
    state = ClassificationService.from_file_list(["wood_col.png", "other.txt"])
    result = service.classify(state)
    contents = result.sources["src"].contents
    assert contents["0"].filetype == "MAP_COL"
    assert contents["1"].filetype == "MAP_LLM"
    assert "LLMFiletypeModule" in service.pipeline._modules
    assert client.calls == ["other.txt"]


def test_from_file_list_json_roundtrip() -> None:
    state = ClassificationService.from_file_list(["a.txt"])
    text = state.to_json()
    loaded = ClassificationState.from_json(text)
    assert loaded.sources["src"].contents["0"].filename == "a.txt"


def test_llm_module_skipped_when_all_classified() -> None:
    client = DummyClient()
    service = _make_service(client)
    state = ClassificationService.from_file_list(["wood_col.png"])
    result = service.classify(state)
    contents = result.sources["src"].contents
    assert contents["0"].filetype == "MAP_COL"
    assert client.calls == []
