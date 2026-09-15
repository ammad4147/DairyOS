from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dairyos.api.reporting import (
    ReportingRequest,
    _canonical_dataset,
    _generic_repo_dataset,
    _in_period,
    _repo_records,
)


class _Factory:
    pass


class _Container:
    repository_factory = _Factory()


def test_missing_repository_fails_closed_instead_of_becoming_authoritative_zero():
    with pytest.raises(HTTPException) as exc:
        _repo_records(_Container(), "missing_authority")
    assert exc.value.status_code == 503


def test_bounded_historical_period_rejects_undated_record():
    undated = SimpleNamespace(id=1)
    assert _in_period(undated, date(2026, 9, 1), date(2026, 9, 30)) is False


def test_generic_historical_dataset_cannot_admit_undated_rows():
    class Repo:
        def get_all(self):
            return [SimpleNamespace(id=1)]

    class Factory:
        def feed_rations(self):
            return Repo()

    container = SimpleNamespace(repository_factory=Factory())
    request = ReportingRequest(
        report_id="historical-tmr",
        domain="FEED",
        period_mode="DATE_RANGE",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )
    result = _generic_repo_dataset(
        request,
        container,
        date(2026, 9, 16),
        "feed_rations",
        {"category": ("category",), "ingredient": ("ingredient",)},
    )
    assert result["rows"] == []
    assert result["summary"]["records"] == 0


def test_whole_farm_snapshot_declares_all_required_reporting_sections(monkeypatch):
    expected = {
        "animal-population",
        "daily-milk",
        "milk-quality-log",
        "current-tmr",
        "finance-ledger",
        "breeding-cycle",
        "health-cases",
        "vaccination-schedule",
        "coml-period",
    }
    seen: list[str] = []

    def fake_dataset(payload, *, container, operational_today):
        if payload.report_id == "whole-farm-snapshot":
            return original(payload, container=container, operational_today=operational_today)
        seen.append(payload.report_id)
        return {
            "dataset_status": "AUTHORITATIVE_DATASET",
            "authority_status": "AUTHORITY_AVAILABLE",
            "columns": [],
            "rows": [],
            "summary": {},
            "warnings": [],
        }

    import dairyos.api.reporting as reporting

    original = reporting._canonical_dataset
    monkeypatch.setattr(reporting, "_canonical_dataset", fake_dataset)
    request = ReportingRequest(
        report_id="whole-farm-snapshot",
        domain="WHOLE_FARM",
        period_mode="SNAPSHOT_DATE",
        snapshot_date=date(2026, 9, 16),
    )
    original(request, container=object(), operational_today=date(2026, 9, 16))
    assert expected.issubset(set(seen))
