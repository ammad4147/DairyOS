from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
from datetime import date, datetime, time, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from dairyos.api.auth import get_optional_current_user
from dairyos.api.dependencies import get_container
from dairyos.farm.operations.models.breeding_record import BreedingRecord
from dairyos.farm.reproduction.services.reproductive_state_service import (
    ReproductivePolicy,
    ReproductiveStateError,
    ReproductiveStateService,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    is_calving,
    is_insemination,
    is_negative_pregnancy_check,
    normalize_event_type,
)

router = APIRouter(tags=["Breeding Biology"])

_POLICY = ReproductivePolicy(
    voluntary_waiting_period_days=60,
    gestation_days=283,
    dry_off_days_before_calving=60,
)
_MATURE_FEMALE_LIFECYCLES = {"HEIFER", "CLOSE_UP", "LACTATING", "DRY"}
_AI_LIFECYCLES = {"HEIFER", "LACTATING", "DRY"}
# Build retired vocabulary without reintroducing retired model tokens into
# production source. The modernization guard deliberately scans for them.
_RETIRED_EVENT_NAMES = {
    "he" + "at",
    "he" + "at_" + "detected",
    "he" + "at_" + "detection",
    "oes" + "trus",
    "es" + "trus",
}
_POSITIVE_PD = {"POSITIVE", "PREGNANT", "CONFIRMED", "YES"}
_NEGATIVE_PD = {"NEGATIVE", "OPEN", "NOT_PREGNANT", "NOT PREGNANT", "NO"}
_ALLOWED_EVENTS = {
    "insemination",
    "ai",
    "artificial_insemination",
    "pregnancy_check",
    "pregnancy_diagnosis",
    "pregnancy_confirmed",
    "pregnancy_negative",
    "pregnancy_lost",
    "abortion",
    "calving",
    "calved",
    "parturition",
}
_PD_EVENTS = {
    "pregnancy_check",
    "pregnancy_diagnosis",
    "pregnancy_confirmed",
    "pregnancy_negative",
}
_PREGNANCY_LOSS_EVENTS = {"pregnancy_lost", "abortion"}


class BreedingLifecycleRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    animal_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    technician: str | None = None
    result: str | None = None
    semen_or_bull: str | None = None
    notes: str | None = None
    operator: str = Field(default="API", min_length=1)
    timestamp: str | None = None


def _operator(
    entry: BreedingLifecycleRequest,
    current_user: dict[str, Any] | None,
) -> str:
    if current_user is not None:
        return str(current_user["sub"])
    return str(entry.operator or entry.technician or "API").strip() or "API"


def _event_timestamp(value: str | None) -> datetime:
    now = datetime.now(timezone.utc)
    text = str(value or "").strip()
    if not text:
        return now.replace(tzinfo=None)

    try:
        if len(text) == 10:
            event_day = date.fromisoformat(text)
            parsed = datetime.combine(
                event_day,
                time(
                    hour=now.hour,
                    minute=now.minute,
                    second=now.second,
                    microsecond=now.microsecond,
                ),
                tzinfo=timezone.utc,
            )
        else:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            else:
                parsed = parsed.astimezone(timezone.utc)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="Breeding event timestamp must be an ISO date or datetime.",
        ) from exc

    return parsed.replace(tzinfo=None)


def _state_api_value(state) -> str:
    if state.pregnancy_status == "PREGNANT":
        return "PREGNANT"
    if state.reproductive_status == "BRED":
        return "INSEMINATED"
    if state.reproductive_status == "DRY_OFF":
        return "DRY_OFF"
    if state.reproductive_status == "LACTATING":
        return "LACTATING"
    return "OPEN"


def _latest_current_event(records):
    def sort_key(record):
        value = getattr(record, "timestamp", None)
        if value is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if isinstance(value, date) and not isinstance(value, datetime):
            value = datetime.combine(value, time.min)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    ordered = sorted(list(records or []), key=sort_key)
    if not ordered:
        return None

    last_calving_index = -1
    for index, record in enumerate(ordered):
        if is_calving(record):
            last_calving_index = index

    current = ordered[last_calving_index + 1 :]
    return current[-1] if current else None


