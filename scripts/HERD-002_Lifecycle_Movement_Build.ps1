# =========================================
# DairyOS Build Script
# HERD-002
# Animal Lifecycle & Movement Engine
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS HERD-002 Build"
Write-Host " Animal Lifecycle & Movement Engine"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/7] Creating folders..."

$folders = @(
    "dairyos\herd\lifecycle",
    "dairyos\herd\lifecycle\models",
    "dairyos\herd\lifecycle\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}


# Init files

Write-Host "[2/7] Creating package files..."

$files = @(
    "dairyos\herd\lifecycle\__init__.py",
    "dairyos\herd\lifecycle\models\__init__.py",
    "dairyos\herd\lifecycle\services\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}



# Lifecycle Event Model

Write-Host "[3/7] Writing lifecycle models..."

@'
from dataclasses import dataclass
from datetime import datetime



@dataclass
class LifecycleEvent:

    animal_id: str

    previous_status: str

    new_status: str

    location: str

    event_type: str

    timestamp: datetime = datetime.utcnow()
'@ | Set-Content dairyos\herd\lifecycle\models\lifecycle_event.py



# Movement Model

@'
from dataclasses import dataclass
from datetime import datetime



@dataclass
class AnimalMovement:

    animal_id: str

    from_location: str

    to_location: str

    reason: str

    timestamp: datetime = datetime.utcnow()
'@ | Set-Content dairyos\herd\lifecycle\models\movement.py



# Export Models

@'
from .lifecycle_event import LifecycleEvent
from .movement import AnimalMovement
'@ | Set-Content dairyos\herd\lifecycle\models\__init__.py



# Lifecycle Service

Write-Host "[4/7] Writing lifecycle services..."

@'
from ..models.lifecycle_event import LifecycleEvent



class LifecycleEngine:


    def __init__(self):

        self.history = []



    def transition(
        self,
        animal,
        new_status
    ):

        event = LifecycleEvent(

            animal_id=animal.animal_id,

            previous_status=animal.status.value,

            new_status=new_status.value,

            location=animal.location,

            event_type="STATUS_CHANGE"

        )


        animal.status = new_status


        self.history.append(event)


        return event
'@ | Set-Content dairyos\herd\lifecycle\services\lifecycle_engine.py



# Movement Service

@'
from ..models.movement import AnimalMovement



class MovementEngine:


    def __init__(self):

        self.movements = []



    def move(
        self,
        animal,
        new_location,
        reason
    ):

        movement = AnimalMovement(

            animal_id=animal.animal_id,

            from_location=animal.location,

            to_location=new_location,

            reason=reason

        )


        animal.location = new_location


        self.movements.append(
            movement
        )


        return movement
'@ | Set-Content dairyos\herd\lifecycle\services\movement_engine.py



# Tests

Write-Host "[5/7] Creating tests..."

@'
from datetime import date

from dairyos.herd.models import (
    Animal,
    AnimalStatus
)

from dairyos.herd.lifecycle.services.lifecycle_engine import (
    LifecycleEngine
)

from dairyos.herd.lifecycle.services.movement_engine import (
    MovementEngine
)



def create_animal():

    return Animal(

        animal_id="HF-1001",

        ear_tag="1001",

        breed="Holstein Friesian",

        gender="FEMALE",

        birth_date=date.today(),

        status=AnimalStatus.HEIFER,

        location="Heifer Area"

    )



def test_lifecycle_transition():

    animal = create_animal()

    engine = LifecycleEngine()


    event = engine.transition(

        animal,

        AnimalStatus.MILKING_COW

    )


    assert event.new_status == "MILKING_COW"

    assert animal.status == AnimalStatus.MILKING_COW



def test_animal_movement():

    animal = create_animal()

    engine = MovementEngine()


    movement = engine.move(

        animal,

        "Main Dairy Shed",

        "Ready for production"

    )


    assert movement.to_location == "Main Dairy Shed"

    assert animal.location == "Main Dairy Shed"
'@ | Set-Content tests\core\test_herd_lifecycle.py



# Verification

Write-Host "[6/7] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " HERD-002 BUILD COMPLETE"
Write-Host "====================================="