from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from dairyos.api.auth import get_optional_current_user
from dairyos.api.dependencies import get_container
from dairyos.api.reference_data import GOVERNED

from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.health_observation import HealthObservation
from dairyos.data.models.health_case import HealthCase
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.data.models.treatment_record import TreatmentRecord
from dairyos.farm.operations.models.breeding_record import BreedingRecord
from dairyos.data.models.milking_session_record import MilkingSessionRecord
from dairyos.milk.models.milking_session import MilkingSession
from dairyos.milk.models.milking_session_ledger import (
    MilkingSessionSkipReason,
    MilkingSessionStatus,
)
from dairyos.milk.services.milk_session_sequence_service import (
    MilkSessionSequenceService,
    SequenceViolation,
)
from dairyos.milk.services.milk_recording_intelligence_service import (
    MilkRecordingIntelligenceService,
)
from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)

from dairyos.operations.intelligence.services.withdrawal_service import (
    WithdrawalPeriod,
)

from dairyos.data.repositories.repository_factory import (
    RepositoryFactory,
)


router = APIRouter(
    prefix="/farm",
    tags=["Farm Data Entry"],
)


class BaseEntryRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    operator: str = Field(
        default="API",
        min_length=1,
    )


class MilkEntryRequest(BaseEntryRequest):
    """A governed milk entry.

    The yields are ``None`` by default rather than ``0.0``. An operator who
    enters only a morning figure has not asserted that the evening yield was
    zero, and the record must not claim they did.
    """

    animal_id: str
    morning_yield: float | None = None
    afternoon_yield: float | None = None
    evening_yield: float | None = None
    milking_session: MilkingSession
    production_date: date | None = None


class LegacyCompatibleMilkEntryRequest(BaseEntryRequest):
    """
    HTTP compatibility boundary for historical /farm/milk callers.

    The governed MilkEntryRequest deliberately requires milking_session.
    Older clients, however, historically omitted it. Such requests are
    normalized to MORNING before entering the governed request model.
    """

    animal_id: str
    morning_yield: float | None = None
    afternoon_yield: float | None = None
    evening_yield: float | None = None
    milking_session: MilkingSession | None = None
    production_date: date | None = None

    @property
    def session_attributed(self) -> bool:
        """Whether the caller actually named a milking session.

        An entry that never named one carries no position in the day, so
        there is nothing to sequence it against. Blocking such callers would
        only push them back into guessing a session -- which is the failure
        this work exists to remove.
        """

        return self.milking_session is not None

    def to_governed_request(self) -> MilkEntryRequest:
        payload = self.model_dump()
        if payload.get("milking_session") is None:
            payload["milking_session"] = MilkingSession.MORNING

        return MilkEntryRequest.model_validate(payload)


class MilkNotMilkedRequest(BaseEntryRequest):
    """Declare that a whole milking session did not happen."""

    milking_session: MilkingSession
    reason: MilkingSessionSkipReason
    operational_date: date | None = None
    notes: str | None = None


class FeedEntryRequest(BaseEntryRequest):
    feed_type: str
    quantity_kg: float
    group_or_pen: str | None = None
    animal_id: str | None = None


class HealthEntryRequest(BaseEntryRequest):
    animal_id: str
    observation: str | None = None
    symptom: str | None = None
    temperature_c: float | None = None
    severity: str = "NORMAL"
    # Optional link to an open HealthCase (G5.1). An observation can still
    # be recorded standalone exactly as before -- this is additive.
    health_case_id: int | None = None


class TreatmentEntryRequest(BaseEntryRequest):
    animal_id: str
    medicine: str
    diagnosis: str | None = None
    dose: str | None = None
    treated_by: str | None = None
    milk_withdrawal_days: float | None = None
    notes: str | None = None
    # Optional link to an open HealthCase (G5.1). A treatment can still be
    # recorded standalone exactly as before -- this is additive. When
    # linked, the case's withdrawal_until is raised to this treatment's
    # milk_withdrawal_until if that is later than what the case already has.
    health_case_id: int | None = None


class HealthCaseOpenRequest(BaseEntryRequest):
    animal_id: str
    severity: str = "NORMAL"
    diagnosis: str | None = None
    notes: str | None = None
    follow_up_due_at: datetime | None = None
    # Optionally attach an already-recorded observation to this case at the
    # moment it's opened, rather than requiring a second call.
    observation_id: int | None = None


class HealthCaseResolveRequest(BaseEntryRequest):
    resolution: str
    resolved_by: str | None = None


class DrugReferenceEntryRequest(BaseEntryRequest):
    medicine: str
    milk_withdrawal_days: float
    meat_withdrawal_days: float | None = None
    notes: str | None = None
    verified: bool = False


class BreedingEntryRequest(BaseEntryRequest):
    animal_id: str
    event_type: str
    technician: str | None = None
    result: str | None = None
    semen_or_bull: str | None = None
    notes: str | None = None


