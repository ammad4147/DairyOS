from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from dairyos.api.dependencies import get_container
from dairyos.api.operational_write import operational_write
from dairyos.api.reference_data import GOVERNED
from dairyos.finance.clinical_inventory import record_clinical_consumption
from dairyos.data.models.vaccination_record import VaccinationRecord
from dairyos.farm.herd.services.animal_classification_service import (
    AnimalClassificationError,
    AnimalClassificationService,
)
from dairyos.farm.herd.services.animal_parentage_service import (
    AnimalParentageError,
    validate_parentage,
)
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService

router = APIRouter()

ALLOWED_LIFECYCLE_STATUSES = set(GOVERNED["lifecycle_statuses"])
ALLOWED_MILKING_FREQUENCIES = set(GOVERNED["milking_frequencies"])
EXIT_STATUSES = {"SOLD", "DECEASED"}
TERMINAL_LIFECYCLE_STATUSES = {"SOLD", "CULLED", "DECEASED"}


def animal_repository(container):
    return container.animal_repository


def _farm_operational_date(container):
    """Resolve a default date from Settings, falling back to Windows local time."""
    try:
        return FarmSettingsService(
            container.repository_factory.app_settings()
        ).get_operational_date()
    except (AttributeError, ImportError, TypeError, ValueError):
        return datetime.now().astimezone().date()


def serialize_animal(animal):
    if animal is None:
        return None
    is_milking = bool(animal.is_currently_milking)
    result = {
        "id": animal.id,
        "animal_id": animal.animal_id,
        "animal_type": animal.animal_type,
        "legacy_animal_id": getattr(animal, "legacy_animal_id", None),
        "ear_tag": animal.ear_tag,
        "rfid": animal.rfid,
        "breed": animal.breed,
        "sex": animal.sex,
        "date_of_birth": animal.date_of_birth.isoformat() if animal.date_of_birth else None,
        "date_of_acquisition": getattr(animal, "date_of_acquisition", None).isoformat() if getattr(animal, "date_of_acquisition", None) else None,
        "dam_id": getattr(animal, "dam_id", None),
        "sire_id": getattr(animal, "sire_id", None),
        "lifecycle_status": animal.lifecycle_status,
        "status": animal.status,
        "is_currently_milking": is_milking,
        "milking_frequency": animal.milking_frequency if is_milking else None,
        "production_group": animal.production_group,
        "location": animal.location,
        "photo_data": getattr(animal, "photo_data", None),
        "active": animal.active,
        "created_at": animal.created_at.isoformat() if animal.created_at else None,
        "updated_at": animal.updated_at.isoformat() if animal.updated_at else None,
    }
    try:
        classification = AnimalClassificationService.classify(
            result.get("lifecycle_status"), result.get("sex")
        )
        result["sex"] = classification.sex
        result["lifecycle_status"] = classification.lifecycle_status
        result["animal_category"] = classification.category.value
    except AnimalClassificationError:
        result["animal_category"] = None
    return result


def get_animal_record(container, animal_id):
    return animal_repository(container).get_by_animal_id(animal_id)


def _record_operational_event(container, input_type, payload, actor):
    gateway = getattr(container, "input_gateway", None)
    if gateway is not None:
        return gateway.record(
            input_type=input_type,
            payload={**payload, "timestamp": datetime.now(UTC).isoformat(), "operator": actor},
            actor=actor,
        )
    return None


def _event_payloads_for_animal(container, input_type, animal_id):
    records = []
    for event in container.event_journal.all_events():
        if (
            event.name == "OperationalInputReceived"
            and event.payload.get("input_type") == input_type
            and str(event.payload.get("animal_id")) == animal_id
        ):
            records.append(event.payload)
    return records


def _serialize_vaccination_record(record):
    return {
        "id": record.id,
        "animal_id": record.animal_id,
        "vaccine": record.vaccine,
        "dose": record.dose,
        "administered_date": (
            record.administered_date.isoformat()
            if record.administered_date else None
        ),
        "next_due_date": (
            record.next_due_date.isoformat() if record.next_due_date else None
        ),
        "schedule_status": record.schedule_status,
        "batch_number": record.batch_number,
        "veterinarian": record.veterinarian,
        "notes": record.notes,
        "operator": record.operator,
        "status": record.status,
        "source_event_id": record.source_event_id,
        "created_at": (
            record.created_at.isoformat() if record.created_at else None
        ),
    }


def _apply_classification_payload(animal, payload):
    try:
        if "animal_category" in payload or "category" in payload:
            classification = AnimalClassificationService.from_category(
                str(payload.get("animal_category") or payload.get("category")),
                current_lifecycle=payload.get("lifecycle_status") or animal.lifecycle_status,
            )
            animal.sex = classification.sex
            animal.lifecycle_status = classification.lifecycle_status
            animal.is_currently_milking = classification.lifecycle_status == "LACTATING"
            if not animal.is_currently_milking:
                animal.milking_frequency = None
            return classification

        lifecycle = payload.get("lifecycle_status", animal.lifecycle_status)
        sex = payload.get("sex", animal.sex)
        classification = AnimalClassificationService.classify(lifecycle, sex)
        animal.sex = classification.sex
        animal.lifecycle_status = classification.lifecycle_status
        animal.is_currently_milking = classification.lifecycle_status == "LACTATING"
        if not animal.is_currently_milking:
            animal.milking_frequency = None
        return classification
    except AnimalClassificationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _parse_date(value, field_name):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} must be an ISO date") from exc


