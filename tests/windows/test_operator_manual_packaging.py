from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANUAL = ROOT / "docs" / "operator" / "DairyOS-Operator-Manual.html"
BUILD = ROOT / "scripts" / "Build-DairyOS-Installer.ps1"
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"

def test_operator_manual_covers_primary_entry_points_and_end_to_end_use():
    text = MANUAL.read_text(encoding="utf-8")
    for term in (
        "Dashboard", "Animals", "Milk", "Feed", "Finance", "Breeding",
        "Health", "Vaccination", "COP", "Record Revenue", "Record Expense",
        "DairyOS Administration", "How to use DairyOS", "recovery key",
        "receivable", "reconciliation", "Animal ID",
    ):
        assert term in text

def test_operator_manual_is_packaged_and_has_start_menu_entry():
    build = BUILD.read_text(encoding="utf-8")
    iss = ISS.read_text(encoding="utf-8")
    assert "DairyOS-Operator-Manual.html" in build
    assert "Documentation" in build
    assert "DairyOS Operator Manual" in iss
    assert "DairyOS-Operator-Manual.html" in iss