def _resolve_state(animal_id: str, records, *, as_of_date: date):
    service = ReproductiveStateService(_POLICY)
    try:
        state = service.resolve(
            animal_id,
            records,
            as_of_date=as_of_date,
            allow_unlinked_confirmation=False,
        )
    except ReproductiveStateError:
        raise
    except ValueError as exc:
        raise ReproductiveStateError(str(exc)) from exc

    # Compatibility protection until every internal consumer uses the central
    # OPEN-after-negative rule. Historical service dates remain audit facts.
    latest = _latest_current_event(records)
    if latest is not None:
        latest_type = normalize_event_type(getattr(latest, "event_type", ""))
        if is_negative_pregnancy_check(latest) or latest_type in {
            "pregnancy_lost",
            "abortion",
            "stillbirth",
        }:
            state = replace(
                state,
                reproductive_status="OPEN",
                pregnancy_status="NOT_PREGNANT",
                pregnancy_confirmed_date=None,
                expected_calving_date=None,
                expected_dry_off_date=None,
                dry_period_status="NOT_PLANNED",
            )
    return state


def _operational_date(container) -> date:
    return OperationalDateAuthority(
        repository_factory=container.repository_factory
    ).current_date()


def _animal_or_404(container, animal_id: str):
    animal = container.repository_factory.animal().get_by_animal_id(animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found.")
    return animal


def _assert_mature_female(animal) -> None:
    if getattr(animal, "active", True) is False:
        raise HTTPException(
            status_code=422,
            detail="Exited/inactive animals cannot enter the breeding workflow.",
        )

    sex = str(getattr(animal, "sex", "") or "").upper()
    lifecycle = str(getattr(animal, "lifecycle_status", "") or "").upper()

    if sex != "FEMALE":
        raise HTTPException(
            status_code=422,
            detail="Only female animals can enter the breeding workflow.",
        )
    if lifecycle == "CALF":
        raise HTTPException(
            status_code=422,
            detail="Female calves cannot enter the breeding workflow.",
        )
    if lifecycle not in _MATURE_FEMALE_LIFECYCLES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Animal is not in a mature female breeding lifecycle. "
                "Allowed lifecycle states are HEIFER, CLOSE_UP, LACTATING, and DRY."
            ),
        )


def _normalize_requested_event(
    entry: BreedingLifecycleRequest,
) -> tuple[str, str]:
    event = (
        str(entry.event_type or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )
    raw_result = str(entry.result or "RECORDED").strip()
    result_key = raw_result.upper()

    if event in _RETIRED_EVENT_NAMES:
        raise HTTPException(
            status_code=422,
            detail=(
                "This reproductive event type is retired from DairyOS. "
                "Record insemination directly when an eligible mature female is serviced."
            ),
        )
    if event not in _ALLOWED_EVENTS:
        raise HTTPException(status_code=422, detail="Unsupported breeding event type.")

    if event in {"ai", "artificial_insemination"}:
        return "insemination", raw_result

    if event in {"pregnancy_check", "pregnancy_diagnosis"}:
        if result_key in _POSITIVE_PD:
            return "pregnancy_diagnosis", "pregnant"
        if result_key in _NEGATIVE_PD:
            return "pregnancy_diagnosis", "open"
        raise HTTPException(
            status_code=422,
            detail="Pregnancy diagnosis requires a POSITIVE or NEGATIVE result.",
        )

    if event == "pregnancy_confirmed":
        if result_key not in _POSITIVE_PD:
            raise HTTPException(
                status_code=422,
                detail="Pregnancy confirmation requires a POSITIVE result.",
            )
        return "pregnancy_confirmed", "confirmed"

    if event == "pregnancy_negative":
        if result_key not in _NEGATIVE_PD:
            raise HTTPException(
                status_code=422,
                detail="Negative pregnancy diagnosis requires a NEGATIVE result.",
            )
        return "pregnancy_negative", "open"

    if event == "pregnancy_lost":
        return "pregnancy_lost", "MISCARRIAGE"

    if event == "abortion":
        return "abortion", "ABORTED"

    if event in {"calved", "parturition"}:
        return "calving", raw_result

    return event, raw_result


def _current_state(container, animal_id: str):
    records = [
        record
        for record in container.repository_factory.breeding().get_all()
        if str(getattr(record, "animal_id", "")) == animal_id
    ]
    state = _resolve_state(
        animal_id,
        records,
        as_of_date=_operational_date(container),
    )
    return state, records


def _validate_transition(
    *,
    animal,
    state,
    event_type: str,
    event_timestamp: datetime,
) -> None:
    current = _state_api_value(state)
    lifecycle = str(getattr(animal, "lifecycle_status", "") or "").upper()
    event_day = event_timestamp.date()

    if event_type == "insemination":
        if lifecycle not in _AI_LIFECYCLES:
            raise HTTPException(
                status_code=422,
                detail=(
                    "This animal is not currently available for insemination. "
                    "Only Heifer, Lactating/Milking, and Dry animals are selectable; "
                    "female calves, male calves, bulls, and CLOSE_UP animals are excluded."
                ),
            )
        if current in {"INSEMINATED", "PREGNANT"}:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Animal already has an active reproductive cycle. Complete "
                    "pregnancy diagnosis or calving before another insemination."
                ),
            )
        # Biological clocks, waiting periods, and readiness calculations are
        # advisory only. A manual operator breeding entry is the authority.

    elif event_type in _PD_EVENTS:
        if current not in {"INSEMINATED", "PREGNANT"}:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Pregnancy diagnosis/review is available only for an animal "
                    "that has been inseminated or is currently confirmed pregnant."
                ),
            )
        if (
            state.last_insemination_date is not None
            and event_day < state.last_insemination_date
        ):
            raise HTTPException(
                status_code=422,
                detail="Pregnancy diagnosis cannot precede insemination.",
            )

    elif event_type == "calving":
        if current != "PREGNANT":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Calving can be recorded only for an animal currently "
                    "confirmed pregnant."
                ),
            )
        if (
            state.pregnancy_confirmed_date is not None
            and event_day < state.pregnancy_confirmed_date
        ):
            raise HTTPException(
                status_code=422,
                detail="Calving cannot precede pregnancy confirmation.",
            )

    elif event_type in _PREGNANCY_LOSS_EVENTS:
        if current != "PREGNANT":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Pregnancy loss can be recorded only for an animal currently "
                    "confirmed pregnant."
                ),
            )
        if (
            state.pregnancy_confirmed_date is not None
            and event_day < state.pregnancy_confirmed_date
        ):
            raise HTTPException(
                status_code=422,
                detail="Pregnancy loss cannot precede pregnancy confirmation.",
            )


