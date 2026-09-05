from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

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
        feed_cost_per_liter: Decimal,
        opex_cost_per_liter: Decimal,
        notes: str | None,
        updated_by: str,
    ) -> COMLRecord:
        row = self.get_by_month(month_start)
        now = utcnow()
        feed = Decimal(feed_cost_per_liter).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP,
        )
        opex = Decimal(opex_cost_per_liter).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP,
        )
        total = (feed + opex).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP,
        )
        if row is None:
            row = COMLRecord(
                month_start=month_start,
                feed_cost_per_liter=feed,
                opex_cost_per_liter=opex,
                total_coml_per_liter=total,
                status="OFFICIAL",
                notes=notes,
                created_at=now,
                updated_at=now,
                locked_at=now,
                updated_by=updated_by,
            )
            self.session.add(row)
        else:
            row.feed_cost_per_liter = feed
            row.opex_cost_per_liter = opex
            row.total_coml_per_liter = total
            row.status = "OFFICIAL"
            row.notes = notes
            row.updated_at = now
            row.locked_at = now
            row.updated_by = updated_by
        self.session.commit()
        self.session.refresh(row)
        return row