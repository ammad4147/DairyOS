# =========================================
# DairyOS Build Script
# HERD-009
# Reproduction Foundation
# Version 1.0
# =========================================


Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-009 Build"
Write-Host " Reproduction Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

$folders = @(
    "dairyos\herd\reproduction",
    "dairyos\herd\reproduction\models",
    "dairyos\herd\reproduction\services"
)


foreach ($folder in $folders) {

    New-Item -ItemType Directory -Force -Path $folder | Out-Null

}



# Init files

$files = @(
    "dairyos\herd\reproduction\__init__.py",
    "dairyos\herd\reproduction\models\__init__.py",
    "dairyos\herd\reproduction\services\__init__.py"
)


foreach ($file in $files) {

    New-Item -ItemType File -Force -Path $file | Out-Null

}



# Breeding Record Model

@'
from dataclasses import dataclass
from datetime import date



@dataclass
class BreedingRecord:


    animal_id: str

    service_date: date

    breeding_method: str

    semen_type: str

    technician: str
'@ | Set-Content dairyos\herd\reproduction\models\breeding_record.py




# Pregnancy Model

@'
from dataclasses import dataclass
from datetime import date



@dataclass
class Pregnancy:


    animal_id: str

    confirmed_date: date

    expected_calving_date: date

    status: str
'@ | Set-Content dairyos\herd\reproduction\models\pregnancy.py




# Exports

@'
from .breeding_record import BreedingRecord
from .pregnancy import Pregnancy
'@ | Set-Content dairyos\herd\reproduction\models\__init__.py




# Service

@'
class ReproductionService:



    def __init__(self):

        self.records = []

        self.pregnancies = []



    def add_breeding(

        self,

        record

    ):

        self.records.append(record)

        return record



    def confirm_pregnancy(

        self,

        pregnancy

    ):

        self.pregnancies.append(pregnancy)

        return pregnancy



    def pregnancy_count(self):

        return len(self.pregnancies)
'@ | Set-Content dairyos\herd\reproduction\services\reproduction_service.py




# Tests

@'
from datetime import date


from dairyos.herd.reproduction.models import (

    BreedingRecord,

    Pregnancy

)


from dairyos.herd.reproduction.services import (

    reproduction_service

)



def test_breeding_record():


    record = BreedingRecord(

        animal_id="HF-5001",

        service_date=date.today(),

        breeding_method="AI",

        semen_type="SEXED_HF",

        technician="AI Technician"

    )


    assert record.breeding_method == "AI"



def test_pregnancy_tracking():


    service = reproduction_service.ReproductionService()


    pregnancy = Pregnancy(

        animal_id="HF-5001",

        confirmed_date=date.today(),

        expected_calving_date=date.today(),

        status="CONFIRMED"

    )


    service.confirm_pregnancy(

        pregnancy

    )


    assert service.pregnancy_count() == 1
'@ | Set-Content tests\core\test_herd_reproduction.py




Write-Host ""
Write-Host "Running verification..."
pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-009 BUILD COMPLETE"
Write-Host "====================================="