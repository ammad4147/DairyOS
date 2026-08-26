from dataclasses import dataclass
from datetime import date, datetime, timezone

from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    is_confirmed_pregnancy,
)


@dataclass
class ReproductionKpiSummary:
    animal_id: str
    calving_interval_days: float | None = None
    days_open: int | None = None
    services_per_conception: float = 0.0
    conception_rate_pct: float = 0.0
    status: str = "NORMAL"


class ReproductionKpiService:
    """Authoritative reproductive KPI calculations.

    KPI calculations that depend on breeding outcomes use the same observed
    outcome rule everywhere in DairyOS: an insemination enters the conception
    denominator only when a subsequent persisted pregnancy diagnosis is
    available for that service. Multiple diagnoses for one service update the
    same service outcome and never create multiple conceptions.
    """

    @staticmethod
    def _as_utc(value: datetime | date | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)

    @classmethod
    def conception_outcomes(cls, inseminations, pregnancy_checks) -> dict[str, bool]:
        """Return one observed pregnancy outcome per service.

        The latest diagnosis chronologically associated with a service is the
        authoritative observed outcome for that service. A diagnosis cannot
        match a service from another animal, and undated records are excluded
        because they cannot establish chronology.
        """
        ordered_inseminations = sorted(
            [
                record
                for record in inseminations
                if cls._as_utc(getattr(record, "timestamp", None)) is not None
            ],
            key=lambda record: cls._as_utc(getattr(record, "timestamp", None)),
        )
        ordered_checks = sorted(
            [
                record
                for record in pregnancy_checks
                if cls._as_utc(getattr(record, "timestamp", None)) is not None
            ],
            key=lambda record: cls._as_utc(getattr(record, "timestamp", None)),
        )

        outcomes: dict[str, bool] = {}
        for check in ordered_checks:
            check_time = cls._as_utc(getattr(check, "timestamp", None))
            candidates = [
                record
                for record in ordered_inseminations
                if getattr(record, "animal_id", None) == getattr(check, "animal_id", None)
                and cls._as_utc(getattr(record, "timestamp", None)) <= check_time
            ]
            if not candidates:
                continue
            matched = candidates[-1]
            key = str(getattr(matched, "record_id", id(matched)))
            outcomes[key] = is_confirmed_pregnancy(check)
        return outcomes

    @classmethod
    def confirmed_pregnancy_count(
        cls,
        inseminations,
        pregnancy_checks,
        confirmation_events=(),
    ) -> int:
        """Count unique observed pregnancy confirmations.

        A positive pregnancy diagnosis and a later ``pregnancy_confirmed``
        event for the same service represent one conception. Standalone
        ``pregnancy_confirmed`` evidence is still counted once when no service
        can be associated with it. This keeps historical observation counts
        useful without allowing repeated positive checks to inflate
        conceptions.
        """
        ordered_services = [
            record
            for record in inseminations
            if cls._as_utc(getattr(record, "timestamp", None)) is not None
        ]
        outcomes = cls.conception_outcomes(ordered_services, pregnancy_checks)
        confirmed = sum(1 for value in outcomes.values() if value)
        matched_service_ids = set(outcomes)

        for event in confirmation_events:
            if not is_confirmed_pregnancy(event):
                continue
            event_time = cls._as_utc(getattr(event, "timestamp", None))
            if event_time is None:
                continue
            candidates = [
                service
                for service in ordered_services
                if getattr(service, "animal_id", None) == getattr(event, "animal_id", None)
                and cls._as_utc(getattr(service, "timestamp", None)) <= event_time
            ]
            if candidates and str(getattr(candidates[-1], "record_id", id(candidates[-1]))) in matched_service_ids:
                continue
            confirmed += 1

        return confirmed

    @classmethod
    def calculate_observed_conception_rate(cls, inseminations, pregnancy_checks) -> float | None:
        """Calculate conception rate from services with documented outcomes."""
        outcomes = cls.conception_outcomes(inseminations, pregnancy_checks)
        if not outcomes:
            return None
        return round((sum(outcomes.values()) / len(outcomes)) * 100, 2)

    @staticmethod
    def calculate_calving_interval(
        previous_calving_date: date | datetime,
        current_calving_date: date | datetime,
    ) -> int:
        if isinstance(previous_calving_date, datetime):
            previous_calving_date = previous_calving_date.date()
        if isinstance(current_calving_date, datetime):
            current_calving_date = current_calving_date.date()
        return (current_calving_date - previous_calving_date).days

    @staticmethod
    def calculate_days_open(
        last_calving_date: date | datetime,
        conception_date: date | datetime,
    ) -> int:
        if isinstance(last_calving_date, datetime):
            last_calving_date = last_calving_date.date()
        if isinstance(conception_date, datetime):
            conception_date = conception_date.date()
        return (conception_date - last_calving_date).days

    @staticmethod
    def calculate_conception_rate(
        confirmed_pregnancies: int,
        total_inseminations: int,
    ) -> float:
        """Legacy count-based arithmetic retained for compatibility.

        Persisted-record KPI paths must use
        :meth:`calculate_observed_conception_rate`, which prevents services
        without a documented pregnancy outcome from entering the denominator.
        """
        if total_inseminations == 0:
            return 0.0
        return round((confirmed_pregnancies / total_inseminations) * 100, 2)

    @staticmethod
    def calculate_services_per_conception(
        total_inseminations: int,
        total_conceptions: int,
    ) -> float:
        if total_conceptions == 0:
            return 0.0
        return round(total_inseminations / total_conceptions, 2)
