$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-063 Feed Management Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\feed\models",
"dairyos\herd\feed\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class FeedManagement:


    animal_group: str

    animal_count: int

    daily_feed_kg: float

    daily_feed_cost: float

    cost_per_animal: float

    status: str
'@ | Set-Content `
"dairyos\herd\feed\models\feed_management.py"



@'
from ..models.feed_management import FeedManagement



class FeedManagementService:



    def evaluate(

        self,

        animal_group,

        animal_count,

        feed_per_animal,

        cost_per_animal

    ):


        total_feed = (

            animal_count *

            feed_per_animal

        )


        total_cost = (

            animal_count *

            cost_per_animal

        )


        if cost_per_animal > 2500:

            status = "MONITOR"

        else:

            status = "NORMAL"



        return FeedManagement(

            animal_group,

            animal_count,

            total_feed,

            total_cost,

            cost_per_animal,

            status

        )
'@ | Set-Content `
"dairyos\herd\feed\services\feed_management_service.py"



@'
from dairyos.herd.feed.services.feed_management_service import FeedManagementService



def test_feed_group():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.animal_group == "Lactating Cows"



def test_animal_count():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.animal_count == 25



def test_daily_feed_calculation():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.daily_feed_kg == 875



def test_daily_cost_calculation():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.daily_feed_cost == 62500



def test_cost_per_animal():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.cost_per_animal == 2500



def test_normal_status():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.status == "NORMAL"



def test_monitor_status():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        3000

    )

    assert result.status == "MONITOR"



def test_small_group():

    result = FeedManagementService().evaluate(

        "Heifers",

        10,

        20,

        1500

    )

    assert result.daily_feed_kg == 200



def test_feed_model():

    result = FeedManagementService().evaluate(

        "Dry Cows",

        5,

        25,

        1800

    )

    assert result.animal_group == "Dry Cows"



def test_feed_management_flow():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.daily_feed_cost == 62500
'@ | Set-Content `
"tests\core\test_feed_management.py"



Write-Host "HERD-063 Feed Management Build Complete"