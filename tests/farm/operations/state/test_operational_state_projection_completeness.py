from datetime import datetime, UTC


from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)



def test_lifecycle_event_projects_to_farm_operational_state():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(

        event_type="lifecycle_changed",

        animal_id="HEIFER-001",

        operator="farm_manager",

        payload={

            "previous_status": "CALF",

            "new_status": "HEIFER",

            "location": "CALF_SHED",

        },

        timestamp=datetime.now(UTC),

    )


    state = service.process_event(
        event
    )


    assert (
        "HEIFER-001"
        in state.animals
    )


    assert (
        state.animals["HEIFER-001"]["lifecycle"]["new_status"]
        ==
        "HEIFER"
    )



def test_insemination_event_projects_to_farm_breeding_status():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(

        event_type="insemination_recorded",

        animal_id="COW-001",

        operator="vet",

        payload={

            "semen_type": "SEXED",

            "bull_reference": "BULL-77",

        },

        timestamp=datetime.now(UTC),

    )


    state = service.process_event(
        event
    )


    assert (
        "COW-001"
        in state.breeding_status
    )


    assert (
        state.breeding_status["COW-001"]["bull_reference"]
        ==
        "BULL-77"
    )



def test_pregnancy_confirmation_projects_to_farm_breeding_status():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(

        event_type="pregnancy_confirmed",

        animal_id="COW-001",

        operator="vet",

        payload={

            "confirmed": True,

        },

        timestamp=datetime.now(UTC),

    )


    state = service.process_event(
        event
    )


    assert (
        state.breeding_status["COW-001"]["confirmed"]
        is
        True
    )



def test_unknown_event_is_audited():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(

        event_type="unknown_future_event",

        animal_id=None,

        operator="system",

        payload={},

        timestamp=datetime.now(UTC),

    )


    state = service.process_event(
        event
    )


    assert len(
        state.unhandled_events
    ) == 1


    assert (
        state.unhandled_events[0]["event_type"]
        ==
        "unknown_future_event"
    )