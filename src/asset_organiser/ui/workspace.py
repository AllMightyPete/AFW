from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, Iterable, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..config_models import AssetTypeDefinition, FileTypeDefinition
from ..config_service import ConfigService


class WorkspaceView(QWidget):
    """Workspace view showing sources, assets and files."""

    def __init__(
        self,
        config: ConfigService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._config = config

        self.file_types: Dict[str, FileTypeDefinition] = dict(
            getattr(self._config.library_config, "FILE_TYPE_DEFINITIONS", {})
        )
        self.asset_types: Dict[str, AssetTypeDefinition] = dict(
            getattr(self._config.library_config, "ASSET_TYPE_DEFINITIONS", {})
        )
        # Ensure special types exist
        self.file_types.setdefault(
            "UNIDENTIFIED",
            FileTypeDefinition(alias="UNID"),
        )

        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("Add Source(s)")
        self.remove_btn = QPushButton("Remove Selected")
        self.classify_btn = QPushButton("Classify Selected")
        self.process_btn = QPushButton("Process All")
        for btn in [
            self.add_btn,
            self.remove_btn,
            self.classify_btn,
            self.process_btn,
        ]:
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type"])
        layout.addWidget(self.tree, 1)
        self.tree.installEventFilter(self)

        self._register_hotkeys()

        self.add_btn.clicked.connect(self._add_sources_dialog)
        self.remove_btn.clicked.connect(self.remove_selected)

    # ------------------------------------------------------------------
    def _register_hotkeys(self) -> None:
        self._shortcuts: List[QShortcut] = []
        for ft_id, definition in self.file_types.items():
            key = definition.UI_keybind
            if not key:
                continue
            sc = QShortcut(QKeySequence(key), self)
            sc.setContext(Qt.WidgetWithChildrenShortcut)
            sc.activated.connect(
                lambda ft_id=ft_id: self.assign_filetype_to_selection(ft_id)
            )
            self._shortcuts.append(sc)

    def eventFilter(self, obj, event):  # type: ignore[override]
        if obj is self.tree and event.type() == event.Type.KeyPress:
            for ft_id, definition in self.file_types.items():
                key = definition.UI_keybind
                if not key:
                    continue
                qt_key = getattr(Qt, f"Key_{key.upper()}", None)
                if qt_key is not None and event.key() == qt_key:
                    self.assign_filetype_to_selection(ft_id)
                    return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):  # type: ignore[override]
        for ft_id, definition in self.file_types.items():
            key = definition.UI_keybind
            if not key:
                continue
            qt_key = getattr(Qt, f"Key_{key.upper()}", None)
            if qt_key is not None and event.key() == qt_key:
                self.assign_filetype_to_selection(ft_id)
                return
        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Drag-and-drop events
    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        self.add_paths(paths)
        event.acceptProposedAction()

    # ------------------------------------------------------------------
    def _collect_files(self, path: Path) -> List[Path]:
        if path.is_dir():
            return [p for p in path.rglob("*") if p.is_file()]
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                return [Path(f) for f in zf.namelist() if not f.endswith("/")]
        return [path]

    def _group_files(self, files: Iterable[Path]) -> Dict[str, List[Path]]:
        assets: Dict[str, List[Path]] = {}
        for file in files:
            stem = file.stem
            asset_name = stem.split("_")[0] if "_" in stem else stem
            assets.setdefault(asset_name, []).append(file)
        return assets

    def _default_asset_type(self) -> str:
        return self._config.settings.DEFAULT_ASSET_TYPE or next(
            iter(self.asset_types.keys()), ""
        )

    # ------------------------------------------------------------------
    def add_paths(self, paths: Iterable[Path]) -> None:
        for path in paths:
            source_item = QTreeWidgetItem([path.name, ""])
            source_item.setData(0, Qt.UserRole, "source")
            self.tree.addTopLevelItem(source_item)
            files = self._collect_files(path)
            assets = self._group_files(files)
            for asset_name, asset_files in assets.items():
                asset_item = QTreeWidgetItem(
                    [f"Asset: {asset_name}", self._default_asset_type()]
                )
                asset_item.setData(0, Qt.UserRole, "asset")
                source_item.addChild(asset_item)
                combo = QComboBox()
                combo.addItems(sorted(self.asset_types.keys()))
                combo.setCurrentText(self._default_asset_type())
                combo.currentTextChanged.connect(
                    lambda text, item=asset_item: item.setText(1, text)
                )
                self.tree.setItemWidget(asset_item, 1, combo)
                for file_path in asset_files:
                    file_item = QTreeWidgetItem(
                        [file_path.name, "UNIDENTIFIED"],
                    )
                    file_item.setData(0, Qt.UserRole, "file")
                    asset_item.addChild(file_item)
                    combo_f = QComboBox()
                    combo_f.addItems(sorted(self.file_types.keys()))
                    combo_f.setCurrentText("UNIDENTIFIED")
                    combo_f.currentTextChanged.connect(
                        lambda text, item=file_item: self._set_file_type(
                            item,
                            text,
                        ),
                    )
                    self.tree.setItemWidget(file_item, 1, combo_f)

    # ------------------------------------------------------------------
    def _set_file_type(self, item: QTreeWidgetItem, file_type: str) -> None:
        item.setText(1, file_type)
        definition = self.file_types.get(file_type)
        if definition and definition.UI_color:
            color = QColor(definition.UI_color)
            item.setForeground(0, color)
            item.setForeground(1, color)

    def assign_filetype_to_selection(self, file_type: str) -> None:
        for item in self.tree.selectedItems():
            if item.data(0, Qt.UserRole) == "file":
                combo = self.tree.itemWidget(item, 1)
                if isinstance(combo, QComboBox):
                    combo.setCurrentText(file_type)
                else:
                    self._set_file_type(item, file_type)

    # ------------------------------------------------------------------
    def remove_selected(self) -> None:
        for item in self.tree.selectedItems():
            parent = item.parent()
            if parent is None:
                index = self.tree.indexOfTopLevelItem(item)
                self.tree.takeTopLevelItem(index)
            else:
                parent.removeChild(item)

    # ------------------------------------------------------------------
    def _add_sources_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Add Sources")
        if files:
            self.add_paths(Path(f) for f in files)
