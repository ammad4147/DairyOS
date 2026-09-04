from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, Iterable, Mapping

from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    is_calving,
    is_confirmed_pregnancy,
    is_dry_off,
    is_insemination,
    is_negative_pregnancy_check,
    normalize_event_type,
)


@dataclass(frozen=True)
class ReproductivePolicy:
    """Farm-configurable reproductive calculation policy."""

    voluntary_waiting_period_days: int
    gestation_days: int
    dry_off_days_before_calving: int

    def __post_init__(self) -> None:
        if self.voluntary_waiting_period_days < 0:
            raise ValueError("voluntary_waiting_period_days must be non-negative")
        if self.gestation_days <= 0:
            raise ValueError("gestation_days must be greater than zero")
        if self.dry_off_days_before_calving < 0:
            raise ValueError("dry_off_days_before_calving must be non-negative")


@dataclass(frozen=True)
class ReproductiveState:
    animal_id: str
    as_of_date: date
    reproductive_status: str
    last_calving_date: date | None
    lactation_number: int
    days_in_milk: int | None
    voluntary_waiting_period_end: date | None
    eligible_to_breed: bool
    last_insemination_date: date | None
    pregnancy_status: str
    pregnancy_confirmed_date: date | None
    expected_calving_date: date | None
    days_open: int | None
    expected_dry_off_date: date | None
    dry_period_status: str


class ReproductiveStateError(ValueError):
    """Raised when reproductive events cannot form a valid state."""