class WorkforceEntryRequest(BaseEntryRequest):
    worker_id: str
    activity: str
    task: str | None = None
    status: str | None = None
    hours: float | None = None
    location: str | None = None
    notes: str | None = None


class InventoryEntryRequest(BaseEntryRequest):
    item: str
    quantity: float
    movement_type: str | None = None
    unit: str | None = None
    location: str | None = None
    supplier: str | None = None
    notes: str | None = None


class EquipmentEntryRequest(BaseEntryRequest):
    equipment_id: str
    activity: str
    status: str | None = None
    running_hours: float | None = None
    location: str | None = None
    notes: str | None = None


class FinancialEntryRequest(BaseEntryRequest):
    transaction_type: str
    amount: float
    category: str | None = None
    payment_method: str | None = None
    counterparty: str | None = None
    notes: str | None = None
    # Optional so an entry can carry the date the money actually moved, not
    # the moment it was typed in. Left unset it still defaults to now, which
    # is what every historical row did.
    transaction_date: date | None = None


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _optional_float(value) -> float | None:
    """Preserve the difference between "not entered" and "entered zero"."""

    if value is None or value == "":
        return None

    return float(value)


def _as_date(value) -> date | None:
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value)[:10])


def _production_datetime(payload: dict[str, Any]) -> datetime | None:
    """The day the milk was produced, as stated by the operator."""

    produced_on = _as_date(payload.get("production_date"))

    if produced_on is None:
        return None

    return datetime(produced_on.year, produced_on.month, produced_on.day)


def _transaction_datetime(payload: dict[str, Any]) -> datetime | None:
    """The day the money moved, as stated by the operator.

    Returns None when no date was supplied, leaving the model default to
    stamp the entry time -- which is what every row written before this
    field existed did.
    """

    moved_on = _as_date(payload.get("transaction_date"))

    if moved_on is None:
        return None

    return datetime(moved_on.year, moved_on.month, moved_on.day)


def _sequence_service(container):
    """The sequencing service, or None when no ledger boundary exists.

    Test doubles and legacy compositions may not expose the ledger. Sequencing
    is an integrity guard, not a hard dependency of milk recording.
    """

    factory = getattr(container, "repository_factory", None)
    accessor = getattr(factory, "milking_session_ledger", None)

    if accessor is None:
        return None

    return MilkSessionSequenceService(accessor())


def _settle_session(
    container,
    *,
    operational_date: date,
    milking_session: str,
    status: str,
    reason: str | None = None,
    notes: str | None = None,
    recorded_by: str | None = None,
):
    """State what happened to a session, if the farm has not already.

    Idempotent: the second animal of a morning milking must not attempt a
    second ledger row.
    """

    factory = getattr(container, "repository_factory", None)
    accessor = getattr(factory, "milking_session_ledger", None)

    if accessor is None:
        return None

    return accessor().settle(
        operational_date=operational_date,
        milking_session=str(milking_session),
        status=str(status),
        reason=reason,
        notes=notes,
        recorded_by=recorded_by,
    )


def _operator(
    payload: dict[str, Any],
    current_user: dict[str, Any] | None,
) -> str:
    if current_user is not None:
        return str(current_user["sub"])

    return str(payload.get("operator") or "API")


