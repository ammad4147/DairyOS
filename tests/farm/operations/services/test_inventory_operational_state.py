from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.state.memory_operational_state_repository import (
    MemoryOperationalStateRepository,
)

from dairyos.farm.operations.state.operational_decision_service import (
    OperationalDecisionService,
)



def test_inventory_status_updates_operational_state():

    repository = MemoryOperationalStateRepository()

    service = FarmOperationalStateService(
        repository=repository
    )


    event = FarmOperationEvent(

        event_type="inventory_status_recorded",

        animal_id=None,

        operator="manager",

        payload={

            "inventory_type": "feed",

            "item": "silage",

            "details": {

                "available_quantity": 500,

                "coverage_days": 5,

                "status": "CRITICAL",

            },

        },

    )


    state = service.process_event(
        event
    )


    assert "feed" in state.inventory_status

    assert (
        state.inventory_status["feed"]["status"]
        ==
        "CRITICAL"
    )



def test_inventory_state_persists():

    repository = MemoryOperationalStateRepository()

    service = FarmOperationalStateService(
        repository=repository
    )


    event = FarmOperationEvent(

        event_type="inventory_status_recorded",

        animal_id=None,

        operator="manager",

        payload={

            "inventory_type": "medicine",

            "item": "antibiotic",

            "details": {

                "coverage_months": 0.5,

                "status": "CRITICAL",

            },

        },

    )


    service.process_event(
        event
    )


    loaded = repository.get_current(
        "TRIDENT-DAIRIES"
    )


    assert loaded is not None

    assert (
        loaded.inventory_status["medicine"]["status"]
        ==
        "CRITICAL"
    )



def test_inventory_creates_decision():

    repository = MemoryOperationalStateRepository()

    state_service = FarmOperationalStateService(
        repository=repository
    )


    state_service.process_event(

        FarmOperationEvent(

            event_type="inventory_status_recorded",

            animal_id=None,

            operator="manager",

            payload={

                "inventory_type": "feed",

                "item": "hay",

                "details": {

                    "status": "CRITICAL",

                },

            },

        )

    )


    decision_service = OperationalDecisionService(
        state_service
    )


    decisions = decision_service.evaluate()


    assert any(

        decision["type"] == "inventory"

        for decision in decisions

    )
