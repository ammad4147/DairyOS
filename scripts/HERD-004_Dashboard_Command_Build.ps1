# =========================================
# DairyOS Build Script
# HERD-004
# Herd Dashboard & Command View Foundation
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-004 Build"
Write-Host " Herd Dashboard & Command View"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\herd\dashboard",
    "dairyos\herd\dashboard\models",
    "dairyos\herd\dashboard\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}


# Init files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\herd\dashboard\__init__.py",
    "dairyos\herd\dashboard\models\__init__.py",
    "dairyos\herd\dashboard\services\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}



# Dashboard Model

Write-Host "[3/7] Writing dashboard models..."

@'
from dataclasses import dataclass



@dataclass
class HerdDashboard:


    farm_name: str

    total_animals: int

    milking_cows: int

    dry_cows: int

    heifers: int

    calves: int

    capacity: int
'@ | Set-Content dairyos\herd\dashboard\models\dashboard.py



@'
from .dashboard import HerdDashboard
'@ | Set-Content dairyos\herd\dashboard\models\__init__.py



# Dashboard Service

Write-Host "[4/7] Writing dashboard service..."

@'
from ..models.dashboard import HerdDashboard



class HerdDashboardService:



    def generate(

        self,

        farm_name,

        snapshot,

        capacity

    ):


        return HerdDashboard(

            farm_name=farm_name,

            total_animals=snapshot.total_animals,

            milking_cows=snapshot.milking_cows,

            dry_cows=snapshot.dry_cows,

            heifers=snapshot.heifers,

            calves=snapshot.calves,

            capacity=capacity

        )
'@ | Set-Content dairyos\herd\dashboard\services\dashboard_service.py



# KPI Service

@'
class HerdKPIService:



    def utilization(

        self,

        total_animals,

        capacity

    ):


        if capacity == 0:

            return 0


        return round(

            (total_animals / capacity) * 100,

            2

        )



    def milking_ratio(

        self,

        milking,

        total

    ):


        if total == 0:

            return 0


        return round(

            (milking / total) * 100,

            2

        )
'@ | Set-Content dairyos\herd\dashboard\services\kpi_service.py



# Tests

Write-Host "[5/7] Creating tests..."

@'
from dairyos.herd.dashboard.models import HerdDashboard

from dairyos.herd.dashboard.services.kpi_service import HerdKPIService



def test_dashboard_creation():


    dashboard = HerdDashboard(

        farm_name="Trident Dairies",

        total_animals=50,

        milking_cows=25,

        dry_cows=5,

        heifers=15,

        calves=5,

        capacity=50

    )


    assert dashboard.total_animals == 50



def test_capacity_utilization():


    service = HerdKPIService()


    result = service.utilization(

        50,

        50

    )


    assert result == 100



def test_milking_ratio():


    service = HerdKPIService()


    result = service.milking_ratio(

        25,

        50

    )


    assert result == 50
'@ | Set-Content tests\core\test_herd_dashboard.py



# Verification

Write-Host "[6/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-004 BUILD COMPLETE"
Write-Host "====================================="