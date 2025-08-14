from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PySide6.QtWidgets import (  # noqa: E501
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class WorkspaceView(QWidget):
    """Workspace view with drag-and-drop area and placeholder tree."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Drag files here"))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Source/Asset/File"])
        layout.addWidget(self.tree, 1)

    # Drag-and-drop events
    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        self.add_paths(paths)
        event.acceptProposedAction()

    # Helper for tests
    def add_paths(self, paths: Iterable[Path]) -> None:
        for path in paths:
            item = QTreeWidgetItem([path.name])
            self.tree.addTopLevelItem(item)
