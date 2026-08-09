# =========================================
# DairyOS Build Script
# HERD-007
# Database Integration Foundation
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-007 Build"
Write-Host " Database Integration Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\herd\database",
    "dairyos\herd\database\models",
    "dairyos\herd\database\repositories"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}


# Init files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\herd\database\__init__.py",
    "dairyos\herd\database\models\__init__.py",
    "dairyos\herd\database\repositories\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}



# Database Record Model

Write-Host "[3/7] Writing database model..."

@'
from dataclasses import dataclass
from datetime import date



@dataclass
class AnimalRecord:


    animal_id: str

    ear_tag: str

    breed: str

    gender: str

    birth_date: date

    status: str

    location: str
'@ | Set-Content dairyos\herd\database\models\animal_record.py



@'
from .animal_record import AnimalRecord
'@ | Set-Content dairyos\herd\database\models\__init__.py



# Database Repository

Write-Host "[4/7] Writing database repository..."

@'
from ..models.animal_record import AnimalRecord



class DatabaseAnimalRepository:



    def __init__(self):

        self.records = {}



    def save(

        self,

        record

    ):


        self.records[

            record.animal_id

        ] = record


        return record



    def find(

        self,

        animal_id

    ):


        return self.records.get(

            animal_id

        )



    def count(self):


        return len(

            self.records

        )
'@ | Set-Content dairyos\herd\database\repositories\database_animal_repository.py



@'
from .database_animal_repository import DatabaseAnimalRepository
'@ | Set-Content dairyos\herd\database\repositories\__init__.py



# Tests

Write-Host "[5/7] Creating tests..."

@'
from datetime import date


from dairyos.herd.database.models import (

    AnimalRecord

)


from dairyos.herd.database.repositories import (

    DatabaseAnimalRepository

)



def test_database_record_save():


    repository = DatabaseAnimalRepository()


    record = AnimalRecord(

        animal_id="HF-3001",

        ear_tag="3001",

        breed="Holstein Friesian",

        gender="FEMALE",

        birth_date=date.today(),

        status="MILKING_COW",

        location="Main Shed"

    )


    repository.save(record)


    result = repository.find(

        "HF-3001"

    )


    assert result.animal_id == "HF-3001"



def test_database_count():


    repository = DatabaseAnimalRepository()


    repository.save(

        AnimalRecord(

            animal_id="HF-3002",

            ear_tag="3002",

            breed="HF",

            gender="FEMALE",

            birth_date=date.today(),

            status="CALF",

            location="Calf Shed"

        )

    )


    assert repository.count() == 1
'@ | Set-Content tests\core\test_herd_database.py



# Verification

Write-Host "[6/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-007 BUILD COMPLETE"
Write-Host "====================================="