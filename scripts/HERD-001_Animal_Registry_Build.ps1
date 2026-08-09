# =========================================
# DairyOS Build Script
# HERD-001
# Animal Registry Foundation
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-001 Build"
Write-Host " Animal Registry Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\herd",
    "dairyos\herd\models",
    "dairyos\herd\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}



# Package files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\herd\__init__.py",
    "dairyos\herd\models\__init__.py",
    "dairyos\herd\services\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}



# Animal Status

Write-Host "[3/7] Writing animal models..."

@'
from enum import Enum


class AnimalStatus(Enum):

    CALF = "CALF"

    HEIFER = "HEIFER"

    PREGNANT_HEIFER = "PREGNANT_HEIFER"

    MILKING_COW = "MILKING_COW"

    DRY_COW = "DRY_COW"

    CULLED = "CULLED"

    SOLD = "SOLD"
'@ | Set-Content dairyos\herd\models\status.py



# Animal Model

@'
from dataclasses import dataclass
from datetime import date

from .status import AnimalStatus



@dataclass
class Animal:

    animal_id: str

    ear_tag: str

    breed: str

    gender: str

    birth_date: date

    status: AnimalStatus

    location: str
'@ | Set-Content dairyos\herd\models\animal.py



# Animal Event

@'
from dataclasses import dataclass
from datetime import datetime



@dataclass
class AnimalEvent:

    animal_id: str

    event_type: str

    event_date: datetime

    notes: str = ""
'@ | Set-Content dairyos\herd\models\animal_event.py



# Export Models

@'
from .animal import Animal
from .status import AnimalStatus
from .animal_event import AnimalEvent
'@ | Set-Content dairyos\herd\models\__init__.py



# Animal Registry Service

Write-Host "[4/7] Writing animal registry..."

@'
class AnimalRegistry:


    def __init__(self):

        self.animals = {}



    def register(
        self,
        animal
    ):

        self.animals[
            animal.animal_id
        ] = animal


        return animal



    def get(
        self,
        animal_id
    ):

        return self.animals.get(
            animal_id
        )



    def count(self):

        return len(
            self.animals
        )
'@ | Set-Content dairyos\herd\services\animal_registry.py



# Lifecycle Service

@'
from ..models.status import AnimalStatus



class LifecycleService:


    def change_status(
        self,
        animal,
        new_status
    ):

        animal.status = new_status

        return animal
'@ | Set-Content dairyos\herd\services\lifecycle.py



# Tests

Write-Host "[5/7] Creating tests..."

@'
from datetime import date

from dairyos.herd.models import (
    Animal,
    AnimalStatus
)

from dairyos.herd.services.animal_registry import (
    AnimalRegistry
)

from dairyos.herd.services.lifecycle import (
    LifecycleService
)



def test_animal_registration():

    registry = AnimalRegistry()

    animal = Animal(
        animal_id="HF-0001",
        ear_tag="001",
        breed="Holstein Friesian",
        gender="FEMALE",
        birth_date=date.today(),
        status=AnimalStatus.MILKING_COW,
        location="Main Shed"
    )


    registry.register(animal)


    assert registry.count() == 1



def test_lifecycle_change():

    animal = Animal(
        animal_id="HF-0002",
        ear_tag="002",
        breed="HF",
        gender="FEMALE",
        birth_date=date.today(),
        status=AnimalStatus.HEIFER,
        location="Heifer Area"
    )


    service = LifecycleService()


    service.change_status(
        animal,
        AnimalStatus.MILKING_COW
    )


    assert animal.status == AnimalStatus.MILKING_COW
'@ | Set-Content tests\core\test_herd_registry.py



# Verification

Write-Host "[6/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-001 BUILD COMPLETE"
Write-Host "====================================="