def _require_text(payload: dict, field_name: str, *, source: str | None = None):
    value = str(payload.get(source or field_name) or "").strip()
    if not value:
        raise HTTPException(status_code=422, detail=f"{field_name} required")
    return value


def _validate_milking_frequency(animal, frequency):
    if frequency is None:
        return
    if not animal.is_currently_milking:
        raise HTTPException(
            status_code=422,
            detail="milking_frequency is only applicable to animals currently classified as Milking",
        )
    if frequency not in ALLOWED_MILKING_FREQUENCIES:
        raise HTTPException(
            status_code=422,
            detail="Invalid milking frequency. Allowed: " + ", ".join(sorted(ALLOWED_MILKING_FREQUENCIES)),
        )


def _validate_parentage_payload(repository, animal, payload):
    if not ({"dam_id", "sire_id", "date_of_birth"} & set(payload)):
        return
    try:
        validate_parentage(
            repository,
            child_id=animal.animal_id,
            dam_id=payload.get("dam_id", getattr(animal, "dam_id", None)),
            sire_id=payload.get("sire_id", getattr(animal, "sire_id", None)),
            child_date_of_birth=(
                _parse_date(payload.get("date_of_birth"), "date_of_birth")
                if "date_of_birth" in payload
                else getattr(animal, "date_of_birth", None)
            ),
        )
    except AnimalParentageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/animals")
def list_animals(currently_milking: bool = False, active_only: bool = False, container=Depends(get_container)):
    repository = animal_repository(container)
    if currently_milking:
        animals = repository.currently_milking_animals()
    elif active_only:
        animals = repository.active_animals()
    else:
        animals = repository.get_all()
    return [serialize_animal(animal) for animal in animals]


@router.get("/animals/current/milking")
def list_currently_milking_animals(container=Depends(get_container)):
    repository = animal_repository(container)
    return [serialize_animal(animal) for animal in repository.currently_milking_animals()]


@router.get("/animals/classification")
def classify_animal(
    category: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    sex: str | None = Query(default=None),
) -> dict[str, str]:
    """Return the canonical animal category/lifecycle/sex contract."""
    try:
        result = (
            AnimalClassificationService.from_category(
                category,
                current_lifecycle=lifecycle_status,
            )
            if category
            else AnimalClassificationService.classify(
                lifecycle_status,
                sex,
            )
        )
    except AnimalClassificationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "animal_category": result.category.value,
        "lifecycle_status": result.lifecycle_status,
        "sex": result.sex,
    }


@router.get("/animals/{animal_id}")
def get_animal(animal_id: str, container=Depends(get_container)):
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return serialize_animal(animal)


@router.patch("/animals/{animal_id}")
@operational_write
def update_animal(animal_id: str, payload: dict, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    if "status" in payload:
        raise HTTPException(
            status_code=422,
            detail=(
                "Animal status is governed by the lifecycle or disposition "
                "workflow; use the dedicated endpoint."
            ),
        )

    requested_lifecycle = payload.get("lifecycle_status")
    if requested_lifecycle is not None:
        requested_lifecycle = str(requested_lifecycle).strip().upper()
        current_lifecycle = str(
            getattr(animal, "lifecycle_status", "") or ""
        ).upper()
        if (
            current_lifecycle in TERMINAL_LIFECYCLE_STATUSES
            and requested_lifecycle not in TERMINAL_LIFECYCLE_STATUSES
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Terminal animals cannot be returned to an active "
                    "lifecycle through a profile update."
                ),
            )

    _validate_parentage_payload(repository, animal, payload)

    if "animal_category" in payload or "category" in payload or "lifecycle_status" in payload or "sex" in payload:
        _apply_classification_payload(animal, payload)

    if str(getattr(animal, "lifecycle_status", "") or "").upper() in TERMINAL_LIFECYCLE_STATUSES:
        animal.active = False
        animal.status = str(animal.lifecycle_status).upper()
        animal.is_currently_milking = False
        animal.milking_frequency = None

    if "milking_frequency" in payload:
        frequency = payload.get("milking_frequency")
        _validate_milking_frequency(animal, frequency)
        if frequency is not None:
            try:
                updated = repository.set_milking_frequency(
                    animal_id=animal_id,
                    new_frequency=frequency,
                    changed_by=payload.get("changed_by") or payload.get("operator") or "API",
                    reason=payload.get("milking_frequency_reason") or payload.get("reason"),
                    effective_date=payload.get("effective_date"),
                )
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            animal = updated or animal
        else:
            animal.milking_frequency = None
    elif not animal.is_currently_milking:
        animal.milking_frequency = None

    editable_fields = {
        "animal_type",
        "legacy_animal_id",
        "ear_tag",
        "rfid",
        "breed",
        "sex",
        "date_of_birth",
        "date_of_acquisition",
        "dam_id",
        "sire_id",
        "production_group",
        "location",
        "photo_data",
    }
    changed = {}
    for field in editable_fields:
        if field in payload:
            value = payload[field]
            if field in {"date_of_birth", "date_of_acquisition"}:
                value = _parse_date(value, field)
            if field == "legacy_animal_id" and value:
                existing = repository.get_all() or []
                if any(
                    other is not animal
                    and getattr(other, "legacy_animal_id", None) == value
                    for other in existing
                ):
                    raise HTTPException(status_code=409, detail=f"Old Animal ID already exists: {value}")
            setattr(animal, field, value)
            changed[field] = value

    animal.updated_at = datetime.now(UTC)
    updated = repository.save(animal)
    if "animal_category" in payload or "category" in payload or "lifecycle_status" in payload or "sex" in payload:
        changed["animal_category"] = serialize_animal(animal).get("animal_category")
        changed["lifecycle_status"] = animal.lifecycle_status
        changed["sex"] = animal.sex
    _record_operational_event(container, "animal_profile_update", {"animal_id": animal_id, "changed_fields": sorted(changed.keys())}, str(payload.get("operator") or "API"))
    return serialize_animal(updated)


