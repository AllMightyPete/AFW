from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QListWidget, QTextEdit, QWidget


class LibraryView(QWidget):
    """Placeholder library view with grid and metadata panel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.grid = QListWidget()
        self.metadata = QTextEdit()
        self.metadata.setReadOnly(True)
        layout.addWidget(self.grid, 1)
        layout.addWidget(self.metadata)
