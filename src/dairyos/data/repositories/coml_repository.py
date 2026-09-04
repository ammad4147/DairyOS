from __future__ import annotations

from datetime import date

from dairyos.core.time_utils import utcnow
from dairyos.data.models.coml_record import COMLRecord


class COMLRepository:
    def __init__(self, session):
        self.session = session

    def get_by_month(self, month_start: date):
        return (
            self.session.query(COMLRecord)
            .filter(COMLRecord.month_start == month_start)
            .first()
        )

    def get_all(self):
        return (
            self.session.query(COMLRecord)
            .order_by(COMLRecord.month_start.desc())
            .all()
        )

    def upsert(
        self,
        *,
        month_start: date,
        feed_cost_per_liter: float,
        opex_cost_per_liter: float,
        notes: str | None,
        updated_by: str,
        official_source: str = "UNSPECIFIED",
    ) -> COMLRecord:
        row = self.get_by_month(month_start)
        now = utcnow()
        total = round(float(feed_cost_per_liter) + float(opex_cost_per_liter), 4)
        source = str(official_source or "UNSPECIFIED").strip().upper()
        if source not in {"AUTO", "MANUAL", "UNSPECIFIED"}:
            raise ValueError("official_source must be AUTO, MANUAL, or UNSPECIFIED")
        if row is None:
            row = COMLRecord(
                month_start=month_start,
                feed_cost_per_liter=float(feed_cost_per_liter),
                opex_cost_per_liter=float(opex_cost_per_liter),
                total_coml_per_liter=total,
                status="OFFICIAL",
                official_source=source,
                notes=notes,
                created_at=now,
                updated_at=now,
                locked_at=now,
                updated_by=updated_by,
            )
            self.session.add(row)
        else:
            row.feed_cost_per_liter = float(feed_cost_per_liter)
            row.opex_cost_per_liter = float(opex_cost_per_liter)
            row.total_coml_per_liter = total
            row.status = "OFFICIAL"
            row.official_source = source
            row.notes = notes
            row.updated_at = now
            row.locked_at = now
            row.updated_by = updated_by
        self.session.commit()
        self.session.refresh(row)
        return row