def _record(
    container,
    input_type: str,
    payload: dict[str, Any],
    current_user: dict[str, Any] | None = None,
):
    """Persist domain data before publishing the operational input event.

    Repository-backed inputs therefore cannot advertise an accepted
    operational event when their domain record failed to persist. Inputs
    without a domain repository (workforce/inventory/equipment) remain
    authoritative through the durable operational-input repository/event
    stream.
    """
    operator = _operator(payload, current_user)

    canonical_payload = {
        **payload,
        "operator": operator,
        "timestamp": payload.get("timestamp") or _timestamp(),
    }

    # Equipment has no domain repository (see docstring above) -- the
    # projection bridge is the only place this fact lands. It, and
    # EquipmentIntelligenceService downstream of it, both read
    # `equipment_status[equipment_id]["operational_status"]` out of a
    # "details" sub-object (see FarmOperationalState.apply(), the
    # equipment_status_recorded branch). Nothing upstream of here has ever
    # built that sub-object -- the real payload's fields sit flat -- so
    # `event_payload.get("details", {})` has always evaluated to `{}` and
    # the equipment attention check has been structurally unreachable
    # regardless of what values it looked for (found 2026-08-14, alongside
    # the vocabulary mismatch already filed as G9.1). Built here, not in
    # the state layer, so the state layer's own existing unit tests --
    # which construct a "details" payload directly -- are untouched.
    if input_type == "equipment":
        canonical_payload["details"] = {
            "operational_status": payload.get("status"),
            "activity": payload.get("activity"),
            "running_hours": payload.get("running_hours"),
            "location": payload.get("location"),
            "notes": payload.get("notes"),
        }

    rf = getattr(container, "repository_factory", None)
    owns_factory = False
    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True

    try:
        if input_type == "milk_production":
            milk_repo = rf.milk()
            production = MilkProduction(
                animal_id=str(payload.get("animal_id")),
                milking_session=str(payload.get("milking_session")),
                morning_yield=_optional_float(payload.get("morning_yield")),
                afternoon_yield=_optional_float(
                    payload.get("afternoon_yield")
                ),
                evening_yield=_optional_float(payload.get("evening_yield")),
                session_ledger=bool(payload.get("session_ledger", False)),
                status=payload.get("status", "RECORDED"),
            )

            produced_at = _production_datetime(payload)
            if produced_at is not None:
                production.production_date = produced_at

            declared_total = _optional_float(
                payload.get(
                    "total_yield",
                    payload.get("litres"),
                )
            )
            if declared_total is not None:
                production.total_yield = declared_total
            else:
                production.calculate_total()

            if production.session_ledger and hasattr(
                milk_repo,
                "upsert_ledger_day",
            ):
                milk_repo.upsert_ledger_day(production)
            elif hasattr(milk_repo, "save"):
                milk_repo.save(production)
            else:
                milk_repo.add(production)

        elif input_type == "milking_session_not_milked":
            ledger = rf.milking_session_ledger()
            ledger.settle(
                operational_date=_as_date(payload.get("operational_date")),
                milking_session=str(payload.get("milking_session")),
                status=MilkingSessionStatus.NOT_MILKED.value,
                reason=str(payload.get("reason")),
                notes=payload.get("notes"),
                recorded_by=operator,
            )

        elif input_type == "feeding":
            feed_repo = rf.feed()
            record = FeedRecord(
                animal_id=payload.get("animal_id"),
                group_or_pen=payload.get("group_or_pen"),
                feed_type=payload.get("feed_type", "DEFAULT"),
                quantity_kg=float(payload.get("quantity_kg", 0.0)),
                notes=payload.get("notes"),
                status=payload.get("status", "RECORDED"),
            )
            if hasattr(feed_repo, "save"):
                feed_repo.save(record)
            else:
                feed_repo.add(record)

        elif input_type == "animal_health":
            health_repo = rf.health()
            observation = HealthObservation(
                animal_id=str(payload.get("animal_id")),
                observation=payload.get("observation"),
                symptom=payload.get("symptom"),
                temperature=(
                    payload.get("temperature_c")
                    or payload.get("temperature")
                ),
                temperature_c=payload.get("temperature_c"),
                reported_by=operator,
                severity=payload.get("severity", "NORMAL"),
                status=payload.get("status", "OPEN"),
                health_case_id=payload.get("health_case_id"),
            )
            if hasattr(health_repo, "save"):
                health_repo.save(observation)
            else:
                health_repo.add(observation)

        elif input_type == "breeding":
            breeding_repo = rf.breeding()
            record = BreedingRecord(
                animal_id=str(payload.get("animal_id")),
                event_type=str(payload.get("event_type")),
                result=str(payload.get("result") or "RECORDED"),
                technician=str(
                    payload.get("technician") or operator
                ),
            )
            breeding_repo.save(record)

        elif input_type == "financial":
            finance_repo = rf.financial()
            transaction = FinancialTransaction(
                transaction_type=payload.get(
                    "transaction_type",
                    "EXPENSE",
                ),
                category=(payload.get("category") or "OTHER_OPERATING"),
                amount=float(payload.get("amount", 0.0)),
                # `reference` keeps its previous meaning so existing readers
                # are unaffected; counterparty and notes are now ALSO stored
                # in their own columns instead of one overwriting the other.
                reference=(
                    payload.get("counterparty")
                    or payload.get("notes")
                    or ""
                ),
                payment_method=payload.get("payment_method"),
                counterparty=payload.get("counterparty"),
                notes=payload.get("notes"),
                status=payload.get("status", "RECORDED"),
                animal_id=payload.get("animal_id"),
                currency=payload.get("currency", "PKR"),
            )

            # The date the money actually moved, when the operator supplied
            # one. Left unset, the model default stamps "now" -- the only
            # behaviour available before this field existed.
            moved_on = _transaction_datetime(payload)
            if moved_on is not None:
                transaction.transaction_date = moved_on
            if hasattr(finance_repo, "save"):
                finance_repo.save(transaction)
            else:
                finance_repo.add(transaction)

        elif input_type == "inventory":
            inventory_repo = rf.inventory()

            # Direction is fixed per governed movement_type (G8.1, decided
            # 2026-08-14 via AskUserQuestion), not inferred from the sign of
            # whatever was submitted -- PURCHASE/RECEIPT always increase
            # stock, CONSUMPTION/WASTAGE always decrease it. Only
            # TRANSFER/ADJUSTMENT carry a direction the type name alone
            # can't imply, so for those two the operator's submitted sign is
            # authoritative. `record_inventory_entry()` has already
            # validated the sign/magnitude contract before this runs.
            movement_type = str(payload.get("movement_type") or "").upper()
            quantity = float(payload.get("quantity", 0.0))

            if movement_type in ("PURCHASE", "RECEIPT"):
                signed_quantity = quantity
            elif movement_type in ("CONSUMPTION", "WASTAGE"):
                signed_quantity = -quantity
            else:
                signed_quantity = quantity

            transaction = InventoryTransaction(
                item=str(payload.get("item")),
                movement_type=movement_type,
                quantity=quantity,
                signed_quantity=signed_quantity,
                unit=payload.get("unit"),
                location=payload.get("location"),
                supplier=payload.get("supplier"),
                notes=payload.get("notes"),
                recorded_by=operator,
            )
            if hasattr(inventory_repo, "save"):
                inventory_repo.save(transaction)
            else:
                inventory_repo.add(transaction)

        event = container.input_gateway.record(
            input_type=input_type,
            payload=canonical_payload,
            actor=operator,
        )
        event_payload = dict(
            getattr(event, "payload", {}) or {}
        )

    except Exception as exc:
        try:
            rf.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=(
                "Operational input persistence failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
    finally:
        if owns_factory:
            rf.close()

    return {
        **canonical_payload,
        **event_payload,
        "status": canonical_payload.get(
            "status",
            "RECORDED",
        ),
    }


def _list_by_type(container, input_type: str):
    records = []
    for event in container.event_journal.all_events():
        if (
            event.name == "OperationalInputReceived"
            and event.payload.get("input_type") == input_type
        ):
            records.append(event.payload)
    return records


@router.post("/milk")
def record_milk_entry(
    entry: LegacyCompatibleMilkEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    governed_entry = entry.to_governed_request()

    # An entry that never named a session has no position in the day, so it
    # is neither sequenced nor admitted to the ledger.
    sequenced = entry.session_attributed
    operational_date = governed_entry.production_date or _today()

    if sequenced:
        sequence = _sequence_service(container)
        if sequence is not None:
            try:
                sequence.assert_can_record(
                    operational_date,
                    governed_entry.milking_session.value,
                )
            except SequenceViolation as violation:
                raise HTTPException(
                    status_code=409,
                    detail=violation.as_operator_guidance(),
                ) from violation

    entered = [
        value
        for value in (
            governed_entry.morning_yield,
            governed_entry.afternoon_yield,
            governed_entry.evening_yield,
        )
        if value is not None
    ]
    total = sum(entered) if entered else None

    status = "RECORDED"
    withdrawal_warning = False
    safety_message = None

    withdrawal_svc = getattr(
        container,
        "withdrawal_service",
        None,
    )

    if withdrawal_svc and withdrawal_svc.is_animal_withdrawn(
        governed_entry.animal_id
    ):
        status = "WITHHELD"
        withdrawal_warning = True
        safety_message = (
            f"SAFETY ALERT: Animal {governed_entry.animal_id} is under "
            "active treatment withdrawal. Milk must be withheld!"
        )

    payload = {
        **governed_entry.model_dump(),
        "milking_session": governed_entry.milking_session.value,
        "production_date": operational_date.isoformat(),
        "litres": total,
        "total_yield": total,
        "status": status,
        "withdrawal_warning": withdrawal_warning,
        "session_ledger": sequenced,
    }

    if safety_message:
        payload["safety_message"] = safety_message

    result = _record(
        container,
        "milk_production",
        payload,
        current_user,
    )

    if sequenced:
        settled = _settle_session(
            container,
            operational_date=operational_date,
            milking_session=governed_entry.milking_session.value,
            status=MilkingSessionStatus.RECORDED.value,
            recorded_by=_operator(payload, current_user),
        )
        if settled is not None:
            result["session_record_id"] = settled.session_record_id

    return result


@router.post("/milk/not-milked")
def declare_session_not_milked(
    entry: MilkNotMilkedRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    """Record that a whole milking session did not happen.

    Without this route the sequencing interlock would have no honest exit: an
    operator whose parlour lost power would either be blocked out of the rest
    of the day or would invent a zero. A declared skip is a fact the farm can
    later explain; an invented zero is not.
    """

    if (
        entry.reason is MilkingSessionSkipReason.OTHER
        and not (entry.notes or "").strip()
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "A reason of OTHER requires notes explaining why the "
                "milking did not happen."
            ),
        )

    operational_date = entry.operational_date or _today()
    session_value = entry.milking_session.value

    sequence = _sequence_service(container)
    if sequence is not None:
        existing = sequence.ledger.get_for(operational_date, session_value)
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "MILKING_SESSION_ALREADY_SETTLED",
                    "message": (
                        f"The {session_value} session for "
                        f"{operational_date.isoformat()} is already "
                        f"recorded as {existing.status}."
                    ),
                    "operational_date": operational_date.isoformat(),
                    "milking_session": session_value,
                    "status": existing.status,
                    "session_record_id": existing.session_record_id,
                },
            )

        try:
            sequence.assert_can_record(operational_date, session_value)
        except SequenceViolation as violation:
            raise HTTPException(
                status_code=409,
                detail=violation.as_operator_guidance(),
            ) from violation

    payload = {
        **entry.model_dump(),
        "milking_session": session_value,
        "reason": entry.reason.value,
        "operational_date": operational_date.isoformat(),
        "status": MilkingSessionStatus.NOT_MILKED.value,
    }

    result = _record(
        container,
        "milking_session_not_milked",
        payload,
        current_user,
    )

    if sequence is not None:
        settled = sequence.ledger.get_for(operational_date, session_value)
        if settled is not None:
            result["session_record_id"] = settled.session_record_id

    return result


