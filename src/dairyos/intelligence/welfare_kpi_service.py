from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone


class WelfareKPIService:
    """Derive welfare indicators strictly from persisted operational evidence."""

    @staticmethod
    def _as_datetime(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
        return None

    @classmethod
    def _in_period(cls, record, start, end, *fields):
        for field in fields:
            timestamp = cls._as_datetime(getattr(record, field, None))
            if timestamp is not None:
                return start <= timestamp < end
        return False

    def evaluate(self, *, animals, health_observations, treatments, start, end):
        animals = list(animals or [])
        health = [
            r for r in (health_observations or [])
            if self._in_period(r, start, end, "observed_at", "timestamp", "observation_date", "created_at")
        ]
        treatments_in_period = [
            r for r in (treatments or [])
            if self._in_period(r, start, end, "treated_at", "timestamp", "treatment_date", "created_at")
        ]

        active_animals = [a for a in animals if getattr(a, "active", True)]
        denominator = len(active_animals)
        health_animals = {getattr(r, "animal_id", None) for r in health if getattr(r, "animal_id", None)}
        treatment_animals = {getattr(r, "animal_id", None) for r in treatments_in_period if getattr(r, "animal_id", None)}

        # The current Animal model does not expose an authoritative mortality
        # event stream here. Do not infer mortality from inactive animals.
        mortality_rate = None
        morbidity_rate = round((len(health_animals) / denominator) * 100, 2) if denominator else None
        treatment_rate = round((len(treatment_animals) / denominator) * 100, 2) if denominator else None

        severity_counts = Counter(
            str(getattr(r, "severity", "NORMAL") or "NORMAL").upper()
            for r in health
        )

        available = {
            "morbidity_rate_percent": morbidity_rate is not None,
            "treatment_rate_percent": treatment_rate is not None,
            "mortality_rate_percent": False,
            "lameness_rate_percent": False,
            "body_condition_score": False,
        }
        evidence_count = len(health) + len(treatments_in_period)

        return {
            "period": {"start": start.isoformat(), "end": end.isoformat(), "days": (end - start).days},
            "data_status": "LIVE_PERSISTED_DATA" if evidence_count else "NO_DATA",
            "evidence": {
                "active_animals": denominator,
                "health_observations": len(health),
                "animals_with_health_observations": len(health_animals),
                "treatments": len(treatments_in_period),
                "animals_treated": len(treatment_animals),
            },
            "kpis": {
                "morbidity_rate_percent": morbidity_rate,
                "treatment_rate_percent": treatment_rate,
                "mortality_rate_percent": mortality_rate,
            },
            "health_severity_counts": dict(severity_counts),
            "coverage": available,
            "unsupported_metrics": [
                name for name, covered in available.items() if not covered
            ],
            "provenance": "PERSISTED_ANIMAL_HEALTH_AND_TREATMENT_RECORDS",
        }

    def evaluate_last_days(self, *, animals, health_observations, treatments, days=30, now=None):
        end = self._as_datetime(now) or datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        return self.evaluate(
            animals=animals,
            health_observations=health_observations,
            treatments=treatments,
            start=start,
            end=end,
        )