@router.patch("/animals/{animal_id}/disposition")
@operational_write
def record_animal_disposition(animal_id: str, payload: dict, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    disposition = str(payload.get("disposition") or "").upper()
    if disposition not in EXIT_STATUSES:
        raise HTTPException(status_code=422, detail="Disposition must be SOLD or DECEASED")

    operational_date = _farm_operational_date(container)
    effective_date_value = _parse_date(
        payload.get("effective_date") or operational_date,
        "effective_date",
    )
    if effective_date_value is None:
        raise HTTPException(status_code=422, detail="effective_date must be an ISO date")
    if effective_date_value > operational_date:
        raise HTTPException(
            status_code=422,
            detail="effective_date cannot be in the future of the farm operational date",
        )
    effective_date = effective_date_value.isoformat()

    animal.lifecycle_status = disposition
    animal.status = disposition
    animal.is_currently_milking = False
    animal.milking_frequency = None
    animal.active = False
    animal.updated_at = datetime.now(UTC)
    updated = repository.save(animal)

    event_payload = {
        "animal_id": animal_id,
        "disposition": disposition,
        "effective_date": effective_date,
        "reason": payload.get("reason"),
        "buyer_or_counterparty": payload.get("buyer_or_counterparty"),
        "amount": payload.get("amount"),
        "reference": payload.get("reference"),
        "veterinarian": payload.get("veterinarian"),
        "cause": payload.get("cause"),
        "notes": payload.get("notes"),
    }
    _record_operational_event(container, "animal_disposition", event_payload, str(payload.get("operator") or "API"))
    return {"animal": serialize_animal(updated), "disposition": event_payload}


@router.get("/animals/{animal_id}/disposition-history")
def disposition_history(animal_id: str, container=Depends(get_container)):
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return _event_payloads_for_animal(container, "animal_disposition", animal_id)


@router.post("/animals/{animal_id}/activate")
@operational_write
def activate_animal(animal_id: str, payload: dict | None = None, container=Depends(get_container)):
    payload = payload or {}
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    if (
        str(getattr(animal, "lifecycle_status", "") or "").upper()
        in TERMINAL_LIFECYCLE_STATUSES
        or str(getattr(animal, "status", "") or "").upper()
        in TERMINAL_LIFECYCLE_STATUSES
    ):
        raise HTTPException(
            status_code=409,
            detail="Sold, culled, or deceased animals cannot be activated.",
        )
    animal.activate()
    updated = repository.save(animal)
    _record_operational_event(container, "animal_activated", {"animal_id": animal_id, "reason": payload.get("reason")}, str(payload.get("operator") or "API"))
    return serialize_animal(updated)


@router.patch("/animals/{animal_id}/lifecycle")
@operational_write
def change_lifecycle(animal_id: str, payload: dict, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    lifecycle = str(payload.get("lifecycle_status", "")).upper()
    if lifecycle not in ALLOWED_LIFECYCLE_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid lifecycle status. Allowed: " + ", ".join(sorted(ALLOWED_LIFECYCLE_STATUSES)))
    previous = animal.lifecycle_status
    previous_terminal = str(previous or "").upper() in TERMINAL_LIFECYCLE_STATUSES
    if previous_terminal and lifecycle not in TERMINAL_LIFECYCLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="Terminal animals cannot be returned to a live lifecycle.",
        )
    try:
        classification = AnimalClassificationService.classify(lifecycle, animal.sex)
    except AnimalClassificationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    animal.lifecycle_status = classification.lifecycle_status
    animal.sex = classification.sex
    if lifecycle in TERMINAL_LIFECYCLE_STATUSES:
        animal.status = lifecycle
        animal.active = False
    else:
        animal.status = "ACTIVE"
        animal.active = True
    animal.production_group = payload.get("production_group", getattr(animal, "production_group", None))
    animal.is_currently_milking = classification.lifecycle_status == "LACTATING"
    if not animal.is_currently_milking:
        animal.milking_frequency = None
    animal.updated_at = datetime.now(UTC)
    updated = repository.save(animal)
    _record_operational_event(container, "animal_lifecycle", {"animal_id": animal_id, "previous_status": previous, "lifecycle_status": classification.lifecycle_status, "reason": payload.get("reason")}, str(payload.get("operator") or "API"))
    return serialize_animal(updated)


@router.post("/animals/{animal_id}/milking-frequency")
def change_milking_frequency(animal_id: str, payload: dict, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    frequency = payload.get("milking_frequency")
    _validate_milking_frequency(animal, frequency)
    if frequency is None:
        raise HTTPException(status_code=422, detail="milking_frequency required")
    try:
        updated = repository.set_milking_frequency(
            animal_id=animal_id,
            new_frequency=frequency,
            changed_by=payload.get("changed_by"),
            reason=payload.get("reason"),
            effective_date=payload.get("effective_date"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return serialize_animal(updated)


@router.get("/animals/{animal_id}/milking-frequency/history")
def milking_frequency_history(animal_id: str, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return [{"milking_frequency": record.milking_frequency, "changed_by": record.changed_by, "reason": record.reason, "effective_from": record.effective_from.isoformat() if record.effective_from else None, "effective_to": record.effective_to.isoformat() if record.effective_to else None} for record in repository.get_milking_frequency_history(animal_id)]


@router.post("/animals/{animal_id}/vaccinations")
@operational_write
def record_vaccination(animal_id: str, payload: dict, container=Depends(get_container)):
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    if getattr(animal, "active", True) is False:
        raise HTTPException(
            status_code=409,
            detail="Vaccinations cannot be recorded for inactive or exited animals.",
        )
    supplied_animal_id = str(payload.get("animal_id") or "").strip()
    if supplied_animal_id and supplied_animal_id != animal_id:
        raise HTTPException(
            status_code=422,
            detail="payload animal_id must match the path animal_id",
        )
    vaccine = str(payload.get("vaccine") or payload.get("vaccination") or "").strip()
    if not vaccine:
        raise HTTPException(status_code=422, detail="vaccine required")
    operational_date = _farm_operational_date(container)
    schedule_only = str(payload.get("schedule_status") or "").strip().upper() == "SCHEDULED"
    administered = _parse_date(payload.get("administered_date"), "administered_date")
    if not schedule_only and administered is None:
        administered = operational_date
    if not schedule_only and administered is None:
        raise HTTPException(status_code=422, detail="administered_date must be an ISO date")
    if administered is not None and administered > operational_date:
        raise HTTPException(
            status_code=422,
            detail="administered_date cannot be in the future of the farm operational date",
        )
    next_due = _parse_date(payload.get("next_due_date"), "next_due_date")
    if next_due is not None and administered is not None and next_due < administered:
        raise HTTPException(
            status_code=422,
            detail="next_due_date cannot precede administered_date",
        )

    schedule_status = str(
        payload.get("schedule_status")
        or ("NEXT_DUE_DATE" if next_due is not None else "UNKNOWN_NEXT_DUE")
    ).strip().upper()
    allowed_schedule_statuses = {
        "SCHEDULED",
        "NEXT_DUE_DATE",
        "NO_REPEAT_REQUIRED",
        "UNKNOWN_NEXT_DUE",
        "ADMINISTERED",
    }
    if schedule_status not in allowed_schedule_statuses:
        raise HTTPException(
            status_code=422,
            detail=(
                "schedule_status must be NEXT_DUE_DATE, NO_REPEAT_REQUIRED, "
                "or UNKNOWN_NEXT_DUE"
            ),
        )
    if schedule_status in {"SCHEDULED", "NEXT_DUE_DATE"} and next_due is None:
        raise HTTPException(
            status_code=422,
            detail="next_due_date is required when schedule_status is NEXT_DUE_DATE",
        )
    if schedule_status == "SCHEDULED" and not str(payload.get("dose") or "").strip():
        raise HTTPException(status_code=422, detail="dose required")
    if schedule_status == "NO_REPEAT_REQUIRED" and next_due is not None:
        raise HTTPException(
            status_code=422,
            detail="next_due_date must be empty when no repeat is required",
        )

    operator = str(payload.get("operator") or "API").strip() or "API"
    vaccination_repository = container.repository_factory.vaccinations()
    if (
        schedule_status == "SCHEDULED"
        and vaccination_repository.active_duplicate_exists(
            animal_id=animal_id,
            vaccine=vaccine,
            scheduled_date=next_due,
        )
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Duplicate active vaccination occurrence: "
                f"{vaccine} on {next_due.isoformat()}"
            ),
        )

    record = VaccinationRecord(
        animal_id=animal_id,
        vaccine=vaccine,
        dose=(str(payload.get("dose")).strip() if payload.get("dose") else None),
        administered_date=administered,
        next_due_date=next_due,
        schedule_status=schedule_status,
        batch_number=(
            str(payload.get("batch_number")).strip()
            if payload.get("batch_number")
            else None
        ),
        veterinarian=(
            str(payload.get("veterinarian")).strip()
            if payload.get("veterinarian")
            else None
        ),
        notes=(
            str(payload.get("notes")).strip()
            if payload.get("notes")
            else None
        ),
        operator=operator,
        # ``status`` remains the validity boundary (active versus VOID).
        # Administration state is represented by ``administered_date``.
        status="COMPLETED",
    )
    vaccination_repository.add(record, commit=False)
    event_payload = {
        "animal_id": animal_id,
        "vaccine": vaccine,
        "dose": record.dose,
        "administered_date": administered.isoformat() if administered else None,
        "next_due_date": next_due.isoformat() if next_due else None,
        "schedule_status": schedule_status,
        "batch_number": record.batch_number,
        "veterinarian": record.veterinarian,
        "notes": record.notes,
        "status": "COMPLETED",
        "event_action": (
            "SCHEDULE_CREATED"
            if schedule_status == "SCHEDULED"
            else "ADMINISTERED"
        ),
    }
    event = _record_operational_event(
        container,
        "vaccination",
        event_payload,
        operator,
    )
    if event is not None:
        record.source_event_id = event.event_id
    container.repository_factory.session.flush()
    if not container.repository_factory.session.info.get(
        "operational_write_managed", False
    ):
        container.repository_factory.session.commit()
        container.repository_factory.session.refresh(record)
    return _serialize_vaccination_record(record)


@router.post("/animals/{animal_id}/vaccinations/schedule-batch")
@operational_write
def schedule_vaccination_batch(
    animal_id: str,
    payload: dict,
    container=Depends(get_container),
):
    """Create one operator-submitted vaccination schedule atomically."""
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    if getattr(animal, "active", True) is False:
        raise HTTPException(
            status_code=409,
            detail="Vaccinations cannot be scheduled for inactive or exited animals.",
        )

    supplied_animal_id = str(payload.get("animal_id") or "").strip()
    if supplied_animal_id and supplied_animal_id != animal_id:
        raise HTTPException(
            status_code=422,
            detail="payload animal_id must match the path animal_id",
        )

    raw_occurrences = payload.get("occurrences")
    if not isinstance(raw_occurrences, list) or not raw_occurrences:
        raise HTTPException(
            status_code=422,
            detail="occurrences must contain at least one vaccination schedule",
        )

    operator = str(payload.get("operator") or "Operator UI").strip() or "Operator UI"
    validated: list[dict] = []
    submitted_keys: set[tuple[str, object]] = set()

    # Validate the complete operator action before creating any row or event.
    for index, occurrence in enumerate(raw_occurrences):
        if not isinstance(occurrence, dict):
            raise HTTPException(
                status_code=422,
                detail=f"occurrences[{index}] must be an object",
            )

        vaccine = str(
            occurrence.get("vaccine")
            or occurrence.get("vaccination")
            or ""
        ).strip()
        if not vaccine:
            raise HTTPException(
                status_code=422,
                detail=f"occurrences[{index}].vaccine required",
            )

        scheduled_date = _parse_date(
            occurrence.get("scheduled_date")
            or occurrence.get("next_due_date"),
            f"occurrences[{index}].scheduled_date",
        )
        if scheduled_date is None:
            raise HTTPException(
                status_code=422,
                detail=f"occurrences[{index}].scheduled_date required",
            )

        dose = str(occurrence.get("dose") or "").strip()
        if not dose:
            raise HTTPException(
                status_code=422,
                detail=f"occurrences[{index}].dose required",
            )

        duplicate_key = (
            vaccine.casefold(),
            scheduled_date,
        )
        if duplicate_key in submitted_keys:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Duplicate vaccination occurrence in submitted schedule: "
                    f"{vaccine} on {scheduled_date.isoformat()}"
                ),
            )
        submitted_keys.add(duplicate_key)

        validated.append(
            {
                "vaccine": vaccine,
                "scheduled_date": scheduled_date,
                "dose": dose,
                "batch_number": (
                    str(occurrence.get("batch_number")).strip()
                    if occurrence.get("batch_number")
                    else None
                ),
                "veterinarian": (
                    str(occurrence.get("veterinarian")).strip()
                    if occurrence.get("veterinarian")
                    else None
                ),
                "notes": (
                    str(occurrence.get("notes")).strip()
                    if occurrence.get("notes")
                    else None
                ),
            }
        )

    vaccination_repository = container.repository_factory.vaccinations()
    for occurrence in validated:
        if vaccination_repository.active_duplicate_exists(
            animal_id=animal_id,
            vaccine=occurrence["vaccine"],
            scheduled_date=occurrence["scheduled_date"],
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Duplicate active vaccination occurrence: "
                    f"{occurrence['vaccine']} on "
                    f"{occurrence['scheduled_date'].isoformat()}"
                ),
            )

    records: list[VaccinationRecord] = []

    for occurrence in validated:
        record = VaccinationRecord(
            animal_id=animal_id,
            vaccine=occurrence["vaccine"],
            dose=occurrence["dose"],
            administered_date=None,
            next_due_date=occurrence["scheduled_date"],
            schedule_status="SCHEDULED",
            batch_number=occurrence["batch_number"],
            veterinarian=occurrence["veterinarian"],
            notes=occurrence["notes"],
            operator=operator,
            # ``status`` remains the validity boundary (active versus VOID).
            status="COMPLETED",
        )
        vaccination_repository.add(record, commit=False)

        event_payload = {
            "animal_id": animal_id,
            "vaccine": record.vaccine,
            "dose": record.dose,
            "administered_date": None,
            "next_due_date": record.next_due_date.isoformat(),
            "scheduled_date": record.next_due_date.isoformat(),
            "schedule_status": "SCHEDULED",
            "batch_number": record.batch_number,
            "veterinarian": record.veterinarian,
            "notes": record.notes,
            "status": "COMPLETED",
            "event_action": "SCHEDULE_CREATED",
        }
        event = _record_operational_event(
            container,
            "vaccination",
            event_payload,
            operator,
        )
        if event is not None:
            record.source_event_id = event.event_id

        records.append(record)

    container.repository_factory.session.flush()

    if not container.repository_factory.session.info.get(
        "operational_write_managed", False
    ):
        container.repository_factory.session.commit()
        for record in records:
            container.repository_factory.session.refresh(record)

    return {
        "animal_id": animal_id,
        "count": len(records),
        "occurrences": [
            _serialize_vaccination_record(record)
            for record in records
        ],
    }


def _get_governed_vaccination_occurrence(
    vaccination_repository,
    animal_id: str,
    vaccination_id: int,
):
    record = vaccination_repository.get_by_id(vaccination_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Vaccination occurrence not found",
        )

    if str(record.animal_id) != animal_id:
        raise HTTPException(
            status_code=409,
            detail="Vaccination occurrence does not belong to this animal",
        )

    if str(record.status or "").upper() == "VOID":
        raise HTTPException(
            status_code=409,
            detail="VOID vaccination occurrence cannot be amended",
        )

    if record.administered_date is not None:
        raise HTTPException(
            status_code=409,
            detail="Administered vaccination occurrence cannot be amended",
        )

    return record


@router.post("/animals/{animal_id}/vaccinations/{vaccination_id}/amend")
@operational_write
def amend_scheduled_vaccination(
    animal_id: str,
    vaccination_id: int,
    payload: dict,
    container=Depends(get_container),
):
    """Governed amendment for an existing scheduled vaccination occurrence."""
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    vaccination_repository = container.repository_factory.vaccinations()
    record = _get_governed_vaccination_occurrence(
        vaccination_repository,
        animal_id,
        vaccination_id,
    )

    vaccine = str(
        payload.get("vaccine")
        or payload.get("vaccination")
        or ""
    ).strip()
    if not vaccine:
        raise HTTPException(status_code=422, detail="vaccine required")

    dose = _require_text(payload, "dose")
    scheduled_date = _parse_date(
        payload.get("scheduled_date") or payload.get("next_due_date"),
        "scheduled_date",
    )
    if scheduled_date is None:
        raise HTTPException(status_code=422, detail="scheduled_date required")

    if vaccination_repository.active_duplicate_exists(
        animal_id=animal_id,
        vaccine=vaccine,
        scheduled_date=scheduled_date,
        exclude_id=record.id,
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Duplicate active vaccination occurrence: "
                f"{vaccine} on {scheduled_date.isoformat()}"
            ),
        )

    operator = str(
        payload.get("operator")
        or payload.get("veterinarian")
        or payload.get("administrator")
        or "Operator UI"
    ).strip() or "Operator UI"
    veterinarian = (
        str(
            payload.get("veterinarian")
            or payload.get("administrator")
            or ""
        ).strip()
        or None
    )
    notes = (
        str(payload.get("notes") or "").strip()
        or None
    )

    vaccination_repository.amend_scheduled_occurrence(
        record,
        vaccine=vaccine,
        dose=dose,
        scheduled_date=scheduled_date,
        veterinarian=veterinarian,
        notes=notes,
        operator=operator,
        commit=False,
    )

    event_payload = {
        "vaccination_occurrence_id": record.id,
        "animal_id": record.animal_id,
        "vaccine": record.vaccine,
        "dose": record.dose,
        "scheduled_date": record.next_due_date.isoformat(),
        "next_due_date": record.next_due_date.isoformat(),
        "administered_date": None,
        "schedule_status": "SCHEDULED",
        "batch_number": record.batch_number,
        "veterinarian": record.veterinarian,
        "notes": record.notes,
        "status": record.status,
        "event_action": "SCHEDULE_AMENDED",
    }
    _record_operational_event(
        container,
        "vaccination",
        event_payload,
        operator,
    )

    inventory_item = payload.get("inventory_item")
    consumption_quantity = payload.get("consumption_quantity")
    consumption_unit = payload.get("consumption_unit")
    if any(value is not None for value in (inventory_item, consumption_quantity, consumption_unit)):
        if not inventory_item or consumption_quantity is None or not consumption_unit:
            raise HTTPException(status_code=422, detail="Clinical inventory linkage requires inventory_item, consumption_quantity, and consumption_unit together.")
        record_clinical_consumption(
            container, item=inventory_item, quantity=float(consumption_quantity),
            unit=consumption_unit, source_type="VACCINATION_CONSUMPTION",
            source_id=record.id, recorded_by=operator, notes=f"Vaccination {record.id}: {record.vaccine}",
        )

    container.repository_factory.session.flush()
    if not container.repository_factory.session.info.get(
        "operational_write_managed", False
    ):
        container.repository_factory.session.commit()
        container.repository_factory.session.refresh(record)

    return _serialize_vaccination_record(record)


