from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_historical_forensic_handover_tool_is_non_mutating():
    source = read("tools/handover/Deploy-DairyOS-ForensicRemediation.ps1")

    assert "RETIRED DAIRYOS HANDOVER ARTEFACT" in source
    assert "NO ACTION PERFORMED" in source
    assert "Copy-Item" not in source
    assert "Set-Content" not in source
    assert "Add-Content" not in source
    assert "Remove-Item" not in source
    assert "Move-Item" not in source
    assert "git reset" not in source.lower()
    assert "git checkout" not in source.lower()
    assert "git restore" not in source.lower()
