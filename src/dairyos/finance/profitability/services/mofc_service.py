from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone


class MOFCService:
    """Calculate animal/group Margin Over Feed Cost from persisted records.

    Feed cost is taken only from historical feed-cost snapshots already stored
    on FeedRecord. Legacy/unpriced feed is reported separately and never given
    an invented price.
    """

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def evaluate(
        self,
        milk_records,
        feed_records,
        milk_price_per_litre: float,
        days: int = 30,
        now: datetime | None = None,
        *,
        subject_type: str = "ANIMAL",
    ) -> dict:
        if days < 1:
            raise ValueError("days must be positive")
        if milk_price_per_litre < 0:
            raise ValueError("milk_price_per_litre must be non-negative")

        now_dt = self._as_utc(now or datetime.now(timezone.utc))
        cutoff = now_dt - timedelta(days=days)

        milk_by_subject: dict[str, float] = defaultdict(float)
        feed_cost_by_subject: dict[str, float] = defaultdict(float)
        feed_qty_by_subject: dict[str, float] = defaultdict(float)
        unpriced_qty_by_subject: dict[str, float] = defaultdict(float)
        unpriced_records_by_subject: dict[str, int] = defaultdict(int)

        for row in milk_records:
            timestamp = self._as_utc(getattr(row, "production_date", None))
            if timestamp is None or timestamp < cutoff:
                continue
            status = str(getattr(row, "status", "RECORDED") or "RECORDED").upper()
            if status not in {"RECORDED", "SOLD", "DISPOSED", "WASTAGE"}:
                continue
            subject_id = str(getattr(row, "animal_id", "") or "").strip()
            if not subject_id:
                continue
            milk_by_subject[subject_id] += max(0.0, float(getattr(row, "total_yield", 0.0) or 0.0))

        for row in feed_records:
            timestamp = self._as_utc(getattr(row, "feeding_date", None))
            if timestamp is None or timestamp < cutoff:
                continue
            quantity = max(0.0, float(getattr(row, "quantity_kg", 0.0) or 0.0))
            subject_id = str(getattr(row, "animal_id", "") or "").strip()
            if not subject_id:
                subject_id = f"GROUP:{str(getattr(row, 'group_or_pen', 'UNSPECIFIED') or 'UNSPECIFIED').strip()}"
            feed_qty_by_subject[subject_id] += quantity
            total_cost = getattr(row, "total_feed_cost", None)
            if total_cost is None:
                unpriced_qty_by_subject[subject_id] += quantity
                unpriced_records_by_subject[subject_id] += 1
            else:
                feed_cost_by_subject[subject_id] += max(0.0, float(total_cost))

        subjects = sorted(set(milk_by_subject) | set(feed_qty_by_subject))
        rows = []
        for subject_id in subjects:
            milk_litres = milk_by_subject.get(subject_id, 0.0)
            feed_cost = feed_cost_by_subject.get(subject_id, 0.0)
            feed_qty = feed_qty_by_subject.get(subject_id, 0.0)
            unpriced_qty = unpriced_qty_by_subject.get(subject_id, 0.0)
            revenue = milk_litres * float(milk_price_per_litre)
            mofc = revenue - feed_cost
            fully_priced = unpriced_qty <= 0.000001
            rows.append({
                "subject_id": subject_id,
                "milk_litres": round(milk_litres, 3),
                "milk_revenue": round(revenue, 2),
                "feed_quantity_kg": round(feed_qty, 3),
                "feed_cost": round(feed_cost, 2),
                "unpriced_feed_quantity_kg": round(unpriced_qty, 3),
                "unpriced_feed_record_count": unpriced_records_by_subject.get(subject_id, 0),
                "mofc": round(mofc, 2) if fully_priced else None,
                "mofc_status": "ACTUAL" if fully_priced else "PARTIAL_COST_DATA",
            })

        return {
            "period_days": days,
            "from": cutoff.isoformat(),
            "to": now_dt.isoformat(),
            "milk_price_per_litre": float(milk_price_per_litre),
            "subject_type": subject_type,
            "data_status": "LIVE_PERSISTED_DATA",
            "rows": rows,
        }