@router.post("/animals/{animal_id}/vaccinations/{vaccination_id}/void")
@operational_write
def void_scheduled_vaccination(
    animal_id: str,
    vaccination_id: int,
    payload: dict,
    container=Depends(get_container),
):
    """Logically VOID one unadministered vaccination schedule occurrence."""
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    vaccination_repository = container.repository_factory.vaccinations()
    record = _get_governed_vaccination_occurrence(
        vaccination_repository,
        animal_id,
        vaccination_id,
    )

    operator = str(
        payload.get("operator")
        or payload.get("veterinarian")
        or payload.get("administrator")
        or "Operator UI"
    ).strip() or "Operator UI"
    notes = (
        str(payload.get("notes") or "").strip()
        or record.notes
    )

    vaccination_repository.void_scheduled_occurrence(
        record,
        operator=operator,
        notes=notes,
        commit=False,
    )

    event_payload = {
        "vaccination_occurrence_id": record.id,
        "animal_id": record.animal_id,
        "vaccine": record.vaccine,
        "dose": record.dose,
        "scheduled_date": (
            record.next_due_date.isoformat()
            if record.next_due_date
            else None
        ),
        "next_due_date": (
            record.next_due_date.isoformat()
            if record.next_due_date
            else None
        ),
        "administered_date": None,
        "schedule_status": "VOID",
        "batch_number": record.batch_number,
        "veterinarian": record.veterinarian,
        "notes": record.notes,
        "status": "VOID",
        "event_action": "SCHEDULE_VOIDED",
    }
    _record_operational_event(
        container,
        "vaccination",
        event_payload,
        operator,
    )

    container.repository_factory.session.flush()
    if not container.repository_factory.session.info.get(
        "operational_write_managed", False
    ):
        container.repository_factory.session.commit()
        container.repository_factory.session.refresh(record)

    return _serialize_vaccination_record(record)


