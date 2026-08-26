from datetime import date

from dairyos.farm.reproduction.services.reproductive_state_service import (
    ReproductivePolicy,
    ReproductiveStateError,
    ReproductiveStateService,
)


POLICY = ReproductivePolicy(
    voluntary_waiting_period_days=60,
    gestation_days=283,
    dry_off_days_before_calving=60,
)


def event(event_type, when, result=None):
    return {
        "animal_id": "A1",
        "event_type": event_type,
        "event_date": when,
        "result": result,
    }


def test_open_cow_has_no_fabricated_days_open():
    state = ReproductiveStateService(POLICY).resolve(
        "A1",
        [event("CALVING", "2026-01-01")],
        as_of_date=date(2026, 4, 15),
    )
    assert state.pregnancy_status == "NOT_PREGNANT"
    assert state.days_open is None
    assert state.reproductive_status == "LACTATING"


def test_negative_pregnancy_returns_to_open_not_bred():
    state = ReproductiveStateService(POLICY).resolve(
        "A1",
        [
            event("CALVING", "2026-01-01"),
            event("INSEMINATION", "2026-03-10"),
            event("PREGNANCY_CONFIRMED", "2026-04-05", "confirmed"),
            event("PREGNANCY_NEGATIVE", "2026-05-01", "negative"),
        ],
        as_of_date=date(2026, 5, 2),
    )
    assert state.pregnancy_status == "NOT_PREGNANT"
    assert state.reproductive_status == "OPEN"
    assert state.days_open is None


def test_insemination_while_pregnant_is_rejected():
    try:
        ReproductiveStateService(POLICY).resolve(
            "A1",
            [
                event("CALVING", "2026-01-01"),
                event("INSEMINATION", "2026-03-10"),
                event("PREGNANCY_CONFIRMED", "2026-04-05", "confirmed"),
                event("INSEMINATION", "2026-04-10"),
            ],
            as_of_date=date(2026, 4, 11),
        )
    except ReproductiveStateError as exc:
        assert "pregnancy" in str(exc).lower()
    else:
        raise AssertionError("A second service during active pregnancy must be rejected")


def test_confirmed_pregnancy_uses_actual_service_date_for_days_open_and_ecd():
    state = ReproductiveStateService(POLICY).resolve(
        "A1",
        [
            event("CALVING", "2026-01-01"),
            event("INSEMINATION", "2026-03-10"),
            event("PREGNANCY_CONFIRMED", "2026-04-05", "confirmed"),
        ],
        as_of_date=date(2026, 4, 20),
    )
    assert state.pregnancy_status == "PREGNANT"
    assert state.days_open == 68
    assert state.expected_calving_date == date(2026, 12, 18)


def test_unanchored_pregnancy_confirmation_is_rejected_not_invented():
    try:
        ReproductiveStateService(POLICY).resolve(
            "A1",
            [event("PREGNANCY_CONFIRMED", "2026-04-05", "confirmed")],
            as_of_date=date(2026, 4, 6),
        )
    except ReproductiveStateError as exc:
        assert "prior INSEMINATION" in str(exc)
    else:
        raise AssertionError("Pregnancy must not be invented without a recorded service")
