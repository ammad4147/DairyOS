from datetime import date


from dairyos.farm.herd.models.animal import (
    Animal,
)

from dairyos.farm.herd.repository.animal_repository import (
    AnimalRepository,
)

from dairyos.farm.herd.services.animal_registry_service import (
    AnimalRegistryService,
)



def test_register_dairy_animal():


    service = AnimalRegistryService(
        AnimalRepository()
    )


    cow = Animal(

        animal_id="HF-001",

        tag_number="104",

        breed="Holstein Friesian",

        gender="female",

        birth_date=date(
            2023,
            1,
            1,
        ),

        status="milking",

        lactation_number=2,

        is_milking=True,
    )


    service.register(
        cow
    )


    assert service.herd_count() == 1

    assert cow.tag_number == "104"
