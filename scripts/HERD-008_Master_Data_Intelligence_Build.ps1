# =========================================
# DairyOS Build Script
# HERD-008
# Master Data & Breed Intelligence
# Version 1.0
# =========================================


Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-008 Build"
Write-Host " Master Data & Breed Intelligence"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\herd\masterdata",
    "dairyos\herd\masterdata\models",
    "dairyos\herd\masterdata\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}



# Init files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\herd\masterdata\__init__.py",
    "dairyos\herd\masterdata\models\__init__.py",
    "dairyos\herd\masterdata\services\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}



# Breed Model

Write-Host "[3/7] Writing master data models..."

@'
from dataclasses import dataclass


@dataclass
class Breed:


    name: str

    category: str

    expected_milk_per_day: float

    maturity_months: int

    active: bool = True
'@ | Set-Content dairyos\herd\masterdata\models\breed.py



# Animal Class

@'
from dataclasses import dataclass


@dataclass
class AnimalClass:


    name: str

    description: str
'@ | Set-Content dairyos\herd\masterdata\models\animal_class.py



# Production Group

@'
from dataclasses import dataclass


@dataclass
class ProductionGroup:


    name: str

    description: str
'@ | Set-Content dairyos\herd\masterdata\models\production_group.py



# Exports

@'
from .breed import Breed
from .animal_class import AnimalClass
from .production_group import ProductionGroup
'@ | Set-Content dairyos\herd\masterdata\models\__init__.py



# Service

Write-Host "[4/7] Writing master data service..."

@'
class MasterDataService:


    def __init__(self):

        self.breeds = []

        self.classes = []

        self.production_groups = []



    def add_breed(

        self,

        breed

    ):

        self.breeds.append(breed)

        return breed



    def get_breeds(self):

        return self.breeds
'@ | Set-Content dairyos\herd\masterdata\services\master_data_service.py



# Tests

Write-Host "[5/7] Creating tests..."

@'
from dairyos.herd.masterdata.models import Breed

from dairyos.herd.masterdata.services.master_data_service import (
    MasterDataService
)



def test_breed_creation():


    breed = Breed(

        name="Holstein Friesian",

        category="DAIRY",

        expected_milk_per_day=25,

        maturity_months=24

    )


    assert breed.name == "Holstein Friesian"

    assert breed.expected_milk_per_day == 25



def test_master_data_service():


    service = MasterDataService()


    breed = Breed(

        name="Jersey",

        category="DAIRY",

        expected_milk_per_day=18,

        maturity_months=22

    )


    service.add_breed(breed)


    assert len(service.get_breeds()) == 1
'@ | Set-Content tests\core\test_herd_masterdata.py



# Verification

Write-Host "[6/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-008 BUILD COMPLETE"
Write-Host "====================================="