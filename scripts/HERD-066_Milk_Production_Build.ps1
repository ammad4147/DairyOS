$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-066 Milk Production Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\production\models",
"dairyos\herd\production\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class MilkProduction:


    animal_group: str

    animal_count: int

    expected_milk: float

    actual_milk: float

    variance: float

    status: str
'@ | Set-Content `
"dairyos\herd\production\models\milk_production.py"



@'
from ..models.milk_production import MilkProduction



class MilkProductionService:



    def evaluate(

        self,

        animal_group,

        animal_count,

        expected_milk,

        actual_milk

    ):


        variance = actual_milk - expected_milk


        if actual_milk >= expected_milk:

            status = "ON TARGET"

        else:

            status = "ATTENTION"



        return MilkProduction(

            animal_group,

            animal_count,

            expected_milk,

            actual_milk,

            variance,

            status

        )
'@ | Set-Content `
"dairyos\herd\production\services\milk_production_service.py"



@'
from dairyos.herd.production.services.milk_production_service import MilkProductionService



def test_group():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.animal_group == "Lactating Cows"



def test_animal_count():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.animal_count == 25



def test_expected_milk():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.expected_milk == 625



def test_actual_milk():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.actual_milk == 602



def test_negative_variance():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.variance == -23



def test_attention_status():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.status == "ATTENTION"



def test_target_status():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        600,

        650

    )

    assert result.status == "ON TARGET"



def test_positive_variance():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        600,

        650

    )

    assert result.variance == 50



def test_zero_variance():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        625

    )

    assert result.variance == 0



def test_production_flow():

    result = MilkProductionService().evaluate(

        "Lactating Cows",

        25,

        625,

        602

    )

    assert result.status == "ATTENTION"
'@ | Set-Content `
"tests\core\test_milk_production.py"



Write-Host "HERD-066 Milk Production Build Complete"