import json
from typing import List

from asset_organiser.classification import (
    ClassificationModule,
    ClassificationPipeline,
    ClassificationState,
    RuleBasedFileTypeModule,
)


class DummyModule(ClassificationModule):
    def __init__(self, label: str, log: List[str]) -> None:
        super().__init__(label)
        self.log = log

    def run(self, state: ClassificationState) -> ClassificationState:
        self.log.append(self.name)
        return state


def test_pipeline_runs_modules_in_order() -> None:
    log: List[str] = []
    pipeline = ClassificationPipeline()
    pipeline.add_module(DummyModule("A", log))
    pipeline.add_module(DummyModule("B", log), after=["A"])
    pipeline.add_module(DummyModule("C", log), after=["A"])
    pipeline.run(ClassificationState())
    assert log[0] == "A"
    assert set(log) == {"A", "B", "C"}


def test_rule_based_filetype_module_assigns_types() -> None:
    data = {
        "sources": {
            "src": {
                "metadata": {},
                "contents": {
                    "1": {"filename": "wood_col.png"},
                    "2": {"filename": "wood_nrm.png"},
                },
            }
        }
    }
    state = ClassificationState.model_validate(data)
    module = RuleBasedFileTypeModule({"_col": "MAP_COL", "_nrm": "MAP_NRM"})
    pipeline = ClassificationPipeline()
    pipeline.add_module(module)
    result = pipeline.run(state)
    contents = result.sources["src"].contents
    assert contents["1"].filetype == "MAP_COL"
    assert contents["2"].filetype == "MAP_NRM"


def test_json_roundtrip() -> None:
    text = json.dumps(
        {
            "sources": {
                "s": {
                    "metadata": {},
                    "contents": {
                        "1": {
                            "filename": "a.txt",
                            "filetype": "IGNORE",
                        }
                    },
                }
            }
        }
    )
    state = ClassificationState.from_json(text)
    dumped = state.to_json()
    loaded = json.loads(dumped)
    assert loaded["sources"]["s"]["contents"]["1"]["filetype"] == "IGNORE"
