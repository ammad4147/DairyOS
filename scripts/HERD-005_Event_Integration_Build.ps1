# =========================================
# DairyOS Build Script
# HERD-005
# Herd Event Integration Engine
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-005 Build"
Write-Host " Herd Event Integration Engine"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\herd\events",
    "dairyos\herd\events\models",
    "dairyos\herd\events\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}



# Init files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\herd\events\__init__.py",
    "dairyos\herd\events\models\__init__.py",
    "dairyos\herd\events\services\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}



# Event Model

Write-Host "[3/7] Writing event models..."

@'
from dataclasses import dataclass
from datetime import datetime



@dataclass
class HerdEvent:


    animal_id: str

    event_type: str

    description: str

    timestamp: datetime = datetime.utcnow()
'@ | Set-Content dairyos\herd\events\models\herd_event.py



@'
from .herd_event import HerdEvent
'@ | Set-Content dairyos\herd\events\models\__init__.py



# Event Handler

Write-Host "[4/7] Writing event handler..."

@'
class HerdEventHandler:



    def __init__(self):

        self.events = []



    def publish(

        self,

        event

    ):

        self.events.append(event)

        return event



    def count(self):

        return len(self.events)
'@ | Set-Content dairyos\herd\events\services\herd_event_handler.py



# Event Factory

@'
from ..models.herd_event import HerdEvent



class HerdEventFactory:



    def create(

        self,

        animal_id,

        event_type,

        description

    ):


        return HerdEvent(

            animal_id=animal_id,

            event_type=event_type,

            description=description

        )
'@ | Set-Content dairyos\herd\events\services\event_factory.py



# Tests

Write-Host "[5/7] Creating tests..."

@'
from dairyos.herd.events.services.herd_event_handler import (
    HerdEventHandler
)

from dairyos.herd.events.services.event_factory import (
    HerdEventFactory
)



def test_event_creation():


    factory = HerdEventFactory()


    event = factory.create(

        "HF-0001",

        "BIRTH",

        "New calf born"

    )


    assert event.event_type == "BIRTH"



def test_event_publish():


    factory = HerdEventFactory()

    handler = HerdEventHandler()


    event = factory.create(

        "HF-0001",

        "MOVE",

        "Moved to shed"

    )


    handler.publish(event)


    assert handler.count() == 1
'@ | Set-Content tests\core\test_herd_events.py



# Verification

Write-Host "[6/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-005 BUILD COMPLETE"
Write-Host "====================================="