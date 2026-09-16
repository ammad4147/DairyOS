from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from dairyos.api import reporting


def _request(report_id: str, **kwargs):
    defaults = {
        "report_id": report_id,
        "domain": "FEED",
        "period_mode": "AS_OF_DATE" if report_id == "historical-tmr" else "CURRENT_HERD",
        "filters": {},
    }
    defaults.update(kwargs)
    return reporting.ReportingRequest(**defaults)


def test_historical_tmr_dispatches_to_governed_tmr_adapter(monkeypatch):
    expected = {"dataset_status": "TMR_SENTINEL"}
    calls = []

    def fake_adapter(payload, container, operational_today):
        calls.append((payload.report_id, container, operational_today))
        return expected

    monkeypatch.setattr(reporting, "tmr_reporting_dataset", fake_adapter)
    monkeypatch.setattr(
        reporting,
        "_generic_repo_dataset",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("generic TMR projection must not be used")),
    )
    container = SimpleNamespace()
    selected = date(2026, 9, 10)
    payload = _request("historical-tmr", as_of_date=selected)

    result = reporting._canonical_dataset(payload, container=container, operational_today=date(2026, 9, 16))

    assert result is expected
    assert calls == [("historical-tmr", container, date(2026, 9, 16))]


def test_current_tmr_dispatches_to_governed_tmr_adapter(monkeypatch):
    expected = {"dataset_status": "TMR_SENTINEL"}
    calls = []

    def fake_adapter(payload, container, operational_today):
        calls.append((payload.report_id, container, operational_today))
        return expected

    monkeypatch.setattr(reporting, "tmr_reporting_dataset", fake_adapter)
    monkeypatch.setattr(
        reporting,
        "_generic_repo_dataset",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("generic TMR projection must not be used")),
    )
    container = SimpleNamespace()
    today = date(2026, 9, 16)
    payload = _request("current-tmr")

    result = reporting._canonical_dataset(payload, container=container, operational_today=today)

    assert result is expected
    assert calls == [("current-tmr", container, today)]
