from datetime import date


from dairyos.herd.models import (

    Animal,

    AnimalStatus

)


from dairyos.herd.intelligence.services.herd_metrics import (

    HerdMetricsService

)



def test_herd_snapshot():


    animals = [

        Animal(

            animal_id="001",

            ear_tag="001",

            breed="HF",

            gender="FEMALE",

            birth_date=date.today(),

            status=AnimalStatus.MILKING_COW,

            location="Shed"

        ),


        Animal(

            animal_id="002",

            ear_tag="002",

            breed="HF",

            gender="FEMALE",

            birth_date=date.today(),

            status=AnimalStatus.HEIFER,

            location="Heifer Area"

        )

    ]



    service = HerdMetricsService()


    snapshot = service.calculate(

        animals

    )


    assert snapshot.total_animals == 2

    assert snapshot.milking_cows == 1

    assert snapshot.heifers == 1
