"""Unit tests for the migration gate without requiring PostgreSQL."""

from pathlib import Path

from dairyos.windows import migrations


def test_find_alembic_ini_uses_explicit_override(tmp_path, monkeypatch):
    ini = tmp_path / "alembic.ini"
    ini.write_text("[alembic]\nscript_location = db_migrations\n", encoding="utf-8")
    monkeypatch.setenv("DAIRYOS_ALEMBIC_INI", str(ini))
    assert migrations._find_alembic_ini() == Path(ini).resolve()
