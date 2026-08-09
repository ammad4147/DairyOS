from dairyos.data.models.animal import Animal


def test_animal_creation():

    animal = Animal(
        animal_id="COW-001",
        animal_type="COW",
        status="ACTIVE",
    )


    assert animal.animal_id == "COW-001"

    assert animal.animal_type == "COW"

    assert animal.status == "ACTIVE"

    assert animal.active is True



def test_animal_activation_cycle():

    animal = Animal(
        animal_id="COW-002",
        animal_type="COW",
        status="ACTIVE",
    )


    animal.deactivate()


    assert animal.active is False

    assert animal.status == "INACTIVE"


    animal.activate()


    assert animal.active is True

    assert animal.status == "ACTIVE"

