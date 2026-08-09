# =========================================
# DairyOS Build Script
# CORE-004
# Event & Workflow Engine
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS CORE-004 Build"
Write-Host " Event & Workflow Engine"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/6] Creating folders..."

$folders = @(
    "dairyos\core\events",
    "dairyos\core\events\models",
    "dairyos\core\events\services",
    "dairyos\core\workflows",
    "dairyos\core\workflows\rules",
    "dairyos\core\workflows\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}


# Create init files

Write-Host "[2/6] Creating package files..."

$initFiles = @(
    "dairyos\core\events\__init__.py",
    "dairyos\core\events\models\__init__.py",
    "dairyos\core\events\services\__init__.py",
    "dairyos\core\workflows\__init__.py",
    "dairyos\core\workflows\rules\__init__.py",
    "dairyos\core\workflows\services\__init__.py"
)

foreach ($file in $initFiles) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}


# Event Model

Write-Host "[3/6] Writing event engine..."

@'
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DairyEvent:

    event_type: str

    source: str

    data: dict[str, Any]

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )
'@ | Set-Content dairyos\core\events\models\event.py


@'
from .event import DairyEvent
'@ | Set-Content dairyos\core\events\models\__init__.py


# Event Publisher

@'
from ..models.event import DairyEvent


class EventPublisher:

    def __init__(self):

        self.events = []


    def publish(self, event: DairyEvent):

        self.events.append(event)

        return event
'@ | Set-Content dairyos\core\events\services\publisher.py


# Event Handler

@'
class EventHandlerRegistry:


    def __init__(self):

        self.handlers = {}


    def register(
        self,
        event_type,
        handler
    ):

        self.handlers[event_type] = handler


    def handle(self, event):

        handler = self.handlers.get(
            event.event_type
        )

        if handler:
            return handler(event)

        return None
'@ | Set-Content dairyos\core\events\services\handler.py



# Workflow Engine

Write-Host "[4/6] Writing workflow engine..."

@'
class WorkflowEngine:


    def __init__(self):

        self.rules = []


    def add_rule(self, rule):

        self.rules.append(rule)


    def evaluate(self, event):

        results = []

        for rule in self.rules:

            result = rule(event)

            if result:
                results.append(result)

        return results
'@ | Set-Content dairyos\core\workflows\rules\engine.py



# Business Rule

@'
def calving_rule(event):

    if event.event_type == "CALVING_COMPLETED":

        return {
            "action": "CREATE_CALF_RECORD"
        }

    return None
'@ | Set-Content dairyos\core\workflows\rules\animal_rules.py



# Test

Write-Host "[5/6] Creating tests..."

@'
from dairyos.core.events.models import DairyEvent
from dairyos.core.events.services.publisher import EventPublisher

from dairyos.core.workflows.rules.engine import WorkflowEngine
from dairyos.core.workflows.rules.animal_rules import calving_rule



def test_event_publish():

    publisher = EventPublisher()

    event = DairyEvent(
        event_type="CALVING_COMPLETED",
        source="HerdOS",
        data={
            "animal_id":101
        }
    )

    result = publisher.publish(event)

    assert result.event_type == "CALVING_COMPLETED"



def test_workflow_rule():

    engine = WorkflowEngine()

    engine.add_rule(calving_rule)

    event = DairyEvent(
        event_type="CALVING_COMPLETED",
        source="HerdOS",
        data={}
    )

    result = engine.evaluate(event)

    assert result[0]["action"] == "CREATE_CALF_RECORD"
'@ | Set-Content tests\core\test_events.py



# Verification

Write-Host "[6/6] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " CORE-004 BUILD COMPLETE"
Write-Host "====================================="