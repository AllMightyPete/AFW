from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple

from .models import ClassificationState


class ClassificationModule(ABC):
    """Base class for all classification modules."""

    name: str

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__

    @abstractmethod
    def run(
        self, state: ClassificationState
    ) -> ClassificationState | Tuple[ClassificationState, List[str]]:
        """Process and return modified classification state.

        Modules may optionally return a tuple of ``(state, [next_module_names])``
        to explicitly route execution to downstream modules.  If only the state
        is returned, the pipeline will follow the predefined DAG edges.
        """
        raise NotImplementedError
