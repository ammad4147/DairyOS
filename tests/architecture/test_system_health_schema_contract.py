from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_system_health_uses_canonical_runtime_table_names():
    source = (ROOT / "src" / "dairyos" / "api" / "health.py").read_text(
        encoding="utf-8-sig"
    )

    assert '"financial_transactions"' in source
    assert '"financial_transaction"' not in source


def test_system_health_uses_canonical_projection_journal_link():
    source = (ROOT / "src" / "dairyos" / "api" / "health.py").read_text(
        encoding="utf-8-sig"
    )

    assert "o.journal_id" in source
    assert "o.event_id" not in source
    assert "get_columns(" in source
    assert '"operational_projection_outbox"' in source
