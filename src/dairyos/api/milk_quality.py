from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.data.repositories.repository_factory import RepositoryFactory


router = APIRouter(prefix="/farm/milk", tags=["Milk Quality"])


class MilkQualityRequest(BaseModel):
    quality_date: date
    fat_pct: float = Field(gt=0, le=15)
    snf_pct: float = Field(gt=0, le=15)
    sample_type: str = Field(default="BULK_TANK", min_length=1)
    notes: str | None = None
    recorded_by: str = Field(default="UI Operator", min_length=1)


def _quality_dict(row):
    return {
        "id": row.id,
        "quality_date": row.quality_date.date().isoformat(),
        "fat_pct": row.fat_pct,
        "snf_pct": row.snf_pct,
        "sample_type": row.sample_type,
        "notes": row.notes,
        "recorded_by": row.recorded_by,
        "status": row.status,
        "recorded_at": row.recorded_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


@router.get("/quality")
def get_milk_quality(quality_date: date | None = None):
    rf = RepositoryFactory.create()
    try:
        if quality_date is not None:
            row = rf.milk_quality().get_by_date(quality_date)
            return {"data_status": "LIVE_PERSISTED_DATA", "sample": _quality_dict(row) if row else None}
        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "samples": [_quality_dict(row) for row in rf.milk_quality().get_all()],
        }
    finally:
        rf.close()


@router.post("/quality")
def record_milk_quality(payload: MilkQualityRequest):
    fat = round(float(payload.fat_pct), 3)
    snf = round(float(payload.snf_pct), 3)
    if fat <= 0 or snf <= 0:
        raise HTTPException(status_code=422, detail="Fat and SNF must be greater than zero.")

    rf = RepositoryFactory.create()
    try:
        row = rf.milk_quality().upsert(
            quality_date=payload.quality_date,
            fat_pct=fat,
            snf_pct=snf,
            sample_type=payload.sample_type.strip().upper(),
            notes=payload.notes,
            recorded_by=payload.recorded_by.strip(),
        )
        return {"data_status": "LIVE_PERSISTED_DATA", "sample": _quality_dict(row)}
    finally:
        rf.close()


@router.get("/quality-summary")
def milk_quality_summary(
    start_date: date,
    end_date: date,
):
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date.")

    rf = RepositoryFactory.create()
    try:
        rows = rf.milk_quality().get_range(start_date, end_date)
        if not rows:
            return {
                "data_status": "LIVE_PERSISTED_DATA",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "sample_count": 0,
                "average_fat_pct": None,
                "average_snf_pct": None,
                "latest_sample": None,
            }

        average_fat = round(sum(float(row.fat_pct) for row in rows) / len(rows), 3)
        average_snf = round(sum(float(row.snf_pct) for row in rows) / len(rows), 3)
        latest = rows[-1]
        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "sample_count": len(rows),
            "average_fat_pct": average_fat,
            "average_snf_pct": average_snf,
            "latest_sample": _quality_dict(latest),
        }
    finally:
        rf.close()
