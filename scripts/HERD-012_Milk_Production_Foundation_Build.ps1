# =========================================
# DairyOS Build Script
# HERD-012
# Milk Production Foundation
# Version 1.0
# =========================================


Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-012 Build"
Write-Host " Milk Production Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

$folders = @(
    "dairyos\herd\production",
    "dairyos\herd\production\models",
    "dairyos\herd\production\services"
)


foreach ($folder in $folders) {

    New-Item -ItemType Directory -Force -Path $folder | Out-Null

}



# Init files

$files = @(
    "dairyos\herd\production\__init__.py",
    "dairyos\herd\production\models\__init__.py",
    "dairyos\herd\production\services\__init__.py"
)


foreach ($file in $files) {

    New-Item -ItemType File -Force -Path $file | Out-Null

}



# Milk Record Model

@'
from dataclasses import dataclass
from datetime import date



@dataclass
class MilkRecord:


    animal_id: str

    production_date: date

    morning_litres: float

    evening_litres: float



    @property
    def total_litres(self):

        return (

            self.morning_litres

            +

            self.evening_litres

        )
'@ | Set-Content dairyos\herd\production\models\milk_record.py



# Production Group Model

@'
from dataclasses import dataclass



@dataclass
class ProductionGroup:


    name: str

    description: str
'@ | Set-Content dairyos\herd\production\models\production_group.py



# Exports

@'
from .milk_record import MilkRecord
from .production_group import ProductionGroup
'@ | Set-Content dairyos\herd\production\models\__init__.py



# Production Service

@'
class ProductionService:



    def __init__(self):

        self.records = []

        self.groups = []



    def record_milk(

        self,

        record

    ):

        self.records.append(record)

        return record



    def add_group(

        self,

        group

    ):

        self.groups.append(group)

        return group



    def milk_record_count(self):

        return len(self.records)



    def group_count(self):

        return len(self.groups)
'@ | Set-Content dairyos\herd\production\services\production_service.py



# Tests

@'
from datetime import date


from dairyos.herd.production.models import (

    MilkRecord,

    ProductionGroup

)


from dairyos.herd.production.services.production_service import (

    ProductionService

)



def test_milk_record_total():


    record = MilkRecord(

        animal_id="HF-7001",

        production_date=date.today(),

        morning_litres=13,

        evening_litres=12

    )


    assert record.total_litres == 25



def test_production_tracking():


    service = ProductionService()


    record = MilkRecord(

        animal_id="HF-7002",

        production_date=date.today(),

        morning_litres=15,

        evening_litres=10

    )


    service.record_milk(record)


    assert service.milk_record_count() == 1



def test_production_group():


    service = ProductionService()


    group = ProductionGroup(

        name="PEAK_LACTATION",

        description="High producing cows"

    )


    service.add_group(group)


    assert service.group_count() == 1
'@ | Set-Content tests\core\test_herd_production.py



Write-Host ""
Write-Host "Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-012 BUILD COMPLETE"
Write-Host "====================================="