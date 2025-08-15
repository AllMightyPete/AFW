from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List

from .models import ClassificationState
from .module import ClassificationModule


class ClassificationPipeline:
    """Execute classification modules arranged in a DAG."""

    def __init__(self) -> None:
        self._modules: Dict[str, ClassificationModule] = {}
        self._graph: Dict[str, List[str]] = defaultdict(list)
        self._reverse: Dict[str, List[str]] = defaultdict(list)

    def add_module(
        self,
        module: ClassificationModule,
        *,
        after: Iterable[str] | None = None,
    ) -> None:
        name = module.name
        if name in self._modules:
            raise ValueError(f"Module {name!r} already exists")
        self._modules[name] = module
        if after:
            for parent in after:
                self._graph[parent].append(name)
                self._reverse[name].append(parent)
        else:
            self._graph.setdefault(name, [])
            self._reverse.setdefault(name, [])

    def run(self, state: ClassificationState) -> ClassificationState:
        indegree: Dict[str, int] = {}
        for name in self._modules:
            indegree[name] = len(self._reverse.get(name, []))
        queue = deque([n for n, d in indegree.items() if d == 0])
        executed = []
        while queue:
            name = queue.popleft()
            module = self._modules[name]
            state = module.run(state)
            executed.append(name)
            for child in self._graph.get(name, []):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if len(executed) != len(self._modules):
            missing = set(self._modules) - set(executed)
            raise RuntimeError(f"Pipeline did not execute modules: {missing}")
        return state
