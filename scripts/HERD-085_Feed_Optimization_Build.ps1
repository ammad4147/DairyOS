$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-085 Feed Optimization Intelligence Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\intelligence\feed\models",
"dairyos\intelligence\feed\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class FeedEfficiency:


    group_id: str

    feed_quantity: float

    milk_output: float

    efficiency: float

    status: str

    recommendation: str
'@ | Set-Content `
"dairyos\intelligence\feed\models\feed_efficiency.py"



@'
from ..models.feed_efficiency import FeedEfficiency



class FeedOptimizationService:



    def evaluate(

        self,

        group_id,

        feed_quantity,

        milk_output

    ):


        if feed_quantity <= 0:

            efficiency = 0

        else:

            efficiency = milk_output / feed_quantity



        if efficiency >= 1.2:

            status = "GOOD"

            recommendation = "Maintain current ration"



        elif efficiency >= 0.8:

            status = "ATTENTION"

            recommendation = "Review ration efficiency"



        else:

            status = "POOR"

            recommendation = "Optimize feeding strategy"



        return FeedEfficiency(

            group_id,

            feed_quantity,

            milk_output,

            efficiency,

            status,

            recommendation

        )
'@ | Set-Content `
"dairyos\intelligence\feed\services\feed_optimization_service.py"



@'
from dairyos.intelligence.feed.services.feed_optimization_service import FeedOptimizationService



def test_group():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.group_id == "LACTATING"



def test_feed_quantity():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.feed_quantity == 500



def test_milk_output():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.milk_output == 625



def test_efficiency():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.efficiency == 1.25



def test_good_status():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.status == "GOOD"



def test_good_recommendation():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.recommendation == "Maintain current ration"



def test_attention_status():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        450

    )

    assert result.status == "ATTENTION"



def test_attention_recommendation():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        450

    )

    assert result.recommendation == "Review ration efficiency"



def test_poor_status():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        300

    )

    assert result.status == "POOR"



def test_service_exists():

    assert FeedOptimizationService is not None
'@ | Set-Content `
"tests\core\test_feed_optimization.py"



Write-Host "HERD-085 Feed Optimization Intelligence Build Complete"