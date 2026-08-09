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



def test_animal_operational_state_persists_after_event_projection():

    repository = (
        AnimalOperationalStateRepository()
    )


    projection = (
        AnimalEventProjection(
            repository=repository
        )
    )


    event = FarmOperationEvent(
        event_type="insemination_recorded",
        animal_id="COW-001",
        operator="vet",
        payload={
            "semen_type": "SEXED",
            "bull_reference": "BULL-77",
            "technician": "Dr-Ali",
        },
        timestamp=datetime.now(UTC),
    )


    projection.apply(
        event
    )


    restored = (
        repository.get(
            "COW-001"
        )
    )


    assert restored is not None

    assert restored.animal_id == "COW-001"

    assert restored.reproduction_status == (
        "INSEMINATED"
    )

    assert restored.pregnancy_status == (
        "PENDING_CONFIRMATION"
    )

    assert restored.last_breeding_event[
        "bull_reference"
    ] == "BULL-77"



def test_lifecycle_event_updates_operational_state_projection():

    repository = (
        AnimalOperationalStateRepository()
    )


    projection = (
        AnimalEventProjection(
            repository=repository
        )
    )


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


    projection.apply(
        event
    )


    restored = (
        repository.get(
            "HEIFER-001"
        )
    )


    assert restored is not None

    assert restored.animal_id == (
        "HEIFER-001"
    )

    assert restored.previous_lifecycle_status == (
        "CALF"
    )

    assert restored.lifecycle_status == (
        "HEIFER"
    )

    assert restored.lifecycle_stage == (
        "HEIFER"
    )

    assert restored.animal_status == (
        "HEIFER"
    )

    assert restored.last_lifecycle_event[
        "event_type"
    ] == (
        "lifecycle_changed"
    )

    assert restored.last_lifecycle_event[
        "new_status"
    ] == (
        "HEIFER"
    )

def test_animal_operational_state_survives_repository_restart(tmp_path):

    first_repository = (
        AnimalOperationalStateRepository(
            storage_path=(
                tmp_path /
                "animal_states.json"
            )
        )
    )


    first_projection = (
        AnimalEventProjection(
            repository=first_repository
        )
    )


    event = FarmOperationEvent(
        event_type="lifecycle_changed",
        animal_id="COW-RESTART-001",
        operator="farm_manager",
        payload={
            "previous_status": "HEIFER",
            "new_status": "LACTATING",
            "location": "MILKING_SHED",
        },
        timestamp=datetime.now(UTC),
    )


    first_projection.apply(
        event
    )


    #
    # Simulate application restart.
    #
    second_repository = (
        AnimalOperationalStateRepository(
            storage_path=(
                tmp_path /
                "animal_states.json"
            )
        )
    )


    restored = (
        second_repository.get(
            "COW-RESTART-001"
        )
    )


    assert restored is not None

    assert restored.animal_id == (
        "COW-RESTART-001"
    )

    assert restored.lifecycle_status == (
        "LACTATING"
    )

    assert restored.animal_status == (
        "LACTATING"
    )

    assert restored.last_lifecycle_event[
        "new_status"
    ] == (
        "LACTATING"
    )

