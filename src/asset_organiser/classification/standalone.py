from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..config_models import FileTypeDefinition
from .models import AssetEntry, ClassificationState
from .module import ClassificationModule


class SeparateStandaloneModule(ClassificationModule):
    """Move standalone files into individual asset entries.

    The module inspects each file's assigned ``filetype`` and consults the
    provided ``FileTypeDefinition`` mapping.  If a file type is marked with
    ``is_standalone=True`` it is considered a complete asset on its own.  The
    file is therefore placed into a newly created :class:`AssetEntry` with no
    other files.  Remaining files are left untouched for further grouping.

    The module can optionally route execution to downstream modules.  When
    ``standalone_next`` or ``grouping_next`` are supplied, the module will
    return ``(state, next_modules)`` directing the pipeline accordingly.  This
    mirrors the behaviour of :class:`RuleBasedFileTypeModule` and allows
    conditional execution of later stages in the pipeline.
    """

    def __init__(
        self,
        filetype_definitions: Dict[str, FileTypeDefinition],
        *,
        standalone_next: str | None = None,
        grouping_next: str | None = None,
    ) -> None:
        super().__init__()
        self.filetype_definitions = filetype_definitions
        self._standalone_next = standalone_next
        self._grouping_next = grouping_next

    # ------------------------------------------------------------------
    def _new_asset_id(self, source) -> str:
        existing = set(source.assets.keys())
        i = 0
        while str(i) in existing:
            i += 1
        return str(i)

    # ------------------------------------------------------------------
    def run(
        self, state: ClassificationState
    ) -> ClassificationState | tuple[ClassificationState, List[str]]:
        has_standalone = False
        has_grouping = False
        for source in state.sources.values():
            for file_id, entry in list(source.contents.items()):
                filetype = entry.filetype
                if not filetype:
                    has_grouping = True
                    continue
                definition = self.filetype_definitions.get(filetype)
                if definition and definition.is_standalone:
                    asset_id = self._new_asset_id(source)
                    source.assets[asset_id] = AssetEntry(
                        asset_contents=[file_id],
                    )
                    has_standalone = True
                else:
                    has_grouping = True
        next_modules: List[str] = []
        if has_standalone and self._standalone_next:
            next_modules.append(self._standalone_next)
        if has_grouping and self._grouping_next:
            next_modules.append(self._grouping_next)
        if next_modules:
            return state, next_modules
        return state


class AssignStandaloneNameModule(ClassificationModule):
    """Assign asset names for standalone assets based on filenames."""

    def __init__(self, *, next_module: str | None = None) -> None:
        super().__init__()
        self._next = next_module

    def run(
        self, state: ClassificationState
    ) -> ClassificationState | tuple[ClassificationState, List[str]]:
        has_unassigned = False
        for source in state.sources.values():
            assigned_files = set()
            for asset in source.assets.values():
                assigned_files.update(asset.asset_contents)
            unassigned = set(source.contents) - assigned_files
            if unassigned:
                has_unassigned = True
            for asset in source.assets.values():
                if asset.asset_name or len(asset.asset_contents) != 1:
                    continue
                file_id = asset.asset_contents[0]
                filename = source.contents[file_id].filename
                asset.asset_name = Path(filename).stem.split("_")[0]
        if not has_unassigned and self._next:
            return state, [self._next]
        return state
