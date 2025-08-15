from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ClassificationState


class ClassificationModule(ABC):
    """Base class for all classification modules."""

    name: str

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__

    @abstractmethod
    def run(self, state: ClassificationState) -> ClassificationState:
        """Process and return modified classification state."""
        raise NotImplementedError
