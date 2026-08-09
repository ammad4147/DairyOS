# =========================================
# DairyOS Build Script
# HERD-003
# Herd Intelligence Foundation
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-003 Build"
Write-Host " Herd Intelligence Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\herd\intelligence",
    "dairyos\herd\intelligence\models",
    "dairyos\herd\intelligence\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}


# Init files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\herd\intelligence\__init__.py",
    "dairyos\herd\intelligence\models\__init__.py",
    "dairyos\herd\intelligence\services\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}



# Herd Snapshot Model

Write-Host "[3/7] Writing intelligence models..."

@'
from dataclasses import dataclass


@dataclass
class HerdSnapshot:

    total_animals: int

    milking_cows: int

    dry_cows: int

    heifers: int

    calves: int
'@ | Set-Content dairyos\herd\intelligence\models\herd_snapshot.py



@'
from .herd_snapshot import HerdSnapshot
'@ | Set-Content dairyos\herd\intelligence\models\__init__.py



# Herd Metrics Service

Write-Host "[4/7] Writing herd metrics engine..."

@'
from ..models.herd_snapshot import HerdSnapshot

from dairyos.herd.models import AnimalStatus



class HerdMetricsService:


    def calculate(
        self,
        animals
    ):

        milking = 0

        dry = 0

        heifers = 0

        calves = 0


        for animal in animals:


            if animal.status == AnimalStatus.MILKING_COW:

                milking += 1


            elif animal.status == AnimalStatus.DRY_COW:

                dry += 1


            elif animal.status in [

                AnimalStatus.HEIFER,

                AnimalStatus.PREGNANT_HEIFER

            ]:

                heifers += 1


            elif animal.status == AnimalStatus.CALF:

                calves += 1



        return HerdSnapshot(

            total_animals=len(animals),

            milking_cows=milking,

            dry_cows=dry,

            heifers=heifers,

            calves=calves

        )
'@ | Set-Content dairyos\herd\intelligence\services\herd_metrics.py



# Herd Summary Service

@'
class HerdSummaryService:


    def percentage(
        self,
        part,
        total
    ):

        if total == 0:

            return 0


        return round(

            (part / total) * 100,

            2

        )
'@ | Set-Content dairyos\herd\intelligence\services\herd_summary.py



# Tests

Write-Host "[5/7] Creating tests..."

@'
from datetime import date


from dairyos.herd.models import (

    Animal,

    AnimalStatus

)


from dairyos.herd.intelligence.services.herd_metrics import (

    HerdMetricsService

)



def test_herd_snapshot():


    animals = [

        Animal(

            animal_id="001",

            ear_tag="001",

            breed="HF",

            gender="FEMALE",

            birth_date=date.today(),

            status=AnimalStatus.MILKING_COW,

            location="Shed"

        ),


        Animal(

            animal_id="002",

            ear_tag="002",

            breed="HF",

            gender="FEMALE",

            birth_date=date.today(),

            status=AnimalStatus.HEIFER,

            location="Heifer Area"

        )

    ]



    service = HerdMetricsService()


    snapshot = service.calculate(

        animals

    )


    assert snapshot.total_animals == 2

    assert snapshot.milking_cows == 1

    assert snapshot.heifers == 1
'@ | Set-Content tests\core\test_herd_intelligence.py



# Verification

Write-Host "[6/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-003 BUILD COMPLETE"
Write-Host "====================================="