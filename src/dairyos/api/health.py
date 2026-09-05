from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends

from dairyos.api.dependencies import get_container
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority

router = APIRouter(tags=["Health"])


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _vaccination_events(container):
    rows = []
    for event in container.event_journal.all_events():
        if event.name != "OperationalInputReceived":
            continue
        payload = dict(event.payload or {})
        if str(payload.get("input_type") or "").lower() != "vaccination":
            continue
        if str(payload.get("status") or "COMPLETED").upper() == "VOID":
            continue
        rows.append(payload)
    return rows


@router.get("/health")
def health():
    return {"system": "DairyOS", "status": "healthy", "runtime": "active"}


@router.get("/farm/health/summary")
def get_health_summary(container=Depends(get_container)):
    factory = container.repository_factory
    today = OperationalDateAuthority(repository_factory=factory).current_date()

    cases = factory.health_cases().get_all()
    active = [
        case
        for case in cases
        if str(getattr(case, "status", "") or "").upper() != "RESOLVED"
    ]
    active_animals = {
        str(getattr(case, "animal_id", ""))
        for case in active
        if getattr(case, "animal_id", None)
    }

    treatments = factory.treatment().get_all()
    withdrawal_animals = set()
    for row in treatments:
        animal_id = str(getattr(row, "animal_id", "") or "")
        treated_on = _as_date(getattr(row, "treated_at", None))
        withdrawal_until = _as_date(
            getattr(row, "milk_withdrawal_until", None)
        )

        if (
            animal_id
            and treated_on is not None
            and withdrawal_until is not None
            and treated_on <= today <= withdrawal_until
        ):
            withdrawal_animals.add(animal_id)

    followups_due = 0
    for case in active:
        due = _as_date(getattr(case, "follow_up_due_at", None))
        if due is not None and due <= today:
            followups_due += 1

    return {
        "activeClinicalCases": len(active),
        "activeSickAnimals": len(active_animals),
        "withdrawalAnimals": len(withdrawal_animals),
        "followupsDue": followups_due,
        "data_status": "LIVE_PERSISTED_DATA",
    }


@router.get("/farm/vaccination/summary")
def get_vaccination_summary(container=Depends(get_container)):
    factory = container.repository_factory
    today = OperationalDateAuthority(repository_factory=factory).current_date()
    next_30 = today + timedelta(days=30)

    rows = _vaccination_events(container)
    completed = len(rows)
    overdue = 0
    due_next_30 = 0
    upcoming = []
    animals_with_history = set()

    for payload in rows:
        animal_id = str(payload.get("animal_id") or "")
        if animal_id:
            animals_with_history.add(animal_id)

        next_due = _as_date(payload.get("next_due_date"))
        if next_due is None:
            continue
        if next_due < today:
            overdue += 1
        elif today <= next_due <= next_30:
            due_next_30 += 1

        upcoming.append({
            "animal_id": payload.get("animal_id"),
            "vaccine": payload.get("vaccine") or payload.get("vaccination"),
            "administered_date": str(payload.get("administered_date") or "")[:10],
            "next_due_date": next_due.isoformat(),
            "batch_number": payload.get("batch_number") or payload.get("batch"),
            "veterinarian": payload.get("veterinarian") or payload.get("operator"),
        })

    upcoming.sort(key=lambda item: item["next_due_date"])

    animal_repo = getattr(container, "animal_repository", None)
    active_animals = []
    if animal_repo is not None and hasattr(animal_repo, "active_animals"):
        active_animals = list(animal_repo.active_animals())
    else:
        repo = factory.animal()
        all_animals = list(repo.get_all()) if hasattr(repo, "get_all") else []
        active_animals = [
            animal for animal in all_animals
            if getattr(animal, "active", True) is not False
        ]

    active_ids = {
        str(getattr(animal, "animal_id", ""))
        for animal in active_animals
        if getattr(animal, "animal_id", None)
    }

    return {
        "vaccinationsRecorded": completed,
        "vaccinationsOverdue": overdue,
        "vaccinationsDueNext30Days": due_next_30,
        "animalsWithNoVaccinationHistory": len(active_ids - animals_with_history),
        "upcomingVaccinations": upcoming[:50],
        "data_status": "LIVE_PERSISTED_DATA",
    }
