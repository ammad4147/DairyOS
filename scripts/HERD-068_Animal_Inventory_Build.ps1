$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-068 Animal Inventory Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\inventory\models",
"dairyos\herd\inventory\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class AnimalInventory:


    animal_id: str

    breed: str

    age_months: int

    category: str

    lifecycle_status: str

    asset_status: str
'@ | Set-Content `
"dairyos\herd\inventory\models\animal_inventory.py"



@'
from ..models.animal_inventory import AnimalInventory



class AnimalInventoryService:



    def evaluate(

        self,

        animal_id,

        breed,

        age_months,

        category

    ):


        if age_months < 12:

            lifecycle_status = "CALF"


        elif age_months < 24:

            lifecycle_status = "HEIFER"


        elif category.lower() == "pregnant heifer":

            lifecycle_status = "PRE-CALVING"


        elif category.lower() == "lactating cow":

            lifecycle_status = "LACTATING"


        else:

            lifecycle_status = "ACTIVE"



        return AnimalInventory(

            animal_id,

            breed,

            age_months,

            category,

            lifecycle_status,

            "ACTIVE"

        )
'@ | Set-Content `
"dairyos\herd\inventory\services\animal_inventory_service.py"



@'
from dairyos.herd.inventory.services.animal_inventory_service import AnimalInventoryService



def test_animal_id():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.animal_id == "HF-1025"



def test_breed():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.breed == "Holstein Friesian"



def test_age():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.age_months == 26



def test_category():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.category == "Pregnant Heifer"



def test_precalving_status():

    result = AnimalInventoryService().evaluate(

        "HF-1025",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.lifecycle_status == "PRE-CALVING"



def test_calf_status():

    result = AnimalInventoryService().evaluate(

        "HF-1026",

        "Holstein Friesian",

        6,

        "Calf"

    )

    assert result.lifecycle_status == "CALF"



def test_heifer_status():

    result = AnimalInventoryService().evaluate(

        "HF-1027",

        "Holstein Friesian",

        18,

        "Heifer"

    )

    assert result.lifecycle_status == "HEIFER"



def test_lactating_status():

    result = AnimalInventoryService().evaluate(

        "HF-1028",

        "Holstein Friesian",

        36,

        "Lactating Cow"

    )

    assert result.lifecycle_status == "LACTATING"



def test_asset_status():

    result = AnimalInventoryService().evaluate(

        "HF-1029",

        "Holstein Friesian",

        30,

        "Pregnant Heifer"

    )

    assert result.asset_status == "ACTIVE"



def test_inventory_flow():

    result = AnimalInventoryService().evaluate(

        "HF-1030",

        "Holstein Friesian",

        26,

        "Pregnant Heifer"

    )

    assert result.lifecycle_status == "PRE-CALVING"
'@ | Set-Content `
"tests\core\test_animal_inventory.py"



Write-Host "HERD-068 Animal Inventory Build Complete"