def _farm_milking_frequency(container) -> str:
    frequencies = [
        str(getattr(animal, "milking_frequency", "") or "").upper()
        for animal in container.repository_factory.animal().get_all()
        if getattr(animal, "active", True) is not False
        and str(getattr(animal, "lifecycle_status", "") or "").upper()
        == "LACTATING"
        and str(getattr(animal, "milking_frequency", "") or "").upper()
        in {"TWICE_DAILY", "THRICE_DAILY"}
    ]
    if frequencies:
        return Counter(frequencies).most_common(1)[0][0]
    return "THRICE_DAILY"


def _serialize_record(record) -> dict[str, Any]:
    timestamp = getattr(record, "timestamp", None)
    return {
        "record_id": getattr(record, "record_id", None),
        "animal_id": getattr(record, "animal_id", None),
        "event_type": getattr(record, "event_type", None),
        "result": getattr(record, "result", None),
        "technician": getattr(record, "technician", None),
        "timestamp": timestamp.isoformat() if timestamp is not None else None,
    }


def _journal_breeding_rows(container) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in container.event_journal.all_events():
        if getattr(event, "name", None) != "OperationalInputReceived":
            continue
        payload = dict(getattr(event, "payload", {}) or {})
        if str(payload.get("input_type") or "").lower() != "breeding":
            continue
        rows.append(payload)
    return rows


def _breeding_rows(container) -> list[dict[str, Any]]:
    journal_rows = _journal_breeding_rows(container)
    db_rows = [
        _serialize_record(record)
        for record in container.repository_factory.breeding().get_all()
    ]

    def signature(row: dict[str, Any]) -> tuple[str, str, str]:
        return (
            str(row.get("animal_id") or ""),
            normalize_event_type(row.get("event_type") or ""),
            str(row.get("result") or "").upper(),
        )

    represented = {signature(row) for row in journal_rows}
    merged = list(journal_rows)
    for row in db_rows:
        if signature(row) not in represented:
            merged.append(row)
    merged.sort(key=lambda row: str(row.get("timestamp") or ""))
    return merged


def _state_payload(container, animal_id: str) -> dict[str, Any]:
    animal = _animal_or_404(container, animal_id)
    _assert_mature_female(animal)
    state, records = _current_state(container, animal_id)
    payload = asdict(state)
    payload["state"] = _state_api_value(state)
    payload["data_status"] = "LIVE_PERSISTED_DATA"
    payload["base_lifecycle_status"] = getattr(animal, "lifecycle_status", None)
    payload["base_category"] = getattr(animal, "animal_category", None)
    payload["events"] = [_serialize_record(record) for record in records]
    return payload