@router.get("/milk/next-session")
def next_milking_session(
    operational_date: date | None = None,
    container=Depends(get_container),
):
    """What the farm still owes a statement about today.

    The operator UI reads this to open on the right session instead of asking
    the operator to remember where the day got to.
    """

    sequence = _sequence_service(container)
    target = operational_date or _today()

    if sequence is None:
        return {
            "operational_date": target.isoformat(),
            "sequencing_active": False,
            "next_session": None,
            "observed_sessions": [],
            "settled_sessions": [],
        }

    state = sequence.session_state(target)
    state["sequencing_active"] = sequence.ledger.has_any()

    return state


@router.get("/milk")
def list_milk_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "milk_production",
    )


@router.post("/feed")
def record_feed_entry(
    entry: FeedEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "feeding",
        {
            **entry.model_dump(),
            "status": "RECORDED",
        },
        current_user,
    )


@router.get("/milk/intelligence")
def milk_recording_intelligence(
    threshold_percent: float = 20.0,
    container=Depends(get_container),
):
    rf = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True

    try:
        service = MilkRecordingIntelligenceService(
            rf.milk()
        )
        return service.dashboard(
            threshold_percent=max(
                1.0,
                min(100.0, threshold_percent),
            )
        )
    finally:
        if owns_factory:
            rf.close()


