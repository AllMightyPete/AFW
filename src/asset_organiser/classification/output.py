from __future__ import annotations

"""Terminal output module for classification pipelines."""

from .models import ClassificationState
from .module import ClassificationModule


class OutputModule(ClassificationModule):
    """Final pipeline stage that simply returns the state."""

    def run(self, state: ClassificationState) -> ClassificationState:
        return state
