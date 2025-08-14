"""Basic tests for package import."""

import importlib


def test_import_package() -> None:
    """Package can be imported."""
    assert importlib.import_module("asset_organiser").__version__ == "0.1.0"
