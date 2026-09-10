from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANUAL = ROOT / "docs" / "operator" / "DairyOS-Operator-Manual.html"
MARKDOWN_MANUAL = ROOT / "docs" / "manuals" / "OPERATOR_MANUAL.md"
LEGACY_HELP = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "Documentation.tsx"
LEGACY_HELP_DATA = ROOT / "src" / "DairyOS.Web" / "src" / "documentation" / "manualContent.ts"
BUILD = ROOT / "scripts" / "Build-DairyOS-Installer.ps1"
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"


def test_operator_manual_is_not_shipped():
    assert not MANUAL.exists()
    assert not MARKDOWN_MANUAL.exists()
    assert not LEGACY_HELP.exists()
    assert not LEGACY_HELP_DATA.exists()

    build = BUILD.read_text(encoding="utf-8-sig")
    iss = ISS.read_text(encoding="utf-8-sig")
    assert "DairyOS-Operator-Manual.html" not in build
    assert "DairyOS-Operator-Manual.html" not in iss
    assert "DairyOS Operator Manual" not in iss
