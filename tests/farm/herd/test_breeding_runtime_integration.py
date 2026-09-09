from dairyos.application.application_runtime import (
    ApplicationRuntime,
)

from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)


def test_record_breeding_updates_animal_operational_state(tmp_path):
    from dairyos.data.database.session import SessionLocal
    from dairyos.data.models.animal import Animal
    with SessionLocal() as session:
        if session.query(Animal).filter_by(animal_id="COW-001").first() is None:
            session.add(Animal(animal_id="COW-001", animal_type="COW"))
            session.commit()
    runtime = ApplicationRuntime(
        animal_operational_state_repository=(
            AnimalOperationalStateRepository(
                storage_path=(
                    tmp_path /
                    "animal_operational_states.json"
                )
            )
        )
    )


    runtime.farm_operations_runtime.record_breeding(

        animal_id="COW-001",

        event_type="insemination",

        result="completed",

        technician="Dr Vet",

    )


    state = (
        runtime
        .animal_operational_state_repository
        .get(
            "COW-001"
        )
    )


    assert state is not None

    assert state.reproduction_status == (
        "insemination"
    )

    assert state.breeding_attempts == 1

    assert state.last_breeding_event[
        "result"
    ] == (
        "completed"
    )
