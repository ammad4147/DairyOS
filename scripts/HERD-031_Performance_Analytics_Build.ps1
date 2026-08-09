$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-031 Performance Analytics Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass


@dataclass
class PerformanceMetric:

    total_actions: int

    completed_actions: int

    open_actions: int

    completion_rate: float

    effectiveness_score: int
'@ | Set-Content `
"dairyos\herd\dashboard\models\performance_metric.py"



@'
from ..models.performance_metric import PerformanceMetric



class PerformanceAnalyticsService:



    def calculate(

        self,

        total_actions,

        completed_actions

    ):


        open_actions = total_actions - completed_actions


        if total_actions == 0:

            completion_rate = 0

        else:

            completion_rate = round(

                (completed_actions / total_actions) * 100,

                2

            )


        effectiveness = round(

            completion_rate

        )


        return PerformanceMetric(

            total_actions,

            completed_actions,

            open_actions,

            completion_rate,

            effectiveness

        )



    def category_count(

        self,

        records

    ):


        result = {}


        for item in records:

            if item.category not in result:

                result[item.category] = 0


            result[item.category] += 1


        return result



    def most_frequent_category(

        self,

        records

    ):


        counts = self.category_count(records)


        if not counts:

            return None


        return max(

            counts,

            key=counts.get

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\performance_analytics_service.py"



@'
from dairyos.herd.dashboard.services.performance_analytics_service import PerformanceAnalyticsService
from dairyos.herd.dashboard.models.operational_memory import OperationalMemory



def test_performance_calculation():

    result = PerformanceAnalyticsService().calculate(

        10,

        8

    )

    assert result.completion_rate == 80



def test_open_actions():

    result = PerformanceAnalyticsService().calculate(

        10,

        6

    )

    assert result.open_actions == 4



def test_effectiveness_score():

    result = PerformanceAnalyticsService().calculate(

        20,

        20

    )

    assert result.effectiveness_score == 100



def test_zero_actions():

    result = PerformanceAnalyticsService().calculate(

        0,

        0

    )

    assert result.completion_rate == 0



def test_category_count():

    records = [

        OperationalMemory(

            "HEALTH",

            "Issue",

            "Action",

            "COMPLETED",

            "Done",

            "HIGH"

        ),

        OperationalMemory(

            "HEALTH",

            "Issue",

            "Action",

            "COMPLETED",

            "Done",

            "HIGH"

        )

    ]


    result = PerformanceAnalyticsService().category_count(records)


    assert result["HEALTH"] == 2



def test_multiple_categories():

    records = [

        OperationalMemory(

            "HEALTH",

            "Issue",

            "Action",

            "COMPLETED",

            "Done",

            "HIGH"

        ),

        OperationalMemory(

            "FINANCE",

            "Issue",

            "Action",

            "COMPLETED",

            "Done",

            "MEDIUM"

        )

    ]


    result = PerformanceAnalyticsService().category_count(records)


    assert len(result) == 2



def test_most_frequent_category():

    records = [

        OperationalMemory(

            "REPRODUCTION",

            "Issue",

            "Action",

            "COMPLETED",

            "Done",

            "HIGH"

        ),

        OperationalMemory(

            "REPRODUCTION",

            "Issue",

            "Action",

            "COMPLETED",

            "Done",

            "HIGH"

        )

    ]


    result = PerformanceAnalyticsService().most_frequent_category(records)


    assert result == "REPRODUCTION"



def test_metric_model():

    result = PerformanceAnalyticsService().calculate(

        5,

        5

    )

    assert result.total_actions == 5



def test_partial_completion():

    result = PerformanceAnalyticsService().calculate(

        4,

        1

    )

    assert result.open_actions == 3



def test_completion_precision():

    result = PerformanceAnalyticsService().calculate(

        3,

        1

    )

    assert result.completion_rate == 33.33
'@ | Set-Content `
"tests\core\test_performance_analytics.py"



Write-Host "HERD-031 Performance Analytics Build Complete"