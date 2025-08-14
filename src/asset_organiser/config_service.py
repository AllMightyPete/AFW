from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .config_models import GeneralSettings, LibraryConfig

logger = logging.getLogger(__name__)


class ConfigService:
    """Service providing access to application and library configuration."""

    def __init__(self, app_config_path: Optional[Path] = None) -> None:
        if app_config_path is None:
            root_dir = Path(__file__).resolve().parents[2]
            app_config_path = root_dir / "config" / "settings.json"
        self.app_config_path = app_config_path
        self.settings = self._load_app_settings()
        self.library_path: Optional[Path] = None
        self.library_config: Optional[LibraryConfig] = None

    # ------------------------------------------------------------------
    def _load_app_settings(self) -> GeneralSettings:
        if not self.app_config_path.exists():
            logger.info(
                "Creating default settings at %s",
                self.app_config_path,
            )
            self.app_config_path.parent.mkdir(parents=True, exist_ok=True)
            settings = GeneralSettings()
            self.app_config_path.write_text(settings.model_dump_json(indent=2))
            return settings
        data = json.loads(self.app_config_path.read_text())
        return GeneralSettings.model_validate(data)

    # ------------------------------------------------------------------
    def save_settings(self) -> None:
        """Persist application settings to disk."""
        text = self.settings.model_dump_json(indent=2)
        self.app_config_path.write_text(text)

    # ------------------------------------------------------------------
    def set_library_path(self, library_root: Path) -> None:
        """Load configuration for the active asset library."""
        config_file = library_root / ".asset-library" / "config.json"
        if not config_file.exists():
            logger.info(
                "Creating default library config at %s",
                config_file,
            )
            config_file.parent.mkdir(parents=True, exist_ok=True)
            self.library_config = LibraryConfig()
            text = self.library_config.model_dump_json(indent=2)
            config_file.write_text(text)
        else:
            data = json.loads(config_file.read_text())
            self.library_config = LibraryConfig.model_validate(data)
        self.library_path = library_root

    # ------------------------------------------------------------------
    def save_library_config(self) -> None:
        if self.library_path is None or self.library_config is None:
            raise RuntimeError("Library path not set")
        config_file = self.library_path / ".asset-library" / "config.json"
        text = self.library_config.model_dump_json(indent=2)
        config_file.write_text(text)


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="ConfigService debug CLI")
    parser.add_argument("--library", help="Library root path", default=None)
    args = parser.parse_args()

    service = ConfigService()
    print(service.settings.model_dump_json(indent=2))
    if args.library:
        try:
            service.set_library_path(Path(args.library))
            print(service.library_config.model_dump_json(indent=2))
        except ValidationError as exc:  # pragma: no cover - CLI feedback
            print(exc)
