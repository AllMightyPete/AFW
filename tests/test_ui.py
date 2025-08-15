import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import asset_organiser.config_models as cm
from asset_organiser import ConfigService
from asset_organiser.ui import MainWindow, WorkspaceView

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_main_window_loads_and_saves_settings(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])

    cfg_path = tmp_path / "settings.json"
    service = ConfigService(app_config_path=cfg_path)
    service.set_library_path(tmp_path)
    window = MainWindow(service)

    # Sidebar has expected tabs
    count = window.sidebar.count()
    items = [window.sidebar.item(i).text() for i in range(count)]
    assert items == ["Workspace", "Library", "Settings"]

    # Switch to settings view and modify value
    window.sidebar.setCurrentRow(2)
    settings_view = window.views["Settings"]
    general = settings_view.editors["General"]
    general.output_dir.setText("/tmp")
    QTest.mouseClick(general.save_btn, Qt.LeftButton)

    assert service.settings.OUTPUT_BASE_DIR == "/tmp"

    window.close()
    app.quit()


def test_workspace_adds_items_and_hotkey(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    service = ConfigService(app_config_path=tmp_path / "settings.json")
    service.set_library_path(tmp_path)
    service.library_config.FILE_TYPE_DEFINITIONS = {
        "MAP_COL": cm.FileTypeDefinition(alias="COL", UI_keybind="C"),
    }
    service.library_config.ASSET_TYPE_DEFINITIONS = {
        "Surface": cm.AssetTypeDefinition(),
    }
    service.save_library_config()

    view = WorkspaceView(service)
    file_path = tmp_path / "file.txt"
    file_path.write_text("x")
    view.add_paths([file_path])
    assert view.tree.topLevelItemCount() == 1
    asset_item = view.tree.topLevelItem(0).child(0)
    file_item = asset_item.child(0)
    view.tree.setCurrentItem(file_item)
    QTest.keyClick(view, Qt.Key_C)
    assert file_item.text(1) == "MAP_COL"
    view.deleteLater()
    app.quit()
