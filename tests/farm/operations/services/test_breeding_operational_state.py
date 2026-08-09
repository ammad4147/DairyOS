from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)


def test_breeding_event_updates_operational_state():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(

        event_type="breeding_recorded",

        animal_id="COW-001",

        operator="Technician",

        payload={

            "event_type": "insemination",

            "result": "completed",

            "technician": "Dr Vet",

        },

    )


    state = service.process_event(
        event
    )


    assert (
        state.breeding_status["COW-001"]["event_type"]
        ==
        "insemination"
    )


    assert (
        state.breeding_status["COW-001"]["result"]
        ==
        "completed"
    )



def test_breeding_state_is_in_summary():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(

        event_type="breeding_recorded",

        animal_id="COW-002",

        operator="Technician",

        payload={

            "event_type": "pregnancy_check",

            "result": "confirmed",

            "technician": "Dr Vet",

        },

    )


    summary = service.process_event(
        event
    ).summary()


    assert (
        "COW-002"
        in summary["breeding_status"]
    )
