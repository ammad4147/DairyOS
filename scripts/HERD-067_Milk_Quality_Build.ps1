$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-067 Milk Quality Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\production\quality\models",
"dairyos\herd\production\quality\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class MilkQuality:


    batch_id: str

    volume_litres: float

    fat_percentage: float

    protein_percentage: float

    quality_status: str

    quality_grade: str
'@ | Set-Content `
"dairyos\herd\production\quality\models\milk_quality.py"



@'
from ..models.milk_quality import MilkQuality



class MilkQualityService:



    def evaluate(

        self,

        batch_id,

        volume_litres,

        fat_percentage,

        protein_percentage

    ):


        if fat_percentage >= 3.5 and protein_percentage >= 3.0:

            quality_status = "GOOD"

            quality_grade = "PREMIUM"


        elif fat_percentage >= 3.2:

            quality_status = "ACCEPTABLE"

            quality_grade = "STANDARD"


        else:

            quality_status = "ATTENTION"

            quality_grade = "LOW"



        return MilkQuality(

            batch_id,

            volume_litres,

            fat_percentage,

            protein_percentage,

            quality_status,

            quality_grade

        )
'@ | Set-Content `
"dairyos\herd\production\quality\services\milk_quality_service.py"



@'
from dairyos.herd.production.quality.services.milk_quality_service import MilkQualityService



def test_batch_id():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.batch_id == "MORNING-001"



def test_volume():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.volume_litres == 310



def test_fat_percentage():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.fat_percentage == 3.8



def test_protein_percentage():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.protein_percentage == 3.2



def test_good_status():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.quality_status == "GOOD"



def test_premium_grade():

    result = MilkQualityService().evaluate(

        "MORNING-001",

        310,

        3.8,

        3.2

    )

    assert result.quality_grade == "PREMIUM"



def test_standard_quality():

    result = MilkQualityService().evaluate(

        "MORNING-002",

        300,

        3.3,

        2.9

    )

    assert result.quality_grade == "STANDARD"



def test_low_quality():

    result = MilkQualityService().evaluate(

        "MORNING-003",

        300,

        3.0,

        2.8

    )

    assert result.quality_status == "ATTENTION"



def test_quality_model():

    result = MilkQualityService().evaluate(

        "MORNING-004",

        250,

        3.6,

        3.1

    )

    assert result.quality_grade == "PREMIUM"



def test_quality_flow():

    result = MilkQualityService().evaluate(

        "MORNING-005",

        310,

        3.8,

        3.2

    )

    assert result.quality_status == "GOOD"
'@ | Set-Content `
"tests\core\test_milk_quality.py"



Write-Host "HERD-067 Milk Quality Build Complete"