@router.post("/animals/{animal_id}/vaccinations/{vaccination_id}/administer")
@operational_write
def administer_scheduled_vaccination(
    animal_id: str,
    vaccination_id: int,
    payload: dict,
    container=Depends(get_container),
):
    """Endorse one existing scheduled vaccination occurrence as administered."""
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    if getattr(animal, "active", True) is False:
        raise HTTPException(
            status_code=409,
            detail="Vaccinations cannot be administered to inactive or exited animals.",
        )

    vaccination_repository = container.repository_factory.vaccinations()
    record = vaccination_repository.get_by_id(vaccination_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Vaccination occurrence not found",
        )

    if str(record.animal_id) != animal_id:
        raise HTTPException(
            status_code=409,
            detail="Vaccination occurrence does not belong to this animal",
        )

    if str(record.status or "").upper() == "VOID":
        raise HTTPException(
            status_code=409,
            detail="VOID vaccination occurrence cannot be administered",
        )

    if record.administered_date is not None:
        raise HTTPException(
            status_code=409,
            detail="Vaccination occurrence has already been administered",
        )

    if record.next_due_date is None:
        raise HTTPException(
            status_code=409,
            detail="Vaccination occurrence has no scheduled date",
        )

    operational_date = _farm_operational_date(container)
    administered = _parse_date(
        payload.get("administered_date"),
        "administered_date",
    )
    if administered is None:
        administered = operational_date

    if administered > operational_date:
        raise HTTPException(
            status_code=422,
            detail=(
                "administered_date cannot be in the future "
                "of the farm operational date"
            ),
        )

    operator = str(
        payload.get("operator")
        or payload.get("veterinarian")
        or "Operator UI"
    ).strip() or "Operator UI"

    record.administered_date = administered
    record.schedule_status = "ADMINISTERED"
    record.operator = operator

    if payload.get("dose") is not None:
        record.dose = str(payload.get("dose")).strip() or record.dose
    if payload.get("batch_number") is not None:
        record.batch_number = (
            str(payload.get("batch_number")).strip() or record.batch_number
        )
    if payload.get("veterinarian") is not None:
        record.veterinarian = (
            str(payload.get("veterinarian")).strip() or record.veterinarian
        )
    if payload.get("notes") is not None:
        record.notes = str(payload.get("notes")).strip() or record.notes

    event_payload = {
        "vaccination_occurrence_id": record.id,
        "animal_id": record.animal_id,
        "vaccine": record.vaccine,
        "dose": record.dose,
        "scheduled_date": (
            record.next_due_date.isoformat()
            if record.next_due_date
            else None
        ),
        "administered_date": administered.isoformat(),
        "next_due_date": record.next_due_date.isoformat(),
        "schedule_status": "ADMINISTERED",
        "batch_number": record.batch_number,
        "veterinarian": record.veterinarian,
        "notes": record.notes,
        "status": "COMPLETED",
        "event_action": "ADMINISTERED",
    }

    _record_operational_event(
        container,
        "vaccination",
        event_payload,
        operator,
    )

    container.repository_factory.session.flush()

    if not container.repository_factory.session.info.get(
        "operational_write_managed",
        False,
    ):
        container.repository_factory.session.commit()
        container.repository_factory.session.refresh(record)

    return _serialize_vaccination_record(record)


