"""Unsupported optional search and Woods forecast code stays out of releases."""

import tomllib
from pathlib import Path

from dairyos.app import app

ROOT = Path(__file__).resolve().parents[2]


def test_elasticsearch_animal_search_is_not_a_mounted_or_packaged_feature():
    paths = app.openapi()["paths"]
    assert "/api/search/animals" not in paths
    assert "/api/search/health" not in paths

    dependencies = tomllib.loads((ROOT / "pyproject.toml").read_text())[
        "project"
    ]["dependencies"]
    assert not any("elasticsearch" in item.lower() for item in dependencies)
    assert "elasticsearch" not in (ROOT / "requirements.txt").read_text().lower()
    assert "elasticsearch" not in (ROOT / "DairyOS.spec").read_text().lower()

    hidden_imports = (ROOT / "packaging/desktop-hiddenimports.txt").read_text()
    assert "dairyos.api.search" not in hidden_imports
    assert "dairyos.api.index_animals" not in hidden_imports
    assert not (ROOT / "src/dairyos/api/search.py").exists()
    assert not (ROOT / "src/dairyos/api/index_animals.py").exists()


def test_unsupported_woods_lactation_forecaster_has_no_source_or_test_contract():
    assert not (ROOT / "src/dairyos/intelligence/yield_forecasting.py").exists()
    assert "yield_forecasting" not in (ROOT / "tests/platform/test_compatibility_imports.py").read_text()