@router.get("/feed")
def list_feed_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "feeding",
    )


@router.post("/health-observations")
def record_health_observation(
    entry: HealthEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    payload = entry.model_dump()
    payload["observation"] = (
        entry.observation
        or entry.symptom
        or "Observation recorded"
    )
    payload["status"] = "OPEN"

    if entry.health_case_id is not None:
        rf = getattr(container, "repository_factory", None)
        owns_factory = False
        if rf is None:
            rf = RepositoryFactory.create()
            owns_factory = True
        try:
            if rf.health_cases().get_by_id(entry.health_case_id) is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"health_case_id {entry.health_case_id} does not exist.",
                )
        finally:
            if owns_factory:
                rf.close()

    return _record(
        container,
        "animal_health",
        payload,
        current_user,
    )


@router.get("/health-observations")
def list_health_observations(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "animal_health",
    )


@router.post("/treatments")
def record_treatment(
    entry: TreatmentEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    operator = _operator(
        entry.model_dump(),
        current_user,
    )

    rf = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True

    try:
        reference = None
        reference_repo = getattr(
            container,
            "drug_reference_repository",
            None,
        )

        if reference_repo is not None:
            reference = reference_repo.find_by_medicine(
                entry.medicine
            )

        withdrawal_source = "reference_table"
        withdrawal_days = None

        if reference is not None:
            withdrawal_days = float(
                reference.milk_withdrawal_days
            )

            if entry.milk_withdrawal_days is not None:
                withdrawal_days = max(
                    withdrawal_days,
                    float(entry.milk_withdrawal_days),
                )

                if (
                    withdrawal_days
                    > float(reference.milk_withdrawal_days)
                ):
                    withdrawal_source = "override_extended"

        elif entry.milk_withdrawal_days is not None:
            withdrawal_days = float(
                entry.milk_withdrawal_days
            )
            withdrawal_source = "manual_override"

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown medicine '{entry.medicine}': "
                    "not found in the drug reference table "
                    "and no milk_withdrawal_days was supplied "
                    "on this treatment."
                ),
            )

        if withdrawal_days < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "milk_withdrawal_days cannot be negative."
                ),
            )

        treated_at = datetime.now(timezone.utc)
        withdrawal_until = (
            treated_at
            + timedelta(days=withdrawal_days)
        )

        treatment_repo = (
            getattr(
                container,
                "treatment_repository",
                None,
            )
            or rf.treatment()
        )

        linked_case = None
        if entry.health_case_id is not None:
            case_repo = rf.health_cases()
            linked_case = case_repo.get_by_id(entry.health_case_id)
            if linked_case is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"health_case_id {entry.health_case_id} does not exist.",
                )

        record = TreatmentRecord(
            animal_id=entry.animal_id,
            diagnosis=entry.diagnosis,
            medicine=entry.medicine,
            dose=entry.dose,
            treated_by=entry.treated_by or operator,
            treated_at=treated_at,
            milk_withdrawal_days=withdrawal_days,
            milk_withdrawal_until=withdrawal_until,
            withdrawal_source=withdrawal_source,
            notes=entry.notes,
            health_case_id=entry.health_case_id,
        )

        treatment_repo.add(record)

        # A linked case's withdrawal_until always reflects the LATEST known
        # withdrawal date across everything wrapped into it -- never a
        # stale independent value a second treatment could silently
        # outrun. Never lowered, only raised.
        if linked_case is not None and (
            linked_case.withdrawal_until is None
            or withdrawal_until.replace(tzinfo=None) > linked_case.withdrawal_until
        ):
            linked_case.withdrawal_until = withdrawal_until.replace(tzinfo=None)
            case_repo.add(linked_case)

        withdrawal_svc = getattr(
            container,
            "withdrawal_service",
            None,
        )

        if withdrawal_svc is not None:
            withdrawal_svc.add_period(
                WithdrawalPeriod(
                    treatment_id=str(record.id),
                    animal_id=entry.animal_id,
                    start_time=treated_at,
                    end_time=withdrawal_until,
                )
            )

        canonical_payload = {
            **entry.model_dump(),
            "operator": operator,
            "treatment_id": record.id,
            "treated_at": treated_at.isoformat(),
            "milk_withdrawal_days": withdrawal_days,
            "milk_withdrawal_until": (
                withdrawal_until.isoformat()
            ),
            "withdrawal_source": withdrawal_source,
            "status": "RECORDED",
        }

        event = container.input_gateway.record(
            input_type="treatment",
            payload=canonical_payload,
            actor=operator,
        )

        event_payload = dict(
            getattr(event, "payload", {}) or {}
        )

        return {
            **canonical_payload,
            **event_payload,
        }

    finally:
        if owns_factory:
            rf.close()


