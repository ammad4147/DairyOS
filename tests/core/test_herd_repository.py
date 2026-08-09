from datetime import date


from dairyos.herd.models import (

    Animal,

    AnimalStatus

)


from dairyos.herd.repositories import (

    AnimalRepository

)


from dairyos.herd.services.animal_service import (

    AnimalService

)



def test_repository_save():

    repository = AnimalRepository()


    animal = Animal(

        animal_id="HF-2001",

        ear_tag="2001",

        breed="Holstein Friesian",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.CALF,

        location="Calf Shed"

    )


    repository.save(animal)


    result = repository.get_by_id(

        "HF-2001"

    )


    assert result.animal_id == "HF-2001"



def test_service_registration():

    repository = AnimalRepository()


    service = AnimalService(

        repository

    )


    animal = Animal(

        animal_id="HF-2002",

        ear_tag="2002",

        breed="HF",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.HEIFER,

        location="Heifer Area"

    )


    service.register(animal)


    result = service.find(

        "HF-2002"

    )


    assert result.status == AnimalStatus.HEIFER



def test_repository_delete():

    repository = AnimalRepository()


    animal = Animal(

        animal_id="HF-2003",

        ear_tag="2003",

        breed="HF",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.CALF,

        location="Calf Shed"

    )


    repository.save(animal)


    assert repository.delete(

        "HF-2003"

    ) is True
