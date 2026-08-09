from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.state.memory_operational_state_repository import (
    MemoryOperationalStateRepository,
)



def test_equipment_status_updates_operational_state():

    repository = MemoryOperationalStateRepository()

    service = FarmOperationalStateService(
        repository=repository
    )


    event = FarmOperationEvent(

        event_type="equipment_status_recorded",

        animal_id=None,

        operator="manager",

        payload={

            "equipment_id": "MILK-MACHINE-01",

            "details": {

                "equipment_name": "Milking Machine",

                "operational_status": "ATTENTION",

                "maintenance_priority": "HIGH",

                "action": "Immediate maintenance required",

            },

        },

    )


    state = service.process_event(
        event
    )


    assert (
        "MILK-MACHINE-01"
        in
        state.equipment_status
    )


    assert (
        state.equipment_status["MILK-MACHINE-01"]
        ["operational_status"]
        ==
        "ATTENTION"
    )



def test_equipment_state_persists():

    repository = MemoryOperationalStateRepository()

    service = FarmOperationalStateService(
        repository=repository
    )


    service.process_event(

        FarmOperationEvent(

            event_type="equipment_status_recorded",

            animal_id=None,

            operator="manager",

            payload={

                "equipment_id": "TRACTOR-01",

                "details": {

                    "operational_status": "OPERATIONAL",

                },

            },

        )

    )


    loaded = repository.get_current(
        "TRIDENT-DAIRIES"
    )


    assert loaded is not None


    assert (
        loaded.equipment_status["TRACTOR-01"]
        ["operational_status"]
        ==
        "OPERATIONAL"
    )