@router.get("/treatments")
def list_treatments(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "treatment",
    )


@router.get("/withdrawals/active")
def list_active_withdrawals(
    container=Depends(get_container),
):
    treatment_repo = getattr(
        container,
        "treatment_repository",
        None,
    )
    withdrawal_svc = getattr(
        container,
        "withdrawal_service",
        None,
    )

    if (
        treatment_repo is None
        or withdrawal_svc is None
    ):
        return []

    now = datetime.now(timezone.utc)
    active = []

    for record in treatment_repo.get_all():
        if withdrawal_svc.is_withdrawn(
            str(record.id),
            at=now,
        ):
            active.append(
                {
                    "treatment_id": record.id,
                    "animal_id": record.animal_id,
                    "medicine": record.medicine,
                    "treated_at": (
                        record.treated_at.isoformat()
                        if record.treated_at
                        else None
                    ),
                    "milk_withdrawal_until": (
                        record.milk_withdrawal_until.isoformat()
                        if record.milk_withdrawal_until
                        else None
                    ),
                }
            )

    return active


@router.get("/drug-reference")
def list_drug_reference(
    container=Depends(get_container),
):
    reference_repo = getattr(
        container,
        "drug_reference_repository",
        None,
    )

    if reference_repo is None:
        return []

    return [
        {
            "id": row.id,
            "medicine": row.medicine,
            "milk_withdrawal_days": (
                row.milk_withdrawal_days
            ),
            "meat_withdrawal_days": (
                row.meat_withdrawal_days
            ),
            "notes": row.notes,
            "verified": row.verified,
            "updated_by": row.updated_by,
            "updated_at": (
                row.updated_at.isoformat()
                if row.updated_at
                else None
            ),
        }
        for row in reference_repo.get_all()
    ]


@router.post("/drug-reference")
def upsert_drug_reference(
    entry: DrugReferenceEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    operator = _operator(
        entry.model_dump(),
        current_user,
    )

    reference_repo = getattr(
        container,
        "drug_reference_repository",
        None,
    )

    if reference_repo is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Drug reference repository is not available."
            ),
        )

    record = reference_repo.upsert(
        medicine=entry.medicine,
        milk_withdrawal_days=(
            entry.milk_withdrawal_days
        ),
        meat_withdrawal_days=(
            entry.meat_withdrawal_days
        ),
        notes=entry.notes,
        verified=entry.verified,
        updated_by=operator,
    )

    return {
        "id": record.id,
        "medicine": record.medicine,
        "milk_withdrawal_days": (
            record.milk_withdrawal_days
        ),
        "meat_withdrawal_days": (
            record.meat_withdrawal_days
        ),
        "notes": record.notes,
        "verified": record.verified,
        "updated_by": record.updated_by,
    }


@router.post("/breeding")
def record_breeding_entry(
    entry: BreedingEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "breeding",
        entry.model_dump(),
        current_user,
    )


@router.get("/breeding")
def list_breeding_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "breeding",
    )


@router.post("/workforce")
def record_workforce_entry(
    entry: WorkforceEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "workforce",
        entry.model_dump(),
        current_user,
    )


@router.get("/workforce")
def list_workforce_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "workforce",
    )


# TRANSFER and ADJUSTMENT are the two movement types whose direction the
# type name alone can't imply (a transfer can be inbound or outbound; an
# adjustment can correct stock up or down) -- decided 2026-08-14 via
# AskUserQuestion. For these two the operator's submitted sign is
# authoritative; every other governed type has a fixed direction enforced
# below.
INVENTORY_SIGNED_BY_OPERATOR = {"TRANSFER", "ADJUSTMENT"}


