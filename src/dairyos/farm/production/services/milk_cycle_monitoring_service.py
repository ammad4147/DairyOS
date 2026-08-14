from __future__ import annotations

from datetime import date, datetime

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.production.services.milk_daily_semantics import (
    expected_sessions,
    missing_sessions,
)
from dairyos.farm.production.services.milk_drop_detection_service import detect_drop
from dairyos.farm.production.services.milk_finding_service import MilkFindingService


SESSION_ORDER = {"MORNING": 0, "AFTERNOON": 1, "EVENING": 2}


class MilkCycleMonitoringService:
    """Post-write observer for individual-animal milk cycle compliance."""

    def monitor(
        self,
        *,
        animal_id: str,
        milking_session: str,
        production_date: date,
    ) -> dict:
        rf = RepositoryFactory.create()
        try:
            animal = rf.animal().get_by_animal_id(str(animal_id))
            if animal is None:
                return {"status": "UNKNOWN_ANIMAL"}

            frequency = str(getattr(animal, "milking_frequency", "") or "").upper()
            expected = expected_sessions(frequency)
            if not expected:
                self._finding(
                    rf,
                    severity="HIGH",
                    title=f"Milking frequency not configured for {animal_id}",
                    detail=(
                        f"{animal_id} received a milk entry on {production_date.isoformat()} "
                        "but has no governed two- or three-session milking frequency."
                    ),
                    subject_id=str(animal_id),
                    dedupe_key=f"MILK_FREQUENCY_MISSING:{animal_id}",
                )
                return {"status": "NO_GOVERNED_FREQUENCY"}

            rows = rf.milk().get_by_animal_id(str(animal_id))
            current = next(
                (
                    row for row in rows
                    if _as_date(row.production_date) == production_date
                    and bool(row.session_ledger)
                ),
                None,
            )
            if current is None:
                return {"status": "NO_LEDGER_ROW"}

            current_session = str(milking_session).upper()
            current_payload = {
                "animal_id": str(animal_id),
                "production_date": production_date,
                "session_ledger": True,
                "status": current.status,
                "morning_yield": current.morning_yield,
                "afternoon_yield": current.afternoon_yield,
                "evening_yield": current.evening_yield,
                "total_yield": current.total_yield,
            }

            if current_session not in expected:
                self._finding(
                    rf,
                    severity="HIGH",
                    title=f"Unscheduled milking session for {animal_id}",
                    detail=(
                        f"{current_session} was entered on {production_date.isoformat()} "
                        f"but the animal is governed at {frequency}."
                    ),
                    subject_id=str(animal_id),
                    dedupe_key=f"MILK_UNSCHEDULED_SESSION:{animal_id}:{production_date.isoformat()}:{current_session}",
                )
                return {"status": "UNSCHEDULED_SESSION", "frequency": frequency}

            index = SESSION_ORDER[current_session]
            earlier_expected = [session for session in expected if SESSION_ORDER[session] < index]
            earlier_missing = [
                session for session in earlier_expected
                if session in missing_sessions(current_payload, frequency)
            ]

            if earlier_missing:
                self._finding(
                    rf,
                    severity="HIGH",
                    title=f"Missed milk yield interval for {animal_id}",
                    detail=(
                        f"A {current_session} yield was entered for {production_date.isoformat()} "
                        f"while the earlier scheduled interval(s) {', '.join(earlier_missing)} "
                        "remain unentered."
                    ),
                    subject_id=str(animal_id),
                    dedupe_key=f"MILK_MISSED_INTERVAL:{animal_id}:{production_date.isoformat()}",
                )

            records = [
                {
                    "animal_id": str(row.animal_id),
                    "production_date": row.production_date,
                    "session_ledger": bool(row.session_ledger),
                    "status": row.status,
                    "morning_yield": row.morning_yield,
                    "afternoon_yield": row.afternoon_yield,
                    "evening_yield": row.evening_yield,
                    "total_yield": row.total_yield,
                }
                for row in rows
            ]

            comparison = detect_drop(
                records,
                animal_id=str(animal_id),
                session=current_session,
                as_of_date=production_date,
                milking_frequency=frequency,
            )

            if comparison and comparison.get("severity"):
                self._finding(
                    rf,
                    severity=comparison["severity"],
                    title=(
                        f"{animal_id} milk yield declined on "
                        f"{production_date.isoformat()}"
                    ),
                    detail=(
                        f"{comparison['previous_date']}: {comparison['previous']:.1f} L -> "
                        f"{comparison['current_date']}: {comparison['current']:.1f} L "
                        f"({abs(comparison['percent']):.1f}% decline)."
                    ),
                    subject_id=str(animal_id),
                    dedupe_key=f"MILK_DAILY_DROP:{animal_id}",
                )

            return {
                "status": comparison.get("status") if comparison else "NO_COMPARISON",
                "comparison": comparison,
                "missing_intervals": earlier_missing,
            }
        finally:
            rf.close()

    @staticmethod
    def _finding(
        rf,
        *,
        severity: str,
        title: str,
        detail: str,
        dedupe_key: str,
        subject_id: str | None = None,
    ):
        return MilkFindingService(rf.operational_findings()).raise_or_update(
            severity=severity,
            title=title,
            detail=detail,
            subject_type="ANIMAL" if subject_id else "FARM",
            subject_id=subject_id or "MILK",
            route=f"/farm/animals/{subject_id}" if subject_id else "/farm/milk",
            dedupe_key=dedupe_key,
        )


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])
