from datetime import date


from dairyos.application.application_runtime import (
    ApplicationRuntime,
)


from dairyos.herd.models import (
    Animal,
    AnimalStatus,
)



def create_animal():

    return Animal(

        animal_id="HF-INT-001",

        ear_tag="INT-001",

        breed="Holstein Friesian",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.HEIFER,

        location="Heifer Area",

    )



def test_lifecycle_engine_updates_animal_operational_state_through_runtime():

    runtime = ApplicationRuntime()


    animal = create_animal()


    runtime.lifecycle_engine.transition(

        animal,

        AnimalStatus.MILKING_COW,

    )


    state = (
        runtime
        .animal_operational_state_repository
        .get(
            "HF-INT-001"
        )
    )


    assert state is not None


    assert state.lifecycle_status == (
        "MILKING_COW"
    )


    assert state.lifecycle_stage == (
        "MILKING_COW"
    )


    assert state.previous_lifecycle_status == (
        "HEIFER"
    )
