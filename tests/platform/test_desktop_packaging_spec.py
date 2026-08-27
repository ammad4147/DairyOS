from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "DairyOS.spec"
PYPROJECT = ROOT / "pyproject.toml"


def test_desktop_spec_has_no_machine_specific_repository_path():
    text = SPEC.read_text(encoding="utf-8")
    assert "D:/DairyOS" not in text
    assert "C:/DairyOS" not in text
    assert "C:\\DairyOS" not in text
    assert "SPECPATH" in text
    assert "ROOT = Path(SPECPATH).resolve()" in text
    assert 'supervisor.py' in text


def test_desktop_build_extra_declares_packaging_tooling():
    text = PYPROJECT.read_text(encoding="utf-8")
    assert "[project.optional-dependencies]" in text
    assert "desktop-build" in text
    assert "pywebview>=6.2.1" in text
    assert "pyinstaller>=6.19" in text
