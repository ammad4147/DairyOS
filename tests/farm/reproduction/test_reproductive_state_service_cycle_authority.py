from datetime import date

import pytest

from dairyos.farm.operations.models.breeding_record import BreedingRecord
from dairyos.farm.reproduction.services.reproductive_state_service import (
    ReproductivePolicy,
    ReproductiveStateService,
)


POLICY = ReproductivePolicy(
    voluntary_waiting_period_days=60,
    gestation_days=283,
    dry_off_days_before_calving=60,
)


def _service():
    return ReproductiveStateService(POLICY)


def test_operational_breeding_record_can_be_resolved():
    record = BreedingRecord(
        animal_id="A1",
        event_type="insemination",
        result="completed",
        technician="Dr Vet",
    )

    record.timestamp = record.timestamp.replace(
        year=2026,
        month=3,
        day=10,
    )

    state = _service().resolve(
        "A1",
        [record],
        as_of_date=date(2026, 4, 20),
    )

    assert state.animal_id == "A1"
    assert state.last_insemination_date == date(2026, 3, 10)


def test_post_calving_history_does_not_drive_current_cycle():
    events = [
        {
            "animal_id": "A1",
            "event_type": "INSEMINATION",
            "event_date": "2025-03-01",
        },
        {
            "animal_id": "A1",
            "event_type": "PREGNANCY_CONFIRMED",
            "event_date": "2025-04-01",
        },
        {
            "animal_id": "A1",
            "event_type": "CALVING",
            "event_date": "2025-12-09",
        },
    ]

    state = _service().resolve(
        "A1",
        events,
        as_of_date=date(2026, 1, 15),
    )

    assert state.last_calving_date == date(2025, 12, 9)
    assert state.last_insemination_date is None
    assert state.pregnancy_status == "NOT_PREGNANT"


def test_pregnancy_diagnosis_is_a_confirmation_when_positive():
    events = [
        {
            "animal_id": "A1",
            "event_type": "insemination",
            "event_date": "2026-03-10",
        },
        {
            "animal_id": "A1",
            "event_type": "pregnancy_diagnosis",
            "result": "pregnant",
            "event_date": "2026-04-05",
        },
    ]

    state = _service().resolve(
        "A1",
        events,
        as_of_date=date(2026, 4, 20),
    )

    assert state.pregnancy_status == "PREGNANT"
    assert state.pregnancy_confirmed_date == date(2026, 4, 5)


def test_pregnancy_negative_returns_open():
    events = [
        {
            "animal_id": "A1",
            "event_type": "insemination",
            "event_date": "2026-03-10",
        },
        {
            "animal_id": "A1",
            "event_type": "pregnancy_negative",
            "result": "open",
            "event_date": "2026-04-05",
        },
    ]

    state = _service().resolve(
        "A1",
        events,
        as_of_date=date(2026, 4, 20),
    )

    assert state.pregnancy_status == "NOT_PREGNANT"
    assert state.reproductive_status == "OPEN"


def test_post_calving_insemination_starts_new_cycle():
    events = [
        {
            "animal_id": "A1",
            "event_type": "insemination",
            "event_date": "2025-03-01",
        },
        {
            "animal_id": "A1",
            "event_type": "pregnancy_confirmed",
            "event_date": "2025-04-01",
        },
        {
            "animal_id": "A1",
            "event_type": "calving",
            "event_date": "2025-12-09",
        },
        {
            "animal_id": "A1",
            "event_type": "insemination",
            "event_date": "2026-03-01",
        },
    ]

    state = _service().resolve(
        "A1",
        events,
        as_of_date=date(2026, 3, 15),
    )

    assert state.last_calving_date == date(2025, 12, 9)
    assert state.last_insemination_date == date(2026, 3, 1)
    assert state.reproductive_status == "BRED"