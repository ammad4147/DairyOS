from dairyos.data.models.animal import Animal
from dairyos.data.repositories.animal_repository import (
    AnimalRepository,
)



def test_repository_add_and_count():

    repository = AnimalRepository()


    repository.add(

        Animal(
            animal_id="COW-001",
            animal_type="COW",
            status="ACTIVE",
        )

    )


    assert repository.count() == 1



def test_repository_lookup():

    repository = AnimalRepository()


    animal = Animal(
        animal_id="COW-002",
        animal_type="COW",
        status="ACTIVE",
        location="SHED-A",
        production_group="MILKING",
    )


    repository.add(animal)


    result = repository.get_by_animal_id(
        "COW-002"
    )


    assert result == animal



def test_repository_filters():

    repository = AnimalRepository()


    repository.add(

        Animal(
            animal_id="COW-003",
            animal_type="COW",
            status="ACTIVE",
            location="SHED-A",
            production_group="MILKING",
        )

    )


    repository.add(

        Animal(
            animal_id="CALF-001",
            animal_type="CALF",
            status="ACTIVE",
            location="CALF-SHED",
            production_group="CALVES",
        )

    )


    assert len(
        repository.find_by_location("SHED-A")
    ) == 1


    assert len(
        repository.find_by_group("CALVES")
    ) == 1


    assert len(
        repository.active_animals()
    ) == 2



def test_repository_inactive_animals():

    repository = AnimalRepository()


    animal = Animal(
        animal_id="COW-004",
        animal_type="COW",
        status="ACTIVE",
    )


    animal.deactivate()


    repository.add(animal)


    assert len(
        repository.inactive_animals()
    ) == 1

