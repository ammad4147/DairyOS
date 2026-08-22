from __future__ import annotations

from datetime import date, datetime

from dairyos.api.milk_quality import MilkQualityRequest
from dairyos.data.models.milk_quality_sample import MilkQualitySample
from dairyos.data.repositories.milk_quality_repository import MilkQualityRepository


def test_quality_request_accepts_valid_percentages():
    payload = MilkQualityRequest(
        quality_date=date(2026, 8, 23),
        fat_pct=3.8,
        snf_pct=8.7,
    )

    assert payload.fat_pct == 3.8
    assert payload.snf_pct == 8.7


def test_quality_request_rejects_non_positive_percentages():
    try:
        MilkQualityRequest(
            quality_date=date(2026, 8, 23),
            fat_pct=0,
            snf_pct=8.7,
        )
    except Exception as exc:
        assert "greater than 0" in str(exc)
    else:
        raise AssertionError("Expected validation error for zero fat percentage")


def test_quality_repository_upsert_is_one_row_per_date():
    repository = MilkQualityRepository()
    first = repository.upsert(
        quality_date=date(2026, 8, 23),
        fat_pct=3.8,
        snf_pct=8.7,
        sample_type="BULK_TANK",
        notes="Morning composite",
        recorded_by="TEST",
    )
    second = repository.upsert(
        quality_date=date(2026, 8, 23),
        fat_pct=4.1,
        snf_pct=8.9,
        sample_type="BULK_TANK",
        notes="Updated sample",
        recorded_by="TEST2",
    )

    assert first is second
    assert len(repository.records) == 1
    assert second.fat_pct == 4.1
    assert second.recorded_by == "TEST2"


def test_quality_repository_summary_range_is_date_isolated():
    repository = MilkQualityRepository()
    repository.records = [
        MilkQualitySample(
            quality_date=datetime(2026, 8, 22),
            fat_pct=3.5,
            snf_pct=8.4,
            status="RECORDED",
        ),
        MilkQualitySample(
            quality_date=datetime(2026, 8, 23),
            fat_pct=4.0,
            snf_pct=8.8,
            status="RECORDED",
        ),
        MilkQualitySample(
            quality_date=datetime(2026, 8, 24),
            fat_pct=4.5,
            snf_pct=9.2,
            status="VOID",
        ),
    ]

    rows = repository.get_range(
        date(2026, 8, 22),
        date(2026, 8, 23),
    )

    assert len(rows) == 2
    assert [round(row.fat_pct, 1) for row in rows] == [3.5, 4.0]
