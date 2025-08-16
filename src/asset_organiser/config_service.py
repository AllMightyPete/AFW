from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import ValidationError

from .config_models import GeneralSettings, LibraryConfig, LLMProviderProfile

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
        config_dir = library_root / ".asset-library"
        if not config_dir.exists():
            logger.info(
                "Creating default library config at %s",
                config_dir,
            )
            config_dir.mkdir(parents=True, exist_ok=True)
            self.library_config = LibraryConfig()
            self.library_path = library_root
            self.save_library_config()
            return

        data = self._load_library_config(config_dir)
        self.library_config = LibraryConfig.model_validate(data)
        self.library_path = library_root

    # ------------------------------------------------------------------
    def _load_library_config(self, config_dir: Path) -> dict:
        def read_json(path: Path):
            if path.exists():
                return json.loads(path.read_text())
            return None

        file_types = read_json(config_dir / "file-types.json")
        asset_types = read_json(config_dir / "asset-types.json")
        suppliers = read_json(config_dir / "suppliers.json")
        classification = read_json(config_dir / "classification.json") or {}
        providers = read_json(config_dir / "llm-profiles.json")
        if providers and "Providers" in providers:
            classification["Providers"] = providers["Providers"]
        processing = read_json(config_dir / "processing.json")
        indexing = read_json(config_dir / "indexing.json")

        data: dict = {}
        if file_types is not None:
            data["FILE_TYPE_DEFINITIONS"] = file_types
        if asset_types is not None:
            data["ASSET_TYPE_DEFINITIONS"] = asset_types
        if suppliers is not None:
            data["SUPPLIERS"] = suppliers
        if classification:
            data["CLASSIFICATION"] = classification
        if processing is not None:
            data["PROCESSING"] = processing
        if indexing is not None:
            data["INDEXING"] = indexing
        return data

    # ------------------------------------------------------------------
    def save_library_config(self) -> None:
        if self.library_path is None or self.library_config is None:
            raise RuntimeError("Library path not set")
        config_dir = self.library_path / ".asset-library"
        config_dir.mkdir(parents=True, exist_ok=True)

        data = self.library_config.model_dump(by_alias=True)
        (config_dir / "file-types.json").write_text(
            json.dumps(data.get("FILE_TYPE_DEFINITIONS", {}), indent=2)
        )
        (config_dir / "asset-types.json").write_text(
            json.dumps(data.get("ASSET_TYPE_DEFINITIONS", {}), indent=2)
        )
        (config_dir / "suppliers.json").write_text(
            json.dumps(data.get("SUPPLIERS", {}), indent=2)
        )
        classification = data.get("CLASSIFICATION", {})
        providers = {"Providers": classification.pop("Providers", [])}
        (config_dir / "classification.json").write_text(
            json.dumps(classification, indent=2)
        )
        (config_dir / "llm-profiles.json").write_text(
            json.dumps(providers, indent=2),
        )
        (config_dir / "processing.json").write_text(
            json.dumps(data.get("PROCESSING", {}), indent=2)
        )
        (config_dir / "indexing.json").write_text(
            json.dumps(data.get("INDEXING", {}), indent=2)
        )

    # ------------------------------------------------------------------
    def get_active_provider_profile(self) -> Optional[LLMProviderProfile]:
        if self.library_config is None:
            return None
        classification = self.library_config.CLASSIFICATION
        active = classification.active_provider
        for profile in classification.providers:
            if profile.profile_name == active:
                return profile
        if classification.providers:
            return classification.providers[0]
        return None

    # ------------------------------------------------------------------
    def get_classification_prompts(self) -> Dict[str, str]:
        if self.library_config is None:
            return {}
        return self.library_config.CLASSIFICATION.prompts

    # ------------------------------------------------------------------
    def get_asset_type_keywords(self) -> Dict[str, List[str]]:
        if self.library_config is None:
            return {}
        return self.library_config.CLASSIFICATION.asset_type_keywords


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
