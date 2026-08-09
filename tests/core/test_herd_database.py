from datetime import date


from dairyos.herd.database.models import (

    AnimalRecord

)


from dairyos.herd.database.repositories import (

    DatabaseAnimalRepository

)



def test_database_record_save():


    repository = DatabaseAnimalRepository()


    record = AnimalRecord(

        animal_id="HF-3001",

        ear_tag="3001",

        breed="Holstein Friesian",

        gender="FEMALE",

        birth_date=date.today(),

        status="MILKING_COW",

        location="Main Shed"

    )


    repository.save(record)


    result = repository.find(

        "HF-3001"

    )


    assert result.animal_id == "HF-3001"



def test_database_count():


    repository = DatabaseAnimalRepository()


    repository.save(

        AnimalRecord(

            animal_id="HF-3002",

            ear_tag="3002",

            breed="HF",

            gender="FEMALE",

            birth_date=date.today(),

            status="CALF",

            location="Calf Shed"

        )

    )


    assert repository.count() == 1
