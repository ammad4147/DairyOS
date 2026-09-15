from pathlib import Path


def test_reporting_keeps_canonical_herd_labels():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8")
    for label in ("Milking Cows", "Dry Cows", "Heifers", "Female Calves", "Male Calves", "Bulls"):
        assert label in source


def test_reporting_keeps_three_milking_sessions_distinct():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8")
    for session in ("MORNING", "AFTERNOON", "EVENING"):
        assert session in source


def test_reporting_preserves_void_audit_semantics():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8")
    assert 'status != "VOID"' in source
    assert "finance_is_active" in source
