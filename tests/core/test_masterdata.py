from dairyos.core.masterdata.models import (
    Farm,
    Location,
    Breed,
    AnimalType
)

from dairyos.core.masterdata.services.master_data_service import (
    MasterDataService
)



def test_master_data_creation():

    farm = Farm(
        name="Trident Dairies",
        location="Lahore",
        capacity=50
    )

    assert farm.status == "ACTIVE"



def test_master_data_service():

    service = MasterDataService()

    breed = Breed(
        name="Holstein Friesian",
        origin="Netherlands"
    )

    result = service.add_breed(
        breed
    )

    assert result.name == "Holstein Friesian"



def test_animal_category():

    animal = AnimalType(
        name="Milking Cow",
        description="Adult lactating animal"
    )

    assert animal.name == "Milking Cow"
