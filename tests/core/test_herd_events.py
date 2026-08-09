from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.herd.services.animal_event_projection import (
    AnimalEventProjection,
)

from dairyos.farm.herd.models.animal_operational_state import (
    AnimalOperationalState,
)


def test_animal_operation_event_creation():

    event = FarmOperationEvent(
        event_type="BIRTH",
        animal_id="HF-0001",
        operator="farm_manager",
        payload={
            "description": "New calf born",
        },
    )


    assert event.event_type == "BIRTH"
    assert event.animal_id == "HF-0001"
    assert event.operator == "farm_manager"



def test_animal_event_projection_updates_state():

    projection = AnimalEventProjection()


    event = FarmOperationEvent(
        event_type="health_observation_recorded",
        animal_id="HF-0001",
        operator="vet",
        payload={
            "observation": "Temperature elevated",
        },
    )


    state = projection.apply(
        event
    )


    assert isinstance(
        state,
        AnimalOperationalState,
    )


    assert state.animal_id == "HF-0001"


    assert state.health_status == (
        "ATTENTION_REQUIRED"
    )


    assert state.attention_required is True



def test_animal_breeding_event_projection():

    projection = AnimalEventProjection()


    event = FarmOperationEvent(
        event_type="insemination_recorded",
        animal_id="HF-0002",
        operator="technician",
        payload={
            "semen_type": "SEXED",
            "bull_reference": "BULL-101",
            "technician": "AI Technician",
        },
    )


    state = projection.apply(
        event
    )


    assert state.reproduction_status == (
        "INSEMINATED"
    )


    assert state.pregnancy_status == (
        "PENDING_CONFIRMATION"
    )


    assert state.breeding_attempts == 1



def test_animal_milk_event_projection():

    projection = AnimalEventProjection()


    event = FarmOperationEvent(
        event_type="milk_recorded",
        animal_id="HF-0003",
        operator="milker",
        payload={
            "litres": 25.0,
        },
    )


    state = projection.apply(
        event
    )


    assert state.milk_today_litres == 25.0


    assert state.production_status == (
        "LACTATING"
    )