class ReproductiveStateService:
    """Resolve current reproductive state exclusively from persisted farm facts.

    No benchmark, default pregnancy, implicit service, or projected status is
    allowed to become an operational fact.
    """

    def __init__(self, policy: ReproductivePolicy):
        self.policy = policy

    @staticmethod
    def _value(event: Mapping[str, Any] | Any, key: str, default=None):
        if isinstance(event, Mapping):
            return event.get(key, default)
        return getattr(event, key, default)

    @classmethod
    def _as_date(cls, value: Any) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if hasattr(value, "date"):
            converted = value.date()
            if isinstance(converted, date):
                return converted
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError(f"Unsupported date value: {value!r}")

    @classmethod
    def _normalize_event(cls, event: Mapping[str, Any] | Any) -> dict[str, Any]:
        animal_id = str(cls._value(event, "animal_id", "")).strip()
        if not animal_id:
            raise ReproductiveStateError("Reproductive event requires animal_id")

        event_type = normalize_event_type(cls._value(event, "event_type", ""))
        if not event_type:
            raise ReproductiveStateError("Reproductive event requires event_type")

        raw_event_date = cls._value(event, "event_date", None)
        raw_timestamp = cls._value(event, "timestamp", None)

        if raw_event_date is None and raw_timestamp is None:
            raise ReproductiveStateError(
                "Reproductive event requires event_date or timestamp"
            )

        event_date_source = (
            raw_event_date
            if raw_event_date is not None
            else raw_timestamp
        )

        timestamp = None
        if raw_timestamp is not None:
            if isinstance(raw_timestamp, datetime):
                timestamp = raw_timestamp
            elif isinstance(raw_timestamp, date):
                timestamp = datetime.combine(
                    raw_timestamp,
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                )
            elif isinstance(raw_timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(
                        raw_timestamp.replace("Z", "+00:00")
                    )
                except ValueError as exc:
                    raise ReproductiveStateError(
                        f"Invalid reproductive event timestamp: {raw_timestamp!r}"
                    ) from exc
            else:
                raise ReproductiveStateError(
                    f"Unsupported reproductive event timestamp: {raw_timestamp!r}"
                )

            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            else:
                timestamp = timestamp.astimezone(timezone.utc)

        return {
            "animal_id": animal_id,
            "event_type": event_type,
            "result": cls._value(event, "result", None),
            "technician": cls._value(event, "technician", None),
            "event_date": cls._as_date(event_date_source),
            "timestamp": timestamp,
            "record_id": cls._value(event, "record_id", "") or "",
            "expected_calving_date": cls._value(
                event,
                "expected_calving_date",
                None,
            ),
            "confirmed": cls._value(event, "confirmed", None),
        }

    @staticmethod
    def _classifier_record(event: Mapping[str, Any]) -> SimpleNamespace:
        timestamp = event.get("timestamp")
        if timestamp is None:
            timestamp = datetime.combine(
                event["event_date"],
                datetime.min.time(),
                tzinfo=timezone.utc,
            )
        return SimpleNamespace(
            animal_id=event["animal_id"],
            event_type=event["event_type"],
            result=event["result"],
            technician=event["technician"],
            timestamp=timestamp,
        )

    def _events_for_animal(
        self,
        events: Iterable[Mapping[str, Any] | Any],
        animal_id: str,
        as_of_date: date,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for raw_event in events:
            event = self._normalize_event(raw_event)
            if event["animal_id"] != animal_id:
                continue
            if event["event_date"] > as_of_date:
                continue
            normalized.append(event)
        normalized.sort(
            key=lambda event: (
                event["timestamp"] is None,
                event["timestamp"] or datetime.max.replace(tzinfo=timezone.utc),
                event["event_date"],
                event["record_id"],
            )
        )
        return normalized

    @staticmethod
    def _latest(events: Iterable[Mapping[str, Any]], predicate):
        matches = [
            event
            for event in events
            if predicate(ReproductiveStateService._classifier_record(event))
        ]
        return matches[-1] if matches else None

    @staticmethod
    def _is_positive_pregnancy_event(event: Mapping[str, Any]) -> bool:
        return is_confirmed_pregnancy(ReproductiveStateService._classifier_record(event))

    @staticmethod
    def _is_negative_pregnancy_event(event: Mapping[str, Any]) -> bool:
        return is_negative_pregnancy_check(ReproductiveStateService._classifier_record(event))

    def _validate_sequence(
        self,
        events: list[dict[str, Any]],
        *,
        allow_unlinked_confirmation: bool = False,
    ) -> None:
        pregnant = False
        last_insemination: date | None = None

        for event in events:
            event_type = normalize_event_type(event["event_type"])
            event_date = event["event_date"]
            classifier_record = self._classifier_record(event)

            if is_calving(classifier_record):
                pregnant = False
                last_insemination = None
                continue

            if is_insemination(classifier_record):
                if pregnant:
                    raise ReproductiveStateError(
                        "INSEMINATION cannot occur while pregnancy is operationally active"
                    )
                last_insemination = event_date
                continue

            if self._is_positive_pregnancy_event(event):
                if last_insemination is None:
                    if not allow_unlinked_confirmation:
                        raise ReproductiveStateError(
                            "PREGNANCY_CONFIRMED requires a prior INSEMINATION event"
                        )
                elif event_date < last_insemination:
                    raise ReproductiveStateError(
                        "Pregnancy confirmation cannot precede insemination"
                    )
                pregnant = True
                continue

            if event_type == "pregnancy_lost":
                if not pregnant:
                    raise ReproductiveStateError(
                        "PREGNANCY_LOST requires an active pregnancy"
                    )
                pregnant = False
                continue

            if event_type in {"abortion", "stillbirth"}:
                if not pregnant:
                    raise ReproductiveStateError(
                        f"{event_type.upper()} requires an active pregnancy"
                    )
                pregnant = False
                continue

            if self._is_negative_pregnancy_event(event):
                pregnant = False
                continue

            if is_dry_off(classifier_record):
                if not any(
                    is_calving(self._classifier_record(previous))
                    and previous["event_date"] <= event_date
                    for previous in events
                ):
                    raise ReproductiveStateError("DRY_OFF requires a prior CALVING event")

    @staticmethod
    def _current_cycle(events: list[dict[str, Any]]):
        calvings = [
            event
            for event in events
            if is_calving(ReproductiveStateService._classifier_record(event))
        ]
        last_calving = calvings[-1] if calvings else None
        if last_calving is None:
            return events, None
        return [
            event
            for event in events
            if event["event_date"] > last_calving["event_date"]
        ], last_calving

    def resolve(
        self,
        animal_id: str,
        events: Iterable[Mapping[str, Any] | Any],
        *,
        as_of_date: date,
        allow_unlinked_confirmation: bool = False,
    ) -> ReproductiveState:
        as_of_date = self._as_date(as_of_date)
        animal_events = self._events_for_animal(events, animal_id, as_of_date)
        self._validate_sequence(
            animal_events,
            allow_unlinked_confirmation=allow_unlinked_confirmation,
        )
        current_events, last_calving_event = self._current_cycle(animal_events)

        last_calving_date = (
            last_calving_event["event_date"] if last_calving_event else None
        )
        lactation_number = sum(
            1
            for event in animal_events
            if is_calving(self._classifier_record(event))
        )
        days_in_milk = (
            (as_of_date - last_calving_date).days
            if last_calving_date is not None
            else None
        )
        vwp_end = (
            last_calving_date + timedelta(days=self.policy.voluntary_waiting_period_days)
            if last_calving_date is not None
            else None
        )

        inseminations = [
            event
            for event in current_events
            if is_insemination(self._classifier_record(event))
        ]
        last_insemination = inseminations[-1] if inseminations else None
        last_insemination_date = (
            last_insemination["event_date"] if last_insemination else None
        )

        pregnancy_status = "NOT_PREGNANT"
        latest_pregnancy: dict[str, Any] | None = None
        latest_state_event: dict[str, Any] | None = None

        for event in current_events:
            classifier_record = self._classifier_record(event)
            event_type = normalize_event_type(event["event_type"])
            if is_insemination(classifier_record):
                latest_state_event = event
            elif self._is_positive_pregnancy_event(event):
                pregnancy_status = "PREGNANT"
                latest_pregnancy = event
                latest_state_event = event
            elif self._is_negative_pregnancy_event(event):
                pregnancy_status = "NOT_PREGNANT"
                latest_pregnancy = None
                latest_state_event = event
            elif event_type in {"pregnancy_lost", "abortion", "stillbirth"}:
                pregnancy_status = "NOT_PREGNANT"
                latest_pregnancy = None
                latest_state_event = event
            elif is_dry_off(classifier_record):
                latest_state_event = event
            elif is_calving(classifier_record):
                pregnancy_status = "NOT_PREGNANT"
                latest_pregnancy = None
                latest_state_event = event

        pregnancy_confirmed_date = (
            latest_pregnancy["event_date"]
            if pregnancy_status == "PREGNANT" and latest_pregnancy is not None
            else None
        )

        expected_calving_date: date | None = None
        if pregnancy_status == "PREGNANT" and latest_pregnancy is not None:
            configured = latest_pregnancy.get("expected_calving_date")
            if configured:
                expected_calving_date = self._as_date(configured)
            elif last_insemination_date is not None:
                expected_calving_date = last_insemination_date + timedelta(
                    days=self.policy.gestation_days
                )

        days_open = None
        if pregnancy_status == "PREGNANT" and last_calving_date is not None:
            successful_service = last_insemination_date
            if successful_service is not None:
                days_open = (successful_service - last_calving_date).days

        expected_dry_off_date = (
            expected_calving_date - timedelta(days=self.policy.dry_off_days_before_calving)
            if expected_calving_date is not None
            else None
        )
        dry_period_status = "NOT_PLANNED"
        if expected_dry_off_date is not None:
            dry_period_status = "DUE_OR_ACTIVE" if as_of_date >= expected_dry_off_date else "NOT_DUE"

        if pregnancy_status == "PREGNANT":
            reproductive_status = "PREGNANT"
        elif latest_state_event is not None:
            latest_type = normalize_event_type(latest_state_event["event_type"])
            if latest_type in {"pregnancy_negative", "pregnancy_lost", "abortion", "stillbirth"}:
                # A negative diagnosis or recorded pregnancy loss closes the
                # preceding insemination cycle. The historical insemination
                # remains in the ledger, but it must not keep the animal in
                # the operational INSEMINATED/BRED queue.
                reproductive_status = "OPEN"
            elif is_insemination(self._classifier_record(latest_state_event)):
                reproductive_status = "BRED"
            elif is_dry_off(self._classifier_record(latest_state_event)):
                reproductive_status = "DRY_OFF"
            elif is_calving(self._classifier_record(latest_state_event)):
                reproductive_status = "LACTATING"
            else:
                reproductive_status = "OPEN"
        elif last_calving_date is not None:
            reproductive_status = "LACTATING"
        else:
            reproductive_status = "OPEN"

        eligible_to_breed = (
            pregnancy_status != "PREGNANT"
            and (vwp_end is None or as_of_date >= vwp_end)
        )

        return ReproductiveState(
            animal_id=animal_id,
            as_of_date=as_of_date,
            reproductive_status=reproductive_status,
            last_calving_date=last_calving_date,
            lactation_number=lactation_number,
            days_in_milk=days_in_milk,
            voluntary_waiting_period_end=vwp_end,
            eligible_to_breed=eligible_to_breed,
            last_insemination_date=last_insemination_date,
            pregnancy_status=pregnancy_status,
            pregnancy_confirmed_date=pregnancy_confirmed_date,
            expected_calving_date=expected_calving_date,
            days_open=days_open,
            expected_dry_off_date=expected_dry_off_date,
            dry_period_status=dry_period_status,
        )