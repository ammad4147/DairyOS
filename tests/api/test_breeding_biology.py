from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dairyos.api.breeding_biology import (
    BreedingLifecycleRequest,
    _assert_mature_female,
    _normalize_requested_event,
    _resolve_state,
    _state_api_value,
)
from dairyos.farm.operations.models.breeding_record import BreedingRecord


def _record(event_type: str, result: str, when: datetime) -> BreedingRecord:
    return BreedingRecord(
        animal_id="A1",
        event_type=event_type,
        result=result,
        technician="Vet",
        timestamp=when,
    )


@pytest.mark.parametrize(
    ("sex", "lifecycle"),
    [
        ("MALE", "BULL"),
        ("MALE", "CALF"),
        ("FEMALE", "CALF"),
    ],
)
def test_breeding_gate_rejects_bulls_and_calves(sex, lifecycle):
    animal = SimpleNamespace(active=True, sex=sex, lifecycle_status=lifecycle)
    with pytest.raises(HTTPException) as exc:
        _assert_mature_female(animal)
    assert exc.value.status_code == 422


@pytest.mark.parametrize("lifecycle", ["HEIFER", "LACTATING", "DRY"])
def test_breeding_gate_accepts_mature_female_lifecycles(lifecycle):
    _assert_mature_female(
        SimpleNamespace(active=True, sex="FEMALE", lifecycle_status=lifecycle)
    )


def test_negative_pd_closes_the_insemination_cycle_and_returns_open():
    records = [
        _record("insemination", "RECORDED", datetime(2026, 3, 10, 8, 0)),
        _record("pregnancy_negative", "NEGATIVE", datetime(2026, 4, 5, 9, 0)),
    ]
    state = _resolve_state("A1", records, as_of_date=date(2026, 4, 5))
    assert state.pregnancy_status == "NOT_PREGNANT"
    assert state.reproductive_status == "OPEN"
    assert _state_api_value(state) == "OPEN"


def test_positive_pd_moves_inseminated_animal_to_pregnant():
    records = [
        _record("insemination", "RECORDED", datetime(2026, 3, 10, 8, 0)),
        _record("pregnancy_confirmed", "POSITIVE", datetime(2026, 4, 5, 9, 0)),
    ]
    state = _resolve_state("A1", records, as_of_date=date(2026, 4, 5))
    assert _state_api_value(state) == "PREGNANT"


def test_calving_removes_pregnant_state_and_starts_lactation():
    records = [
        _record("insemination", "RECORDED", datetime(2025, 11, 1, 8, 0)),
        _record("pregnancy_confirmed", "POSITIVE", datetime(2025, 12, 1, 9, 0)),
        _record("calving", "RECORDED", datetime(2026, 8, 11, 6, 0)),
    ]
    state = _resolve_state("A1", records, as_of_date=date(2026, 8, 11))
    assert state.pregnancy_status == "NOT_PREGNANT"
    assert _state_api_value(state) == "LACTATING"


def test_pd_request_is_normalized_to_a_factual_positive_or_negative_event():
    positive = BreedingLifecycleRequest(
        animal_id="A1", event_type="pregnancy_diagnosis", result="positive"
    )
    negative = BreedingLifecycleRequest(
        animal_id="A1", event_type="pregnancy_check", result="negative"
    )

    # A PD form submission remains a factual diagnosis encounter so analytics
    # can count the manual check itself. The result drives the reproductive
    # state projection to PREGNANT or OPEN without inventing another event.
    assert _normalize_requested_event(positive) == ("pregnancy_diagnosis", "pregnant")
    assert _normalize_requested_event(negative) == ("pregnancy_diagnosis", "open")