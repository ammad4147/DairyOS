from datetime import date


from dairyos.application.application_runtime import (
    ApplicationRuntime,
)


from dairyos.herd.models import (
    Animal,
    AnimalStatus,
)



def test_lifecycle_engine_runtime_updates_animal_operational_state():

    runtime = ApplicationRuntime()


    animal = Animal(

        animal_id="COW-900",

        ear_tag="900",

        breed="Holstein Friesian",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.HEIFER,

        location="HEIFER_AREA",

    )


    runtime.lifecycle_engine.transition(

        animal,

        AnimalStatus.MILKING_COW,

    )


    state = (
        runtime
        .animal_operational_state_repository
        .get(
            "COW-900"
        )
    )


    assert state is not None

    assert state.lifecycle_status == (
        "MILKING_COW"
    )

    assert state.previous_lifecycle_status == (
        "HEIFER"
    )

    assert state.last_lifecycle_event[
        "event_type"
    ] == (
        "lifecycle_changed"
    )