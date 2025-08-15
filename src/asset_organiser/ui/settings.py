from __future__ import annotations

from typing import Dict

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..config_models import AssetTypeDefinition, FileTypeDefinition
from ..config_service import ConfigService


class GeneralSettingsEditor(QWidget):
    """Editor for general application settings."""

    def __init__(
        self,
        config: ConfigService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config

        self.output_dir = QLineEdit()
        self.metadata_name = QLineEdit()
        form = QFormLayout()
        form.addRow("Output Base Directory", self.output_dir)
        form.addRow("Metadata Filename", self.metadata_name)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.save_btn)

        self.load_settings()

    def load_settings(self) -> None:
        settings = self._config.settings
        self.output_dir.setText(settings.OUTPUT_BASE_DIR)
        self.metadata_name.setText(settings.METADATA_FILENAME)

    def save_settings(self) -> None:
        settings = self._config.settings
        settings.OUTPUT_BASE_DIR = self.output_dir.text()
        settings.METADATA_FILENAME = self.metadata_name.text()
        self._config.settings = settings
        self._config.save_settings()


class FileTypesEditor(QWidget):
    """Master-detail editor for file type definitions."""

    def __init__(
        self,
        config: ConfigService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self.file_types: Dict[str, FileTypeDefinition] = dict(
            getattr(self._config.library_config, "FILE_TYPE_DEFINITIONS", {})
        )

        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        self.list = QListWidget()
        left.addWidget(self.list)
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.remove_btn = QPushButton("Remove")
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.remove_btn)
        left.addLayout(btn_row)
        layout.addLayout(left)

        form = QFormLayout()
        self.alias = QLineEdit()
        self.color = QLineEdit()
        self.hotkey = QLineEdit()
        form.addRow("Alias", self.alias)
        form.addRow("UI Color", self.color)
        form.addRow("Hotkey", self.hotkey)
        self.save_btn = QPushButton("Save")
        form.addRow(self.save_btn)
        layout.addLayout(form)

        self.list.currentItemChanged.connect(self._load_current)
        self.add_btn.clicked.connect(self._add)
        self.remove_btn.clicked.connect(self._remove)
        self.save_btn.clicked.connect(self._save_current)

        for key in sorted(self.file_types.keys()):
            self.list.addItem(key)

    def _load_current(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        definition = self.file_types[item.text()]
        self.alias.setText(definition.alias)
        self.color.setText(definition.UI_color or "")
        self.hotkey.setText(definition.UI_keybind or "")

    def _save_current(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        key = item.text()
        definition = self.file_types[key]
        definition.alias = self.alias.text()
        definition.UI_color = self.color.text() or None
        definition.UI_keybind = self.hotkey.text() or None
        self._config.library_config.FILE_TYPE_DEFINITIONS[key] = definition
        self._config.save_library_config()

    def _add(self) -> None:
        text, ok = QInputDialog.getText(self, "New File Type", "ID")
        if ok and text:
            if text in self.file_types:
                QMessageBox.warning(self, "Exists", "ID already exists")
                return
            definition = FileTypeDefinition(alias="")
            self.file_types[text] = definition
            self.list.addItem(text)
            self.list.setCurrentRow(self.list.count() - 1)

    def _remove(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        key = item.text()
        del self.file_types[key]
        self._config.library_config.FILE_TYPE_DEFINITIONS.pop(key, None)
        row = self.list.row(item)
        self.list.takeItem(row)
        self._config.save_library_config()


class AssetTypesEditor(QWidget):
    """Editor for asset type definitions."""

    def __init__(
        self,
        config: ConfigService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self.asset_types: Dict[str, AssetTypeDefinition] = dict(
            getattr(self._config.library_config, "ASSET_TYPE_DEFINITIONS", {})
        )

        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        self.list = QListWidget()
        left.addWidget(self.list)
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.remove_btn = QPushButton("Remove")
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.remove_btn)
        left.addLayout(btn_row)
        layout.addLayout(left)

        form = QFormLayout()
        self.color = QLineEdit()
        form.addRow("Color", self.color)
        self.save_btn = QPushButton("Save")
        form.addRow(self.save_btn)
        layout.addLayout(form)

        self.list.currentItemChanged.connect(self._load_current)
        self.add_btn.clicked.connect(self._add)
        self.remove_btn.clicked.connect(self._remove)
        self.save_btn.clicked.connect(self._save_current)

        for key in sorted(self.asset_types.keys()):
            self.list.addItem(key)

    def _load_current(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        definition = self.asset_types[item.text()]
        self.color.setText(definition.color or "")

    def _save_current(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        key = item.text()
        definition = self.asset_types[key]
        definition.color = self.color.text() or None
        self._config.library_config.ASSET_TYPE_DEFINITIONS[key] = definition
        self._config.save_library_config()

    def _add(self) -> None:
        text, ok = QInputDialog.getText(self, "New Asset Type", "ID")
        if ok and text:
            if text in self.asset_types:
                QMessageBox.warning(self, "Exists", "ID already exists")
                return
            definition = AssetTypeDefinition()
            self.asset_types[text] = definition
            self.list.addItem(text)
            self.list.setCurrentRow(self.list.count() - 1)

    def _remove(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        key = item.text()
        del self.asset_types[key]
        self._config.library_config.ASSET_TYPE_DEFINITIONS.pop(key, None)
        row = self.list.row(item)
        self.list.takeItem(row)
        self._config.save_library_config()


class SettingsView(QWidget):
    """Settings view with category navigation."""

    def __init__(
        self,
        config: ConfigService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config

        layout = QHBoxLayout(self)
        self.categories = QListWidget()
        self.stack = QStackedWidget()
        layout.addWidget(self.categories)
        layout.addWidget(self.stack, 1)

        self.editors: Dict[str, QWidget] = {
            "General": GeneralSettingsEditor(self._config),
            "File Types": FileTypesEditor(self._config),
            "Asset Types": AssetTypesEditor(self._config),
        }

        for name, editor in self.editors.items():
            item = QListWidgetItem(name)
            self.categories.addItem(item)
            self.stack.addWidget(editor)

        self.categories.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.categories.setCurrentRow(0)
