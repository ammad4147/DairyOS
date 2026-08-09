# =========================================
# DairyOS Build Script
# HERD-006
# Repository & Persistence Layer
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-006 Build"
Write-Host " Repository & Persistence Layer"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\herd\repositories",
    "dairyos\herd\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}


# Init files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\herd\repositories\__init__.py",
    "dairyos\herd\services\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}



# Repository

Write-Host "[3/7] Writing repository..."

@'
class AnimalRepository:



    def __init__(self):

        self.storage = {}



    def save(

        self,

        animal

    ):


        self.storage[

            animal.animal_id

        ] = animal


        return animal



    def get_by_id(

        self,

        animal_id

    ):


        return self.storage.get(

            animal_id

        )



    def get_all(self):


        return list(

            self.storage.values()

        )



    def delete(

        self,

        animal_id

    ):


        if animal_id in self.storage:

            del self.storage[animal_id]

            return True


        return False
'@ | Set-Content dairyos\herd\repositories\animal_repository.py



# Repository Export

@'
from .animal_repository import AnimalRepository
'@ | Set-Content dairyos\herd\repositories\__init__.py



# Service Layer

Write-Host "[4/7] Writing animal service..."

@'
class AnimalService:



    def __init__(

        self,

        repository

    ):

        self.repository = repository



    def register(

        self,

        animal

    ):


        return self.repository.save(

            animal

        )



    def find(

        self,

        animal_id

    ):


        return self.repository.get_by_id(

            animal_id

        )
'@ | Set-Content dairyos\herd\services\animal_service.py



# Tests

Write-Host "[5/7] Creating tests..."

@'
from datetime import date


from dairyos.herd.models import (

    Animal,

    AnimalStatus

)


from dairyos.herd.repositories import (

    AnimalRepository

)


from dairyos.herd.services.animal_service import (

    AnimalService

)



def test_repository_save():

    repository = AnimalRepository()


    animal = Animal(

        animal_id="HF-2001",

        ear_tag="2001",

        breed="Holstein Friesian",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.CALF,

        location="Calf Shed"

    )


    repository.save(animal)


    result = repository.get_by_id(

        "HF-2001"

    )


    assert result.animal_id == "HF-2001"



def test_service_registration():

    repository = AnimalRepository()


    service = AnimalService(

        repository

    )


    animal = Animal(

        animal_id="HF-2002",

        ear_tag="2002",

        breed="HF",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.HEIFER,

        location="Heifer Area"

    )


    service.register(animal)


    result = service.find(

        "HF-2002"

    )


    assert result.status == AnimalStatus.HEIFER



def test_repository_delete():

    repository = AnimalRepository()


    animal = Animal(

        animal_id="HF-2003",

        ear_tag="2003",

        breed="HF",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.CALF,

        location="Calf Shed"

    )


    repository.save(animal)


    assert repository.delete(

        "HF-2003"

    ) is True
'@ | Set-Content tests\core\test_herd_repository.py



# Verification

Write-Host "[6/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-006 BUILD COMPLETE"
Write-Host "====================================="