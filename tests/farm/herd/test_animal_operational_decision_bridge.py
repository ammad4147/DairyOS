from datetime import datetime, UTC


from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)


from dairyos.farm.herd.services.animal_event_projection import (
    AnimalEventProjection,
)


from dairyos.farm.herd.services.animal_operational_bridge import (
    AnimalOperationalBridge,
)


from dairyos.farm.herd.models.animal_operational_state import (
    AnimalOperationalState,
)



class TestAnimalIntelligenceService:

    def evaluate(
        self,
        state: AnimalOperationalState,
    ):

        state.add_intelligence_attention(
            "Milk production below expected level"
        )

        return state



def test_animal_intelligence_creates_operational_decision():

    repository = (
        AnimalOperationalStateRepository()
    )


    projection = (
        AnimalEventProjection(
            repository=repository
        )
    )


    bridge = (
        AnimalOperationalBridge(
            projection=projection,
            intelligence_service=(
                TestAnimalIntelligenceService()
            ),
        )
    )


    event = FarmOperationEvent(

        event_type="milk_recorded",

        animal_id="COW-DECISION-001",

        operator="worker",

        payload={
            "milk_litres": 10,
        },

        timestamp=datetime.now(UTC),

    )


    result = (
        bridge.process_with_decisions(
            event
        )
    )


    assert result["state"] is not None


    assert (
        result["state"].animal_id
        ==
        "COW-DECISION-001"
    )


    assert (
        len(result["decisions"])
        ==
        1
    )


    decision = (
        result["decisions"][0]
    )


    assert (
        decision.source
        ==
        "animal:COW-DECISION-001"
    )


    assert (
        decision.owner_action_required
        is True
    )


    assert (
        decision.status
        ==
        "CREATED"
    )
