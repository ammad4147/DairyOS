from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dairyos.api.reporting_milk_quality import milk_quality_reporting_dataset


class QualityRepo:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def get_range(self, start_date, end_date):
        self.calls.append((start_date, end_date))
        return [row for row in self.rows if start_date <= row.quality_date.date() <= end_date and row.status == "RECORDED"]


class Factory:
    def __init__(self, repository):
        self.repository = repository

    def milk_quality(self):
        return self.repository


def request(report_id, period_mode, **kwargs):
    return SimpleNamespace(
        report_id=report_id,
        period_mode=period_mode,
        operational_date=kwargs.get("operational_date"),
        start_date=kwargs.get("start_date"),
        end_date=kwargs.get("end_date"),
        as_of_date=kwargs.get("as_of_date"),
        filters=kwargs.get("filters", {}),
    )


def sample(day, fat, snf, *, sample_type="BULK_TANK", revisions=None):
    return SimpleNamespace(
        id=day,
        quality_date=datetime(2026, 9, day),
        fat_pct=fat,
        snf_pct=snf,
        sample_type=sample_type,
        notes=None,
        recorded_by="Operator",
        status="RECORDED",
        recorded_at=datetime(2026, 9, day, 12),
        updated_at=datetime(2026, 9, day, 13),
        revision_history=revisions or [],
    )


def test_quality_log_uses_repository_range_and_operational_date():
    repo = QualityRepo([sample(14, 3.7, 8.5), sample(15, 3.8, 8.6)])
    payload = request("milk-quality-log", "OPERATIONAL_DATE", operational_date=date(2026, 9, 15))
    result = milk_quality_reporting_dataset(payload, SimpleNamespace(repository_factory=Factory(repo)), date(2026, 9, 16))
    assert repo.calls == [(date(2026, 9, 15), date(2026, 9, 15))]
    assert result["dataset_status"] == "AUTHORITATIVE_DATASET"
    assert result["rows"][0]["quality_date"] == "2026-09-15"
    assert result["rows"][0]["fat_pct"] == 3.8


def test_quality_log_preserves_revision_history_as_export_safe_scalar():
    revisions = [{"fat_pct": 3.5, "snf_pct": 8.4, "recorded_by": "First Operator"}]
    repo = QualityRepo([sample(15, 3.8, 8.6, revisions=revisions)])
    payload = request("milk-quality-log", "OPERATIONAL_DATE", operational_date=date(2026, 9, 15))
    result = milk_quality_reporting_dataset(payload, SimpleNamespace(repository_factory=Factory(repo)), date(2026, 9, 16))
    assert isinstance(result["rows"][0]["revision_history"], str)
    assert "First Operator" in result["rows"][0]["revision_history"]
    assert result["summary"]["revision_history_preserved"] is True


def test_quality_summary_matches_existing_api_average_arithmetic():
    repo = QualityRepo([sample(14, 3.7, 8.5), sample(15, 3.9, 8.7)])
    payload = request("quality-summary", "DATE_RANGE", start_date=date(2026, 9, 14), end_date=date(2026, 9, 15))
    result = milk_quality_reporting_dataset(payload, SimpleNamespace(repository_factory=Factory(repo)), date(2026, 9, 16))
    assert result["summary"]["sample_count"] == 2
    assert result["summary"]["average_fat_pct"] == 3.8
    assert result["summary"]["average_snf_pct"] == 8.6
    assert result["summary"]["latest_sample_date"] == "2026-09-15"


def test_quality_filters_are_applied_after_authoritative_range_read():
    repo = QualityRepo([sample(14, 3.7, 8.5, sample_type="BULK_TANK"), sample(15, 4.0, 8.8, sample_type="LAB")])
    payload = request("milk-quality-log", "DATE_RANGE", start_date=date(2026, 9, 14), end_date=date(2026, 9, 15), filters={"sample_type": "LAB"})
    result = milk_quality_reporting_dataset(payload, SimpleNamespace(repository_factory=Factory(repo)), date(2026, 9, 16))
    assert result["summary"]["sample_count"] == 1
    assert result["rows"][0]["sample_type"] == "LAB"


def test_empty_quality_period_is_authoritative_not_fabricated():
    repo = QualityRepo([])
    payload = request("quality-summary", "DATE_RANGE", start_date=date(2026, 9, 1), end_date=date(2026, 9, 2))
    result = milk_quality_reporting_dataset(payload, SimpleNamespace(repository_factory=Factory(repo)), date(2026, 9, 16))
    assert result["summary"]["sample_count"] == 0
    assert result["summary"]["average_fat_pct"] is None
    assert result["summary"]["average_snf_pct"] is None
    assert result["warnings"]


def test_missing_quality_authority_fails_closed():
    payload = request("milk-quality-log", "OPERATIONAL_DATE", operational_date=date(2026, 9, 15))
    with pytest.raises(HTTPException) as exc:
        milk_quality_reporting_dataset(payload, SimpleNamespace(repository_factory=SimpleNamespace()), date(2026, 9, 16))
    assert exc.value.status_code == 503
    assert exc.value.detail["authority"] == "MilkQuality"
