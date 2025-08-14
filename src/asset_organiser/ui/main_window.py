from __future__ import annotations

from typing import Dict

from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from ..config_service import ConfigService
from .library import LibraryView
from .settings import SettingsView
from .workspace import WorkspaceView


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(
        self,
        config: ConfigService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Asset Organiser")
        self._config = config

        central = QWidget()
        layout = QHBoxLayout(central)
        self.sidebar = QListWidget()
        self.stack = QStackedWidget()
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        # Views
        self.views: Dict[str, QWidget] = {
            "Workspace": WorkspaceView(),
            "Library": LibraryView(),
            "Settings": SettingsView(self._config),
        }
        for name, widget in self.views.items():
            item = QListWidgetItem(name)
            self.sidebar.addItem(item)
            self.stack.addWidget(widget)

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)
