# =========================================
# DairyOS Build Script
# CORE-007
# Master Data Foundation
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS CORE-007 Build"
Write-Host " Master Data Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\core\masterdata",
    "dairyos\core\masterdata\models",
    "dairyos\core\masterdata\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}


# Package files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\core\masterdata\__init__.py",
    "dairyos\core\masterdata\models\__init__.py",
    "dairyos\core\masterdata\services\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}



# Farm Model

Write-Host "[3/7] Writing master entities..."

@'
from dataclasses import dataclass


@dataclass
class Farm:

    name: str

    location: str

    capacity: int

    status: str = "ACTIVE"
'@ | Set-Content dairyos\core\masterdata\models\farm.py



# Location Model

@'
from dataclasses import dataclass


@dataclass
class Location:

    name: str

    category: str

    active: bool = True
'@ | Set-Content dairyos\core\masterdata\models\location.py



# Breed Model

@'
from dataclasses import dataclass


@dataclass
class Breed:

    name: str

    origin: str
'@ | Set-Content dairyos\core\masterdata\models\breed.py



# Animal Type Model

@'
from dataclasses import dataclass


@dataclass
class AnimalType:

    name: str

    description: str
'@ | Set-Content dairyos\core\masterdata\models\animal_type.py



# Export Models

@'
from .farm import Farm
from .location import Location
from .breed import Breed
from .animal_type import AnimalType
'@ | Set-Content dairyos\core\masterdata\models\__init__.py



# Master Data Service

Write-Host "[4/7] Writing master data service..."

@'
class MasterDataService:


    def __init__(self):

        self.farms = []

        self.locations = []

        self.breeds = []

        self.animal_types = []



    def add_farm(self, farm):

        self.farms.append(farm)

        return farm



    def add_location(self, location):

        self.locations.append(location)

        return location



    def add_breed(self, breed):

        self.breeds.append(breed)

        return breed



    def add_animal_type(self, animal_type):

        self.animal_types.append(animal_type)

        return animal_type
'@ | Set-Content dairyos\core\masterdata\services\master_data_service.py



# Tests

Write-Host "[5/7] Creating tests..."

@'
from dairyos.core.masterdata.models import (
    Farm,
    Location,
    Breed,
    AnimalType
)

from dairyos.core.masterdata.services.master_data_service import (
    MasterDataService
)



def test_master_data_creation():

    farm = Farm(
        name="Trident Dairies",
        location="Lahore",
        capacity=50
    )

    assert farm.status == "ACTIVE"



def test_master_data_service():

    service = MasterDataService()

    breed = Breed(
        name="Holstein Friesian",
        origin="Netherlands"
    )

    result = service.add_breed(
        breed
    )

    assert result.name == "Holstein Friesian"



def test_animal_category():

    animal = AnimalType(
        name="Milking Cow",
        description="Adult lactating animal"
    )

    assert animal.name == "Milking Cow"
'@ | Set-Content tests\core\test_masterdata.py



# Verification

Write-Host "[6/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " CORE-007 BUILD COMPLETE"
Write-Host "====================================="