@router.post("/inventory")
def record_inventory_entry(
    entry: InventoryEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    allowed_movement_types = set(GOVERNED["inventory_movement_types"])
    movement_type = (entry.movement_type or "").upper()

    if movement_type not in allowed_movement_types:
        raise HTTPException(
            status_code=422,
            detail=(
                "movement_type must be one of: "
                + ", ".join(sorted(allowed_movement_types))
            ),
        )

    if movement_type in INVENTORY_SIGNED_BY_OPERATOR:
        if entry.quantity == 0:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"{movement_type} requires a nonzero quantity -- "
                    "positive for stock coming in, negative for stock "
                    "going out."
                ),
            )
    elif entry.quantity <= 0:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{movement_type} requires a positive quantity; direction "
                "is implied by the movement type, not the sign entered."
            ),
        )

    payload = entry.model_dump()
    payload["movement_type"] = movement_type

    return _record(
        container,
        "inventory",
        payload,
        current_user,
    )


@router.get("/inventory")
def list_inventory_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "inventory",
    )


@router.get("/inventory/balance")
def inventory_balance(
    container=Depends(get_container),
):
    """Current stock per item, derived from the ledger.

    Deliberately not a separately-maintained running total -- summing the
    full history on every read is the whole point of G8.1's decision, since
    a cached total can drift from its own history and nothing would notice.

    No reorder-threshold/low-stock flag here: that needs an item catalog
    (`InventoryItem`, not yet built -- see the execution roadmap's
    Inventory remainder) to know what "low" means per item, and inventing a
    threshold would be exactly the kind of unrequested guess this session's
    other fixes have been removing, not adding.
    """
    rf = getattr(container, "repository_factory", None)
    owns_factory = False
    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True
    try:
        balance = rf.inventory().balance_by_item()
    finally:
        if owns_factory:
            rf.close()

    return {
        "data_status": "LIVE_PERSISTED_DATA",
        "items": balance,
    }


@router.post("/equipment")
def record_equipment_entry(
    entry: EquipmentEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "equipment",
        entry.model_dump(),
        current_user,
    )


@router.get("/equipment")
def list_equipment_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "equipment",
    )


@router.post("/financial")
def record_financial_entry(
    entry: FinancialEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    payload = entry.model_dump()

    # category was previously free text while every report matched on it by
    # exact string -- a typo (or "Feed" vs "FEED") silently mis-bucketed
    # money into UNCLASSIFIED with no error to the operator. Validated
    # against the governed list the same way lifecycle_status is, at the
    # only place a new value can enter the ledger. An unset category still
    # falls back to OTHER_OPERATING in _record(), unchanged.

    allowed_categories = set(GOVERNED["financial_categories"])
    if entry.category is not None and entry.category not in allowed_categories:
        raise HTTPException(
            status_code=422,
            detail=(
                "category must be one of: "
                + ", ".join(sorted(allowed_categories))
            ),
        )
    # The payload is written to the durable event journal as JSON, which
    # cannot carry a date object. Serialised here for the same reason and in
    # the same way the milk endpoint serialises production_date.
    if entry.transaction_date is not None:
        payload["transaction_date"] = entry.transaction_date.isoformat()

    return _record(
        container,
        "financial",
        payload,
        current_user,
    )


@router.get("/financial")
def list_financial_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "financial",
    )


# ---------------------------------------------------------------------------
# Health cases (G5.1). A real status-transition entity wrapping
# observations[] + diagnosis + treatments[] + withdrawal_until +
# follow_up_due_at + resolution -- what `HealthObservation` alone never
# modeled. Resolution is always an explicit operator action, never inferred
# from a new observation/treatment arriving.
# ---------------------------------------------------------------------------


def _generate_health_case_id(case_repo) -> str:
    date_prefix = f"HL-{datetime.now(timezone.utc).strftime('%y%m%d')}"
    sequence = case_repo.count_opened_on(date_prefix) + 1
    candidate = f"{date_prefix}-{sequence:03d}"
    # Defends against a concurrent open landing the same sequence number
    # between the count and the insert -- retry upward rather than risk a
    # duplicate case_id, since case_id is the operator-facing identifier.
    while case_repo.get_by_case_id(candidate) is not None:
        sequence += 1
        candidate = f"{date_prefix}-{sequence:03d}"
    return candidate


def _health_case_dict(case) -> dict[str, Any]:
    return {
        "id": case.id,
        "case_id": case.case_id,
        "animal_id": case.animal_id,
        "severity": case.severity,
        "diagnosis": case.diagnosis,
        "notes": case.notes,
        "status": case.status,
        "opened_at": case.opened_at.isoformat() if case.opened_at else None,
        "opened_by": case.opened_by,
        "follow_up_due_at": (
            case.follow_up_due_at.isoformat() if case.follow_up_due_at else None
        ),
        "withdrawal_until": (
            case.withdrawal_until.isoformat() if case.withdrawal_until else None
        ),
        "resolution": case.resolution,
        "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        "resolved_by": case.resolved_by,
    }


