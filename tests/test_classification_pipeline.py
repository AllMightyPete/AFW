import json
from typing import List

import asset_organiser.config_models as cm
from asset_organiser.classification import (
    AssignConstantsModule,
    ClassificationModule,
    ClassificationPipeline,
    ClassificationState,
    LLMGroupFilesModule,
    RuleBasedFileTypeModule,
    SeparateStandaloneModule,
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
    filetype_defs = {
        "MAP_COL": cm.FileTypeDefinition(alias="COL", rule_keywords=["_col"]),
        "MAP_NRM": cm.FileTypeDefinition(alias="NRM", rule_keywords=["_nrm"]),
    }
    module = RuleBasedFileTypeModule(filetype_defs)
    pipeline = ClassificationPipeline()
    pipeline.add_module(module)
    result = pipeline.run(state)
    contents = result.sources["src"].contents
    assert contents["1"].filetype == "MAP_COL"
    assert contents["2"].filetype == "MAP_NRM"


def test_assign_constants_module_assigns_types() -> None:
    data = {
        "sources": {
            "src": {
                "metadata": {},
                "contents": {
                    "1": {"filename": "model.fbx"},
                    "2": {"filename": "readme.txt"},
                },
            }
        }
    }
    state = ClassificationState.model_validate(data)
    module = AssignConstantsModule({".fbx": "FILE_MODEL", "readme": "IGNORE"})
    pipeline = ClassificationPipeline()
    pipeline.add_module(module)
    result = pipeline.run(state)
    contents = result.sources["src"].contents
    assert contents["1"].filetype == "FILE_MODEL"
    assert contents["2"].filetype == "IGNORE"


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


class RouterModule(ClassificationModule):
    def __init__(self, log: List[str]) -> None:
        super().__init__("Router")
        self.log = log

    def run(self, state: ClassificationState):
        self.log.append(self.name)
        next_mods: List[str] = []
        for source in state.sources.values():
            for entry in source.contents.values():
                if entry.filename.endswith(".id"):
                    entry.filetype = "ID"
        has_identified = any(
            entry.filetype is not None
            for source in state.sources.values()
            for entry in source.contents.values()
        )
        has_unidentified = any(
            entry.filetype is None
            for source in state.sources.values()
            for entry in source.contents.values()
        )
        if has_identified:
            next_mods.append("Identified")
        if has_unidentified:
            next_mods.append("Unidentified")
        return state, next_mods


class BranchModule(ClassificationModule):
    def __init__(self, name: str, log: List[str]) -> None:
        super().__init__(name)
        self.log = log

    def run(self, state: ClassificationState):
        self.log.append(self.name)
        return state


def test_pipeline_routes_to_selected_modules() -> None:
    data = {
        "sources": {
            "src": {
                "metadata": {},
                "contents": {
                    "1": {"filename": "file.id"},
                    "2": {"filename": "other"},
                },
            }
        }
    }
    state = ClassificationState.model_validate(data)
    log: List[str] = []
    pipeline = ClassificationPipeline()
    pipeline.add_module(RouterModule(log))
    pipeline.add_module(BranchModule("Identified", log), after=["Router"])
    pipeline.add_module(BranchModule("Unidentified", log), after=["Router"])
    pipeline.run(state)
    assert log[0] == "Router"
    assert set(log[1:]) == {"Identified", "Unidentified"}
    contents = state.sources["src"].contents
    assert contents["1"].filetype == "ID"
    assert contents["2"].filetype is None


def test_pipeline_skips_unrouted_modules() -> None:
    data = {
        "sources": {
            "src": {
                "metadata": {},
                "contents": {"1": {"filename": "file.id"}},
            }
        }
    }
    state = ClassificationState.model_validate(data)
    log: List[str] = []
    pipeline = ClassificationPipeline()
    pipeline.add_module(RouterModule(log))
    pipeline.add_module(BranchModule("Identified", log), after=["Router"])
    pipeline.add_module(BranchModule("Unidentified", log), after=["Router"])
    pipeline.run(state)
    assert log == ["Router", "Identified"]


def test_separate_standalone_module_creates_assets() -> None:
    data = {
        "sources": {
            "src": {
                "metadata": {},
                "contents": {
                    "1": {"filename": "model.fbx", "filetype": "FILE_MODEL"},
                    "2": {"filename": "wood_col.png", "filetype": "MAP_COL"},
                },
            }
        }
    }
    state = ClassificationState.model_validate(data)
    filetype_defs = {
        "FILE_MODEL": cm.FileTypeDefinition(alias="MODEL", is_standalone=True),
        "MAP_COL": cm.FileTypeDefinition(alias="COL"),
    }
    module = SeparateStandaloneModule(filetype_defs)
    pipeline = ClassificationPipeline()
    pipeline.add_module(module)
    pipeline.run(state)
    assets = state.sources["src"].assets
    assert len(assets) == 1
    asset = next(iter(assets.values()))
    assert asset.asset_contents == ["1"]


def test_llm_group_files_module_groups_unassigned_files() -> None:
    data = {
        "sources": {
            "src": {
                "metadata": {},
                "contents": {
                    "1": {"filename": "wood_col.png"},
                    "2": {"filename": "wood_nrm.png"},
                    "3": {"filename": "rock_col.png"},
                    "4": {"filename": "rock_nrm.png"},
                },
                "assets": {"0": {"asset_contents": ["1", "2"]}},
            }
        }
    }
    state = ClassificationState.model_validate(data)
    module = LLMGroupFilesModule()
    pipeline = ClassificationPipeline()
    pipeline.add_module(module)
    pipeline.run(state)
    assets = state.sources["src"].assets
    assert any(set(a.asset_contents) == {"3", "4"} for a in assets.values())
    # ensure existing asset unchanged
    assert set(assets["0"].asset_contents) == {"1", "2"}
