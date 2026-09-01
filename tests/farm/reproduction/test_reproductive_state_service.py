from datetime import date

import pytest

from dairyos.farm.reproduction.services.reproductive_state_service import (
    ReproductivePolicy,
    ReproductiveStateError,
    ReproductiveStateService,
)


POLICY = ReproductivePolicy(
    voluntary_waiting_period_days=60,
    gestation_days=280,
    dry_off_days_before_calving=60,
)


def test_first_calving_creates_lactation_one_and_dim_zero():
    service = ReproductiveStateService(POLICY)

    state = service.resolve(
        "A1",
        [
            {
                "animal_id": "A1",
                "event_type": "CALVING",
                "event_date": "2026-01-01",
            }
        ],
        as_of_date=date(2026, 1, 1),
    )

    assert state.reproductive_status == "LACTATING"
    assert state.lactation_number == 1
    assert state.days_in_milk == 0


def test_dim_and_vwp_are_date_driven():
    service = ReproductiveStateService(POLICY)

    state = service.resolve(
        "A1",
        [
            {
                "animal_id": "A1",
                "event_type": "CALVING",
                "event_date": "2026-01-01",
            }
        ],
        as_of_date=date(2026, 2, 15),
    )

    assert state.days_in_milk == 45
    assert state.voluntary_waiting_period_end == date(
        2026, 3, 2
    )
    assert state.eligible_to_breed is False


def test_insemination_then_confirmed_pregnancy_produces_days_open_and_ecd():
    service = ReproductiveStateService(POLICY)

    state = service.resolve(
        "A1",
        [
            {
                "animal_id": "A1",
                "event_type": "CALVING",
                "event_date": "2026-01-01",
            },
            {
                "animal_id": "A1",
                "event_type": "INSEMINATION",
                "event_date": "2026-03-10",
            },
            {
                "animal_id": "A1",
                "event_type": "PREGNANCY_CONFIRMED",
                "event_date": "2026-04-05",
            },
        ],
        as_of_date=date(2026, 4, 20),
    )

    assert state.pregnancy_status == "PREGNANT"
    assert state.last_insemination_date == date(2026, 3, 10)
    assert state.days_open == 68
    assert state.expected_calving_date == date(
        2026, 12, 15
    )
    assert state.expected_dry_off_date == date(
        2026, 10, 16
    )


def test_pregnancy_loss_returns_animal_to_open_state():
    service = ReproductiveStateService(POLICY)

    state = service.resolve(
        "A1",
        [
            {
                "animal_id": "A1",
                "event_type": "CALVING",
                "event_date": "2026-01-01",
            },
            {
                "animal_id": "A1",
                "event_type": "INSEMINATION",
                "event_date": "2026-03-10",
            },
            {
                "animal_id": "A1",
                "event_type": "PREGNANCY_CONFIRMED",
                "event_date": "2026-04-05",
            },
            {
                "animal_id": "A1",
                "event_type": "PREGNANCY_LOST",
                "event_date": "2026-05-01",
            },
        ],
        as_of_date=date(2026, 5, 10),
    )

    assert state.pregnancy_status == "NOT_PREGNANT"
    assert state.reproductive_status == "BRED"
    assert state.expected_calving_date is None


def test_pregnancy_confirmation_without_insemination_is_rejected():
    service = ReproductiveStateService(POLICY)

    with pytest.raises(
        ReproductiveStateError,
        match="prior INSEMINATION",
    ):
        service.resolve(
            "A1",
            [
                {
                    "animal_id": "A1",
                    "event_type": "PREGNANCY_CONFIRMED",
                    "event_date": "2026-04-05",
                }
            ],
            as_of_date=date(2026, 4, 6),
        )


def test_insemination_while_pregnant_is_rejected_as_conflicting_operational_state():
    service = ReproductiveStateService(POLICY)

    with pytest.raises(
        ReproductiveStateError,
        match="INSEMINATION",
    ):
        service.resolve(
            "A1",
            [
                {
                    "animal_id": "A1",
                    "event_type": "CALVING",
                    "event_date": "2026-01-01",
                },
                {
                    "animal_id": "A1",
                    "event_type": "INSEMINATION",
                    "event_date": "2026-03-10",
                },
                {
                    "animal_id": "A1",
                    "event_type": "PREGNANCY_CONFIRMED",
                    "event_date": "2026-04-05",
                },
                {
                    "animal_id": "A1",
                    "event_type": "INSEMINATION",
                    "event_date": "2026-04-10",
                },
            ],
            as_of_date=date(2026, 4, 11),
        )


def test_historical_as_of_date_does_not_see_future_calving():
    service = ReproductiveStateService(POLICY)

    state = service.resolve(
        "A1",
        [
            {
                "animal_id": "A1",
                "event_type": "CALVING",
                "event_date": "2026-08-01",
            }
        ],
        as_of_date=date(2026, 7, 31),
    )

    assert state.lactation_number == 0
    assert state.last_calving_date is None
    assert state.days_in_milk is None