@router.get("/vaccinations/audit-history")
def vaccination_audit_history(
    animal_id: str | None = None,
    container=Depends(get_container),
):
    """Return immutable vaccination lifecycle events from the event journal."""
    history = []

    for entry in container.event_journal.all_entries():
        if entry.event_type != "OperationalInputReceived":
            continue

        payload = dict(entry.payload or {})

        if str(payload.get("input_type") or "").lower() != "vaccination":
            continue

        event_animal_id = str(payload.get("animal_id") or "")

        if animal_id is not None and event_animal_id != animal_id:
            continue

        raw_action = str(payload.get("event_action") or "").upper()

        if raw_action in {"VACCINATION_SCHEDULED", "SCHEDULE_CREATED"}:
            action = "SCHEDULE_CREATED"
        elif raw_action in {"VACCINATION_SCHEDULE_AMENDED", "SCHEDULE_AMENDED"}:
            action = "SCHEDULE_AMENDED"
        elif raw_action in {"VACCINATION_SCHEDULE_VOIDED", "SCHEDULE_VOIDED"}:
            action = "SCHEDULE_VOIDED"
        elif raw_action in {"VACCINATION_ADMINISTERED", "ADMINISTERED"}:
            action = "ADMINISTERED"
        else:
            action = "LEGACY"

        scheduled_date = (
            payload.get("scheduled_date")
            or payload.get("next_due_date")
        )

        history.append(
            {
                "event_id": entry.event_id,
                "event_type": entry.event_type,
                "event_timestamp": entry.timestamp.isoformat(),
                "vaccination_occurrence_id": payload.get(
                    "vaccination_occurrence_id"
                ),
                "animal_id": event_animal_id,
                "vaccine": payload.get("vaccine"),
                "action": action,
                "event_action": payload.get("event_action"),
                "scheduled_date": scheduled_date,
                "administered_date": payload.get("administered_date"),
                "dose": payload.get("dose"),
                "batch_number": payload.get("batch_number"),
                "administrator": (
                    payload.get("veterinarian")
                    or payload.get("administrator")
                ),
                "operator": (
                    payload.get("operator")
                    or payload.get("actor")
                ),
                "notes": payload.get("notes"),
                "status": payload.get("status"),
            }
        )

    history.sort(
        key=lambda row: (
            row.get("event_timestamp") or "",
            row.get("event_id") or "",
        )
    )

    return history



@router.get("/animals/{animal_id}/vaccinations")
def list_vaccinations(animal_id: str, container=Depends(get_container)):
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    relational = container.repository_factory.vaccinations().get_for_animal(animal_id)
    if relational:
        linked_event_ids = {
            row.source_event_id for row in relational if row.source_event_id
        }
        legacy = []
        for event in container.event_journal.all_events():
            if getattr(event, "name", None) != "OperationalInputReceived":
                continue
            payload = dict(event.payload or {})
            if (
                str(payload.get("input_type") or "").lower() == "vaccination"
                and str(payload.get("animal_id") or "") == animal_id
                and getattr(event, "event_id", None) not in linked_event_ids
                and str(payload.get("event_action") or "").upper()
                not in {
                    "VACCINATION_ADMINISTERED",
                    "ADMINISTERED",
                    "VACCINATION_SCHEDULE_AMENDED",
                    "SCHEDULE_AMENDED",
                    "VACCINATION_SCHEDULE_VOIDED",
                    "SCHEDULE_VOIDED",
                }
            ):
                legacy.append(payload)
        return [_serialize_vaccination_record(row) for row in relational] + legacy
    return _event_payloads_for_animal(container, "vaccination", animal_id)
