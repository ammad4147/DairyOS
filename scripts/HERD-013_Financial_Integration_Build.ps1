# =========================================
# DairyOS Build Script
# HERD-013
# Herd Financial Integration Foundation
# Version 1.0
# =========================================


Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-013 Build"
Write-Host " Financial Integration Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

$folders = @(
    "dairyos\herd\finance",
    "dairyos\herd\finance\models",
    "dairyos\herd\finance\services"
)


foreach ($folder in $folders) {

    New-Item -ItemType Directory -Force -Path $folder | Out-Null

}



# Init files

$files = @(
    "dairyos\herd\finance\__init__.py",
    "dairyos\herd\finance\models\__init__.py",
    "dairyos\herd\finance\services\__init__.py"
)


foreach ($file in $files) {

    New-Item -ItemType File -Force -Path $file | Out-Null

}



# Animal Cost Model

@'
from dataclasses import dataclass
from datetime import date



@dataclass
class AnimalCost:


    animal_id: str

    cost_date: date

    feed_cost: float

    health_cost: float

    breeding_cost: float



    @property
    def total_cost(self):

        return (

            self.feed_cost

            +

            self.health_cost

            +

            self.breeding_cost

        )
'@ | Set-Content dairyos\herd\finance\models\animal_cost.py



# Milk Revenue Model

@'
from dataclasses import dataclass
from datetime import date



@dataclass
class MilkRevenue:


    animal_id: str

    revenue_date: date

    litres: float

    price_per_litre: float



    @property
    def total_revenue(self):

        return (

            self.litres

            *

            self.price_per_litre

        )
'@ | Set-Content dairyos\herd\finance\models\milk_revenue.py



# Exports

@'
from .animal_cost import AnimalCost
from .milk_revenue import MilkRevenue
'@ | Set-Content dairyos\herd\finance\models\__init__.py



# Finance Service

@'
class FinanceService:



    def __init__(self):

        self.costs = []

        self.revenues = []



    def record_cost(

        self,

        cost

    ):

        self.costs.append(cost)

        return cost



    def record_revenue(

        self,

        revenue

    ):

        self.revenues.append(revenue)

        return revenue



    def cost_count(self):

        return len(self.costs)



    def revenue_count(self):

        return len(self.revenues)
'@ | Set-Content dairyos\herd\finance\services\finance_service.py



# Tests

@'
from datetime import date


from dairyos.herd.finance.models import (

    AnimalCost,

    MilkRevenue

)


from dairyos.herd.finance.services.finance_service import (

    FinanceService

)



def test_animal_cost_calculation():


    cost = AnimalCost(

        animal_id="HF-8001",

        cost_date=date.today(),

        feed_cost=2500,

        health_cost=100,

        breeding_cost=50

    )


    assert cost.total_cost == 2650



def test_milk_revenue_calculation():


    revenue = MilkRevenue(

        animal_id="HF-8001",

        revenue_date=date.today(),

        litres=25,

        price_per_litre=225

    )


    assert revenue.total_revenue == 5625



def test_finance_service():


    service = FinanceService()


    service.record_cost(

        AnimalCost(

            animal_id="HF-8002",

            cost_date=date.today(),

            feed_cost=2000,

            health_cost=100,

            breeding_cost=0

        )

    )


    assert service.cost_count() == 1
'@ | Set-Content tests\core\test_herd_finance.py



Write-Host ""
Write-Host "Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-013 BUILD COMPLETE"
Write-Host "====================================="