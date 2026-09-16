from datetime import date
from types import SimpleNamespace

from dairyos.api import reporting


def test_milk_quality_reports_delegate_to_authoritative_adapter(monkeypatch):
    calls = []

    def fake_adapter(payload, container, operational_today):
        calls.append((payload.report_id, container, operational_today))
        return {
            "dataset_status": "AUTHORITATIVE_DATASET",
            "authority_status": "AUTHORITY_AVAILABLE",
            "columns": [],
            "rows": [],
            "summary": {"delegated": True},
            "warnings": [],
        }

    monkeypatch.setattr(reporting, "milk_quality_reporting_dataset", fake_adapter)
    container = SimpleNamespace()
    for report_id in ("milk-quality-log", "quality-summary"):
        payload = SimpleNamespace(report_id=report_id)
        result = reporting._canonical_dataset(
            payload,
            container=container,
            operational_today=date(2026, 9, 16),
        )
        assert result["summary"]["delegated"] is True

    assert [call[0] for call in calls] == ["milk-quality-log", "quality-summary"]
    assert all(call[1] is container for call in calls)
    assert all(call[2] == date(2026, 9, 16) for call in calls)