def _observation_dict(observation) -> dict[str, Any]:
    return {
        "id": observation.id,
        "animal_id": observation.animal_id,
        "observed_at": (
            observation.observed_at.isoformat() if observation.observed_at else None
        ),
        "observation": observation.effective_observation,
        "temperature": observation.effective_temperature,
        "reported_by": observation.effective_reporter,
        "severity": observation.severity,
    }


def _treatment_dict(treatment) -> dict[str, Any]:
    return {
        "id": treatment.id,
        "animal_id": treatment.animal_id,
        "diagnosis": treatment.diagnosis,
        "medicine": treatment.medicine,
        "treated_at": treatment.treated_at.isoformat() if treatment.treated_at else None,
        "milk_withdrawal_until": (
            treatment.milk_withdrawal_until.isoformat()
            if treatment.milk_withdrawal_until
            else None
        ),
    }


@router.post("/health-cases")
def open_health_case(
    entry: HealthCaseOpenRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    allowed_severities = set(GOVERNED["health_severities"])
    if entry.severity not in allowed_severities:
        raise HTTPException(
            status_code=422,
            detail="severity must be one of: " + ", ".join(sorted(allowed_severities)),
        )

    operator = _operator(entry.model_dump(), current_user)

    rf = getattr(container, "repository_factory", None)
    owns_factory = False
    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True

    try:
        case_repo = rf.health_cases()

        linked_observation = None
        if entry.observation_id is not None:
            linked_observation = rf.health().get_by_id(entry.observation_id)
            if linked_observation is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"observation_id {entry.observation_id} does not exist.",
                )

        case = HealthCase(
            case_id=_generate_health_case_id(case_repo),
            animal_id=entry.animal_id,
            severity=entry.severity,
            diagnosis=entry.diagnosis,
            notes=entry.notes,
            status="OPEN",
            opened_at=datetime.now(timezone.utc).replace(tzinfo=None),
            opened_by=operator,
            follow_up_due_at=(
                entry.follow_up_due_at.replace(tzinfo=None)
                if entry.follow_up_due_at
                else None
            ),
        )
        case_repo.add(case)

        if linked_observation is not None:
            linked_observation.health_case_id = case.id
            rf.health().add(linked_observation)

        # Not routed through container.input_gateway: that path validates
        # input_type against InputCatalog.definitions(), a shared registry
        # this session deliberately isn't extending for a resource that
        # already has its own persisted, directly queryable table (unlike
        # equipment/inventory/financial, which had no queryable model of
        # their own and depended on the event journal + bridge to be
        # readable at all). HealthCase's own opened_at/opened_by/
        # resolved_at/resolved_by columns are the audit trail.
        return _health_case_dict(case)
    finally:
        if owns_factory:
            rf.close()


@router.get("/health-cases")
def list_health_cases(
    animal_id: str | None = None,
    status: str | None = None,
    container=Depends(get_container),
):
    rf = getattr(container, "repository_factory", None)
    owns_factory = False
    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True
    try:
        cases = rf.health_cases().get_all()
        if animal_id is not None:
            cases = [c for c in cases if c.animal_id == animal_id]
        if status is not None:
            cases = [c for c in cases if c.status == status]
        return {"cases": [_health_case_dict(c) for c in cases]}
    finally:
        if owns_factory:
            rf.close()


@router.get("/health-cases/{case_id}")
def get_health_case(
    case_id: str,
    container=Depends(get_container),
):
    rf = getattr(container, "repository_factory", None)
    owns_factory = False
    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True
    try:
        case = rf.health_cases().get_by_case_id(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail=f"No health case '{case_id}'.")

        observations = [
            _observation_dict(o)
            for o in rf.health().get_all()
            if o.health_case_id == case.id
        ]
        treatments = [
            _treatment_dict(t)
            for t in rf.treatment().get_all()
            if getattr(t, "health_case_id", None) == case.id
        ]

        return {
            **_health_case_dict(case),
            "observations": observations,
            "treatments": treatments,
        }
    finally:
        if owns_factory:
            rf.close()


@router.post("/health-cases/{case_id}/resolve")
def resolve_health_case(
    case_id: str,
    entry: HealthCaseResolveRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    operator = _operator(entry.model_dump(), current_user)

    rf = getattr(container, "repository_factory", None)
    owns_factory = False
    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True
    try:
        case_repo = rf.health_cases()
        case = case_repo.get_by_case_id(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail=f"No health case '{case_id}'.")

        if case.status == "RESOLVED":
            raise HTTPException(
                status_code=409,
                detail=f"Health case '{case_id}' is already resolved.",
            )

        case.status = "RESOLVED"
        case.resolution = entry.resolution
        case.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        case.resolved_by = entry.resolved_by or operator
        case_repo.add(case)

        return _health_case_dict(case)
    finally:
        if owns_factory:
            rf.close()






