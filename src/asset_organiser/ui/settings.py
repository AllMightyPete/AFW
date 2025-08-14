from __future__ import annotations

from PySide6.QtWidgets import (  # noqa: E501
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config_service import ConfigService


class SettingsView(QWidget):
    """Settings editor connected to ConfigService."""

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
