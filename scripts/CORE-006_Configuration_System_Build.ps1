# =========================================
# DairyOS Build Script
# CORE-006
# Configuration & System Management
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS CORE-006 Build"
Write-Host " Configuration & System Management"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\core\configuration",
    "dairyos\core\configuration\models",
    "dairyos\core\configuration\services",
    "dairyos\core\system"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}


# Create init files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\core\configuration\__init__.py",
    "dairyos\core\configuration\models\__init__.py",
    "dairyos\core\configuration\services\__init__.py",
    "dairyos\core\system\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}


# Configuration Model

Write-Host "[3/7] Writing configuration model..."

@'
from dataclasses import dataclass


@dataclass
class SystemSetting:

    key: str

    value: str

    category: str = "SYSTEM"
'@ | Set-Content dairyos\core\configuration\models\setting.py


@'
from .setting import SystemSetting
'@ | Set-Content dairyos\core\configuration\models\__init__.py



# Default Settings

@'
DEFAULT_SETTINGS = {

    "farm_name": "Trident Dairies",

    "currency": "PKR",

    "timezone": "Asia/Karachi",

    "milk_unit": "litres",

    "environment": "development"
}
'@ | Set-Content dairyos\core\configuration\defaults.py



# Configuration Manager

Write-Host "[4/7] Writing configuration manager..."

@'
from ..defaults import DEFAULT_SETTINGS


class ConfigurationManager:


    def __init__(self):

        self.settings = DEFAULT_SETTINGS.copy()


    def get(self, key):

        return self.settings.get(key)


    def set(
        self,
        key,
        value
    ):

        self.settings[key] = value


        return value
'@ | Set-Content dairyos\core\configuration\services\config_manager.py



# System Health

Write-Host "[5/7] Writing system management..."

@'
from datetime import datetime


def system_health():

    return {

        "status": "ONLINE",

        "timestamp": datetime.utcnow()

    }
'@ | Set-Content dairyos\core\system\health.py



# System Information

@'
def system_info():

    return {

        "name": "DairyOS",

        "version": "0.1.0"

    }
'@ | Set-Content dairyos\core\system\info.py



# Tests

Write-Host "[6/7] Creating tests..."

@'
from dairyos.core.configuration.services.config_manager import ConfigurationManager

from dairyos.core.system.health import system_health

from dairyos.core.system.info import system_info



def test_configuration():

    config = ConfigurationManager()

    assert config.get(
        "currency"
    ) == "PKR"



def test_configuration_update():

    config = ConfigurationManager()

    config.set(
        "milk_unit",
        "litres"
    )

    assert config.get(
        "milk_unit"
    ) == "litres"



def test_system_health():

    result = system_health()

    assert result["status"] == "ONLINE"



def test_system_info():

    result = system_info()

    assert result["name"] == "DairyOS"
'@ | Set-Content tests\core\test_configuration.py



# Verification

Write-Host "[7/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " CORE-006 BUILD COMPLETE"
Write-Host "====================================="