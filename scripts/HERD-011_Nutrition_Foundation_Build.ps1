# =========================================
# DairyOS Build Script
# HERD-011
# Feed & Nutrition Foundation
# Version 1.0
# =========================================


Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-011 Build"
Write-Host " Feed & Nutrition Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

$folders = @(
    "dairyos\herd\nutrition",
    "dairyos\herd\nutrition\models",
    "dairyos\herd\nutrition\services"
)


foreach ($folder in $folders) {

    New-Item -ItemType Directory -Force -Path $folder | Out-Null

}



# Init files

$files = @(
    "dairyos\herd\nutrition\__init__.py",
    "dairyos\herd\nutrition\models\__init__.py",
    "dairyos\herd\nutrition\services\__init__.py"
)


foreach ($file in $files) {

    New-Item -ItemType File -Force -Path $file | Out-Null

}



# Feed Plan Model

@'
from dataclasses import dataclass



@dataclass
class FeedPlan:


    group_name: str

    silage_kg: float

    concentrate_kg: float

    mineral_grams: float
'@ | Set-Content dairyos\herd\nutrition\models\feed_plan.py



# Feed Consumption Model

@'
from dataclasses import dataclass
from datetime import date



@dataclass
class FeedConsumption:


    group_name: str

    consumption_date: date

    total_feed_kg: float

    animals_count: int
'@ | Set-Content dairyos\herd\nutrition\models\feed_consumption.py



# Exports

@'
from .feed_plan import FeedPlan
from .feed_consumption import FeedConsumption
'@ | Set-Content dairyos\herd\nutrition\models\__init__.py



# Nutrition Service

@'
class NutritionService:



    def __init__(self):

        self.feed_plans = []

        self.consumptions = []



    def add_feed_plan(

        self,

        plan

    ):

        self.feed_plans.append(plan)

        return plan



    def record_consumption(

        self,

        consumption

    ):

        self.consumptions.append(consumption)

        return consumption



    def feed_plan_count(self):

        return len(self.feed_plans)



    def consumption_count(self):

        return len(self.consumptions)
'@ | Set-Content dairyos\herd\nutrition\services\nutrition_service.py



# Tests

@'
from datetime import date


from dairyos.herd.nutrition.models import (

    FeedPlan,

    FeedConsumption

)


from dairyos.herd.nutrition.services.nutrition_service import (

    NutritionService

)



def test_feed_plan_creation():


    plan = FeedPlan(

        group_name="HIGH_LACTATION",

        silage_kg=25,

        concentrate_kg=8,

        mineral_grams=100

    )


    assert plan.concentrate_kg == 8



def test_feed_consumption_tracking():


    service = NutritionService()


    consumption = FeedConsumption(

        group_name="MILKING_COWS",

        consumption_date=date.today(),

        total_feed_kg=750,

        animals_count=25

    )


    service.record_consumption(

        consumption

    )


    assert service.consumption_count() == 1



def test_nutrition_service():


    service = NutritionService()


    plan = FeedPlan(

        group_name="DRY_COWS",

        silage_kg=15,

        concentrate_kg=3,

        mineral_grams=80

    )


    service.add_feed_plan(plan)


    assert service.feed_plan_count() == 1
'@ | Set-Content tests\core\test_herd_nutrition.py



Write-Host ""
Write-Host "Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-011 BUILD COMPLETE"
Write-Host "====================================="