from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func

from dairyos.core.time_utils import utcnow
from dairyos.data.models.milk_quality_sample import MilkQualitySample


class MilkQualityRepository:
    def __init__(self, session=None):
        self.session = session
        self.records: list[MilkQualitySample] = []

    def get_by_date(self, quality_date: date):
        if self.session:
            return (
                self.session.query(MilkQualitySample)
                .filter(func.date(MilkQualitySample.quality_date) == quality_date)
                .filter(MilkQualitySample.status == "RECORDED")
                .first()
            )
        for row in self.records:
            if row.quality_date.date() == quality_date and row.status == "RECORDED":
                return row
        return None

    def upsert(self, *, quality_date: date, fat_pct: float, snf_pct: float,
               sample_type: str, notes: str | None, recorded_by: str):
        row = self.get_by_date(quality_date)
        when = datetime(quality_date.year, quality_date.month, quality_date.day)
        if row is None:
            row = MilkQualitySample(
                quality_date=when,
                fat_pct=fat_pct,
                snf_pct=snf_pct,
                sample_type=sample_type,
                notes=notes,
                recorded_by=recorded_by,
                status="RECORDED",
                recorded_at=utcnow(),
                updated_at=utcnow(),
            )
            if self.session:
                self.session.add(row)
            else:
                self.records.append(row)
        else:
            row.fat_pct = fat_pct
            row.snf_pct = snf_pct
            row.sample_type = sample_type
            row.notes = notes
            row.recorded_by = recorded_by
            row.updated_at = utcnow()

        if self.session:
            self.session.commit()
            self.session.refresh(row)
        return row

    def get_range(self, start_date: date, end_date: date):
        if self.session:
            return (
                self.session.query(MilkQualitySample)
                .filter(func.date(MilkQualitySample.quality_date) >= start_date)
                .filter(func.date(MilkQualitySample.quality_date) <= end_date)
                .filter(MilkQualitySample.status == "RECORDED")
                .order_by(MilkQualitySample.quality_date.asc())
                .all()
            )
        return [
            row for row in self.records
            if start_date <= row.quality_date.date() <= end_date and row.status == "RECORDED"
        ]

    def get_all(self):
        if self.session:
            return (
                self.session.query(MilkQualitySample)
                .filter(MilkQualitySample.status == "RECORDED")
                .order_by(MilkQualitySample.quality_date.desc())
                .all()
            )
        return [row for row in self.records if row.status == "RECORDED"]
