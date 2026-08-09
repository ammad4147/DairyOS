# =========================================
# DairyOS Build Script
# HERD-010
# Animal Health Foundation
# Version 1.0
# =========================================


Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-010 Build"
Write-Host " Animal Health Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

$folders = @(
    "dairyos\herd\health",
    "dairyos\herd\health\models",
    "dairyos\herd\health\services"
)


foreach ($folder in $folders) {

    New-Item -ItemType Directory -Force -Path $folder | Out-Null

}



# Init files

$files = @(
    "dairyos\herd\health\__init__.py",
    "dairyos\herd\health\models\__init__.py",
    "dairyos\herd\health\services\__init__.py"
)


foreach ($file in $files) {

    New-Item -ItemType File -Force -Path $file | Out-Null

}



# Health Record Model

@'
from dataclasses import dataclass
from datetime import date



@dataclass
class HealthRecord:


    animal_id: str

    event_date: date

    diagnosis: str

    treatment: str

    veterinarian: str

    status: str
'@ | Set-Content dairyos\herd\health\models\health_record.py



# Vaccination Model

@'
from dataclasses import dataclass
from datetime import date



@dataclass
class Vaccination:


    animal_id: str

    vaccine_name: str

    vaccination_date: date

    next_due_date: date
'@ | Set-Content dairyos\herd\health\models\vaccination.py



# Exports

@'
from .health_record import HealthRecord
from .vaccination import Vaccination
'@ | Set-Content dairyos\herd\health\models\__init__.py



# Health Service

@'
class HealthService:



    def __init__(self):

        self.records = []

        self.vaccinations = []



    def add_health_record(

        self,

        record

    ):

        self.records.append(record)

        return record



    def add_vaccination(

        self,

        vaccination

    ):

        self.vaccinations.append(vaccination)

        return vaccination



    def health_event_count(self):

        return len(self.records)



    def vaccination_count(self):

        return len(self.vaccinations)
'@ | Set-Content dairyos\herd\health\services\health_service.py



# Tests

@'
from datetime import date


from dairyos.herd.health.models import (

    HealthRecord,

    Vaccination

)


from dairyos.herd.health.services.health_service import (

    HealthService

)



def test_health_record_creation():


    record = HealthRecord(

        animal_id="HF-6001",

        event_date=date.today(),

        diagnosis="MASTITIS",

        treatment="ANTIBIOTIC",

        veterinarian="Farm Vet",

        status="RECOVERED"

    )


    assert record.diagnosis == "MASTITIS"



def test_vaccination_tracking():


    service = HealthService()


    vaccination = Vaccination(

        animal_id="HF-6001",

        vaccine_name="FMD",

        vaccination_date=date.today(),

        next_due_date=date.today()

    )


    service.add_vaccination(

        vaccination

    )


    assert service.vaccination_count() == 1



def test_health_service_record():


    service = HealthService()


    record = HealthRecord(

        animal_id="HF-6002",

        event_date=date.today(),

        diagnosis="FEVER",

        treatment="MEDICINE",

        veterinarian="Farm Vet",

        status="OPEN"

    )


    service.add_health_record(record)


    assert service.health_event_count() == 1
'@ | Set-Content tests\core\test_herd_health.py



Write-Host ""
Write-Host "Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-010 BUILD COMPLETE"
Write-Host "====================================="