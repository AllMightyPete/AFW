import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from asset_organiser import ConfigService
from asset_organiser.config_models import GeneralSettings


def test_loads_and_saves_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.json"
    service = ConfigService(app_config_path=config_path)
    assert service.settings == GeneralSettings()

    service.settings.OUTPUT_BASE_DIR = "/tmp"
    service.save_settings()
    data = json.loads(config_path.read_text())
    assert data["OUTPUT_BASE_DIR"] == "/tmp"


def test_load_library_config_valid(tmp_path: Path) -> None:
    lib_root = tmp_path / "lib"
    cfg_dir = lib_root / ".asset-library"
    cfg_dir.mkdir(parents=True)
    data = {"MAP_COL": {"alias": "COL"}}
    (cfg_dir / "file-types.json").write_text(json.dumps(data))

    service = ConfigService(app_config_path=tmp_path / "settings.json")
    service.set_library_path(lib_root)
    assert "MAP_COL" in service.library_config.FILE_TYPE_DEFINITIONS


def test_load_library_config_invalid(tmp_path: Path) -> None:
    lib_root = tmp_path / "lib"
    cfg_dir = lib_root / ".asset-library"
    cfg_dir.mkdir(parents=True)
    data = {"MAP_COL": {"alias": 5}}
    (cfg_dir / "file-types.json").write_text(json.dumps(data))

    service = ConfigService(app_config_path=tmp_path / "settings.json")
    with pytest.raises(ValidationError):
        service.set_library_path(lib_root)
