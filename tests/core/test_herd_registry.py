from datetime import date

from dairyos.herd.models import (
    Animal,
    AnimalStatus
)

from dairyos.herd.services.animal_registry import (
    AnimalRegistry
)

from dairyos.herd.services.lifecycle import (
    LifecycleService
)



def test_animal_registration():

    registry = AnimalRegistry()

    animal = Animal(
        animal_id="HF-0001",
        ear_tag="001",
        breed="Holstein Friesian",
        gender="FEMALE",
        birth_date=date.today(),
        status=AnimalStatus.MILKING_COW,
        location="Main Shed"
    )


    registry.register(animal)


    assert registry.count() == 1



def test_lifecycle_change():

    animal = Animal(
        animal_id="HF-0002",
        ear_tag="002",
        breed="HF",
        gender="FEMALE",
        birth_date=date.today(),
        status=AnimalStatus.HEIFER,
        location="Heifer Area"
    )


    service = LifecycleService()


    service.change_status(
        animal,
        AnimalStatus.MILKING_COW
    )


    assert animal.status == AnimalStatus.MILKING_COW
