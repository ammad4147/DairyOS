from datetime import date

from dairyos.herd.models import (
    Animal,
    AnimalStatus
)

from dairyos.herd.lifecycle.services.lifecycle_engine import (
    LifecycleEngine
)

from dairyos.herd.lifecycle.services.movement_engine import (
    MovementEngine
)



def create_animal():

    return Animal(

        animal_id="HF-1001",

        ear_tag="1001",

        breed="Holstein Friesian",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.HEIFER,

        location="Heifer Area"

    )



def test_lifecycle_transition():

    animal = create_animal()

    engine = LifecycleEngine()


    event = engine.transition(

        animal,

        AnimalStatus.MILKING_COW

    )


    assert event.new_status == "MILKING_COW"

    assert animal.status == AnimalStatus.MILKING_COW



def test_animal_movement():

    animal = create_animal()

    engine = MovementEngine()


    movement = engine.move(

        animal,

        "Main Dairy Shed",

        "Ready for production"

    )


    assert movement.to_location == "Main Dairy Shed"

    assert animal.location == "Main Dairy Shed"
