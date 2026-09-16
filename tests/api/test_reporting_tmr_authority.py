from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dairyos.api import reporting_tmr


class Factory:
    pass


def request(report_id, period_mode, **kwargs):
    return SimpleNamespace(
        report_id=report_id,
        period_mode=period_mode,
        filters=kwargs.pop("filters", {}),
        operational_date=kwargs.pop("operational_date", None),
        as_of_date=kwargs.pop("as_of_date", None),
        start_date=kwargs.pop("start_date", None),
        end_date=kwargs.pop("end_date", None),
    )


def test_historical_tmr_uses_daily_snapshot_period_authority(monkeypatch):
    calls = []

    def fake_period(factory, start, end):
        calls.append((factory, start, end))
        return {
            "total_feed_cost": 300.0,
            "daily": [
                {
                    "date": "2026-09-14",
                    "feed_cost": 300.0,
                    "basis": "LOCKED_DAILY_TMR",
                    "record_id": 41,
                    "locked_at": "2026-09-14T12:00:00+05:00",
                }
            ],
            "locked_days": 1,
            "provisional_days": 0,
            "complete": True,
            "missing_authority_days": [],
            "source": "TMR_DAILY_12_00_SNAPSHOT",
            "requested_period": {"start": "2026-09-14", "end": "2026-09-14"},
            "effective_period": {"start": "2026-09-14", "end": "2026-09-14"},
            "clamped_to_operational_date": False,
        }

    monkeypatch.setattr(reporting_tmr, "tmr_feed_cost_for_period", fake_period)
    factory = Factory()
    result = reporting_tmr.tmr_reporting_dataset(
        request("historical-tmr", "AS_OF_DATE", as_of_date=date(2026, 9, 14)),
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 15),
    )

    assert calls == [(factory, date(2026, 9, 14), date(2026, 9, 14))]
    assert result["dataset_status"] == "AUTHORITATIVE_HISTORICAL_TMR_DATASET"
    assert result["summary"]["source"] == "TMR_DAILY_12_00_SNAPSHOT"
    assert result["rows"][0]["basis"] == "LOCKED_DAILY_TMR"
    assert result["rows"][0]["feed_cost"] == 300.0


def test_historical_tmr_missing_snapshot_fails_closed(monkeypatch):
    def fake_period(factory, start, end):
        return {
            "total_feed_cost": None,
            "daily": [
                {
                    "date": "2026-09-13",
                    "feed_cost": None,
                    "basis": "DAILY_TMR_SNAPSHOT_MISSING",
                    "record_id": None,
                    "locked_at": None,
                }
            ],
            "locked_days": 0,
            "provisional_days": 0,
            "complete": False,
            "missing_authority_days": ["2026-09-13"],
            "source": "TMR_DAILY_12_00_SNAPSHOT",
        }

    monkeypatch.setattr(reporting_tmr, "tmr_feed_cost_for_period", fake_period)
    with pytest.raises(HTTPException) as exc:
        reporting_tmr.tmr_reporting_dataset(
            request("historical-tmr", "AS_OF_DATE", as_of_date=date(2026, 9, 13)),
            SimpleNamespace(repository_factory=Factory()),
            date(2026, 9, 15),
        )

    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "HISTORICAL_TMR_AUTHORITY_MISSING"
    assert exc.value.detail["authority"] == "TMR_DAILY_12_00_SNAPSHOT"
    assert exc.value.detail["missing_authority_days"] == ["2026-09-13"]


def test_historical_tmr_never_calls_live_tmr_for_missing_past_day(monkeypatch):
    monkeypatch.setattr(
        reporting_tmr,
        "tmr_feed_cost_for_period",
        lambda factory, start, end: {
            "total_feed_cost": None,
            "daily": [],
            "complete": False,
            "missing_authority_days": [start.isoformat()],
            "source": "TMR_DAILY_12_00_SNAPSHOT",
        },
    )

    def forbidden_live(*args, **kwargs):
        raise AssertionError("Historical Reporting must not use live TMR fallback")

    monkeypatch.setattr(reporting_tmr, "build_live_tmr_summary", forbidden_live)
    with pytest.raises(HTTPException) as exc:
        reporting_tmr.tmr_reporting_dataset(
            request("historical-tmr", "AS_OF_DATE", as_of_date=date(2026, 9, 12)),
            SimpleNamespace(repository_factory=Factory()),
            date(2026, 9, 15),
        )
    assert exc.value.detail["code"] == "HISTORICAL_TMR_AUTHORITY_MISSING"


def test_current_tmr_uses_live_governed_authority(monkeypatch):
    factory = Factory()
    calls = []

    def fake_live(selected_factory, *, operational_date):
        calls.append((selected_factory, operational_date))
        return {
            "operational_date": "2026-09-15",
            "stages": {
                "early_milking": {
                    "label": "Early Lactation",
                    "ingredients": [
                        {
                            "catalog_name": "Silage",
                            "quantity": 22.0,
                            "dose_unit": "kg",
                            "price_per_kg": 20.0,
                            "price_source": "FINANCE",
                            "selected_price_source": "FINANCE",
                            "finance_transaction_id": 9,
                            "finance_purchase_date": "2026-09-10",
                            "cost_per_head_day": 440.0,
                        }
                    ],
                }
            },
            "categories": [
                {"category": "Milking", "stage_keys": ["early_milking"], "animal_count": 1}
            ],
            "herd_counts": {"Milking": 1},
            "total_herd_feed_cost_per_day": 440.0,
            "milk_production_today_liters": 20.0,
            "feed_cost_per_litre_today": 22.0,
            "feed_cost_basis": "TMR_RATION_X_ACTIVE_HERD",
        }

    monkeypatch.setattr(reporting_tmr, "build_live_tmr_summary", fake_live)
    result = reporting_tmr.tmr_reporting_dataset(
        request("current-tmr", "CURRENT_HERD"),
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 15),
    )

    assert calls == [(factory, date(2026, 9, 15))]
    assert result["dataset_status"] == "AUTHORITATIVE_CURRENT_TMR_DATASET"
    assert result["summary"]["total_herd_feed_cost_per_day"] == 440.0
    assert result["summary"]["feed_cost_per_litre_today"] == 22.0
    assert result["rows"][0]["ingredient"] == "Silage"


def test_current_tmr_rejects_prior_operational_date_without_reconstruction(monkeypatch):
    monkeypatch.setattr(
        reporting_tmr,
        "build_live_tmr_summary",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("live authority must not be called")),
    )
    with pytest.raises(HTTPException) as exc:
        reporting_tmr.tmr_reporting_dataset(
            request("current-tmr", "OPERATIONAL_DATE", operational_date=date(2026, 9, 14)),
            SimpleNamespace(repository_factory=Factory()),
            date(2026, 9, 15),
        )
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "CURRENT_TMR_REQUIRES_CURRENT_OPERATIONAL_DATE"
