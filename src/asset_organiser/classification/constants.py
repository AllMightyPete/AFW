from __future__ import annotations

from typing import Dict

from .models import ClassificationState
from .module import ClassificationModule

# Default mapping of file extensions or substrings to file types.  This can be
# overridden by providing a custom mapping when instantiating the module.
DEFAULT_CONSTANTS: Dict[str, str] = {
    ".fbx": "FILE_MODEL",
    ".obj": "FILE_MODEL",
    ".sbsar": "FILE_SBSAR",
}


class AssignConstantsModule(ClassificationModule):
    """Assign file types based on constant filename patterns or extensions."""

    def __init__(self, constants: Dict[str, str] | None = None) -> None:
        super().__init__()
        constants = constants or DEFAULT_CONSTANTS
        # Normalise patterns for case-insensitive comparison
        self.constants = {k.lower(): v for k, v in constants.items()}

    def run(self, state: ClassificationState) -> ClassificationState:
        for source in state.sources.values():
            for entry in source.contents.values():
                if entry.filetype:
                    continue
                name = entry.filename.lower()
                for pattern, filetype in self.constants.items():
                    if name.endswith(pattern) or pattern in name:
                        entry.filetype = filetype
                        break
        return state
