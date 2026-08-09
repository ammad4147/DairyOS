from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.state.operational_state_repository import (
    OperationalStateRepository,
)


def test_operational_state_survives_service_restart():

    repository = OperationalStateRepository()


    service_one = FarmOperationalStateService(
        repository=repository
    )


    event = FarmOperationEvent(

        event_type="milk_recorded",

        animal_id=None,

        operator="Farm Manager",

        payload={
            "shift": "morning",
            "litres": 620,
        },

    )


    service_one.process_event(event)



    service_two = FarmOperationalStateService(
        repository=repository
    )


    state = service_two.get_state()



    assert (
        state.milk_status["morning"]["litres"]
        ==
        620
    )