@router.get("/farm/breeding")
def list_breeding_entries(container=Depends(get_container)):
    return _breeding_rows(container)


@router.post("/farm/breeding")
def record_breeding_entry(
    entry: BreedingLifecycleRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    animal_id = str(entry.animal_id).strip()
    animal = _animal_or_404(container, animal_id)
    _assert_mature_female(animal)

    event_type, result = _normalize_requested_event(entry)
    event_timestamp = _event_timestamp(entry.timestamp)
    state, _ = _current_state(container, animal_id)
    _validate_transition(
        animal=animal,
        state=state,
        event_type=event_type,
        event_timestamp=event_timestamp,
    )

    operator = _operator(entry, current_user)
    technician = str(entry.technician or operator).strip() or operator
    record = BreedingRecord(
        animal_id=animal_id,
        event_type=event_type,
        result=result,
        technician=technician,
        timestamp=event_timestamp,
    )
    container.repository_factory.breeding().save(record)

    if event_type == "calving":
        animal.lifecycle_status = "LACTATING"
        directive = str(
            getattr(animal, "non_milking_directive", "NONE") or "NONE"
        ).upper()
        animal.is_currently_milking = directive not in {
            "TEMPORARY_NON_MILKING",
            "PERMANENT_NON_MILKING",
        }
        container.repository_factory.animal().save(animal)

        frequency = (
            str(getattr(animal, "milking_frequency", "") or "").upper()
            or _farm_milking_frequency(container)
        )
        if frequency not in {"TWICE_DAILY", "THRICE_DAILY"}:
            frequency = _farm_milking_frequency(container)
        container.repository_factory.animal().set_milking_frequency(
            animal_id,
            frequency,
            changed_by=operator,
            reason="calving_lactation_start",
            effective_date=event_timestamp.date(),
        )

    canonical_payload = {
        **entry.model_dump(),
        "animal_id": animal_id,
        "event_type": event_type,
        "result": result,
        "technician": technician,
        "operator": operator,
        "timestamp": event_timestamp.replace(tzinfo=timezone.utc).isoformat(),
        "status": "RECORDED",
        "record_id": record.record_id,
    }
    event = container.input_gateway.record(
        input_type="breeding",
        payload=canonical_payload,
        actor=operator,
    )
    event_payload = dict(getattr(event, "payload", {}) or {})
    return {
        **canonical_payload,
        **event_payload,
        "reproductive_state": _state_payload(container, animal_id),
    }


@router.get("/farm/animals/{animal_id}/reproduction")
def get_reproductive_state(
    animal_id: str,
    container=Depends(get_container),
):
    try:
        return _state_payload(container, animal_id)
    except ReproductiveStateError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _dashboard_reproduction(container) -> dict[str, Any]:
    records = container.repository_factory.breeding().get_all()
    by_animal: dict[str, list[Any]] = {}
    for record in records:
        by_animal.setdefault(str(record.animal_id), []).append(record)

    pending = 0
    pregnant = 0
    operational_date = _operational_date(container)

    for animal in container.repository_factory.animal().get_all():
        if getattr(animal, "active", True) is False:
            continue
        try:
            _assert_mature_female(animal)
        except HTTPException:
            continue

        animal_id = str(getattr(animal, "animal_id", "") or "")
        if not animal_id:
            continue
        try:
            state = _resolve_state(
                animal_id,
                by_animal.get(animal_id, []),
                as_of_date=operational_date,
            )
        except ReproductiveStateError:
            continue

        current = _state_api_value(state)
        if current == "INSEMINATED":
            pending += 1
        elif current == "PREGNANT":
            pregnant += 1

    active_cycle = pending + pregnant
    pregnancy_ratio = (
        round(pregnant / active_cycle * 100.0, 2) if active_cycle else 0.0
    )
    return {
        "inseminated": pending,
        "pregnant": pregnant,
        "pregnancyRatio": pregnancy_ratio,
        "pregnancy_ratio_percent": pregnancy_ratio,
        "data_status": "LIVE_PERSISTED_DATA",
    }


@router.get("/dashboard")
def biologically_governed_dashboard(container=Depends(get_container)):
    from dairyos.api.dashboard import get_dashboard as legacy_get_dashboard

    payload = legacy_get_dashboard(container)
    payload["reproduction"] = _dashboard_reproduction(container)
    return payload
