from dairyos.herd.masterdata.models import Breed

from dairyos.herd.masterdata.services.master_data_service import (
    MasterDataService
)



def test_breed_creation():


    breed = Breed(

        name="Holstein Friesian",

        category="DAIRY",

        expected_milk_per_day=25,

        maturity_months=24

    )


    assert breed.name == "Holstein Friesian"

    assert breed.expected_milk_per_day == 25



def test_master_data_service():


    service = MasterDataService()


    breed = Breed(

        name="Jersey",

        category="DAIRY",

        expected_milk_per_day=18,

        maturity_months=22

    )


    service.add_breed(breed)


    assert len(service.get_breeds()) == 1
