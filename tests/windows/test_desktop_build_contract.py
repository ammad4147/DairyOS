from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "scripts" / "Build-DairyOS-Desktop.ps1"


def _source() -> str:
    return BUILD.read_text(encoding="utf-8-sig")


def test_clean_worktree_git_probes_are_null_safe_in_powershell():
    source = _source()

    assert '(@(& git rev-parse HEAD) -join "").Trim()' in source
    assert '(@(& git rev-parse "$sourceRevision^{tree}") -join "").Trim()' in source
    assert '(@(& git status --porcelain) -join "`n").Trim()' in source
