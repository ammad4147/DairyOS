# =========================================
# DairyOS Build Script
# CORE-005
# Notification & Alert Foundation
# Version 1.0
# =========================================

Write-Host ""
Write-Host "====================================="
Write-Host " DairyOS CORE-005 Build"
Write-Host " Notification & Alert Foundation"
Write-Host "====================================="
Write-Host ""


# Create folders

Write-Host "[1/6] Creating folders..."

$folders = @(
    "dairyos\core\notifications",
    "dairyos\core\notifications\models",
    "dairyos\core\notifications\services",
    "dairyos\core\alerts",
    "dairyos\core\alerts\models",
    "dairyos\core\alerts\services"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}


# Create package files

Write-Host "[2/6] Creating package files..."

$files = @(
    "dairyos\core\notifications\__init__.py",
    "dairyos\core\notifications\models\__init__.py",
    "dairyos\core\notifications\services\__init__.py",
    "dairyos\core\alerts\__init__.py",
    "dairyos\core\alerts\models\__init__.py",
    "dairyos\core\alerts\services\__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}


# Notification Model

Write-Host "[3/6] Writing notification system..."

@'
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Notification:

    recipient: str

    message: str

    priority: str = "INFO"

    status: str = "NEW"

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )
'@ | Set-Content dairyos\core\notifications\models\notification.py


@'
from .notification import Notification
'@ | Set-Content dairyos\core\notifications\models\__init__.py



# Priority Engine

@'
PRIORITIES = [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
    "INFO"
]


def is_valid_priority(priority):

    return priority in PRIORITIES
'@ | Set-Content dairyos\core\notifications\services\priority.py



# Notification Dispatcher

@'
from ..models.notification import Notification


class NotificationDispatcher:


    def __init__(self):

        self.notifications = []


    def send(
        self,
        notification: Notification
    ):

        self.notifications.append(
            notification
        )

        return notification
'@ | Set-Content dairyos\core\notifications\services\dispatcher.py



# Alert Model

Write-Host "[4/6] Writing alert engine..."

@'
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Alert:

    event_type: str

    message: str

    priority: str

    created_at: datetime = datetime.utcnow()
'@ | Set-Content dairyos\core\alerts\models\alert.py


@'
from .alert import Alert
'@ | Set-Content dairyos\core\alerts\models\__init__.py



# Alert Engine

@'
from ..models.alert import Alert


class AlertEngine:


    def create_alert(
        self,
        event_type,
        message,
        priority
    ):

        return Alert(
            event_type=event_type,
            message=message,
            priority=priority
        )
'@ | Set-Content dairyos\core\alerts\services\alert_engine.py



# Tests

Write-Host "[5/6] Creating tests..."

@'
from dairyos.core.notifications.models import Notification
from dairyos.core.notifications.services.dispatcher import NotificationDispatcher

from dairyos.core.alerts.services.alert_engine import AlertEngine



def test_notification_dispatch():

    dispatcher = NotificationDispatcher()

    notification = Notification(
        recipient="FARM_MANAGER",
        message="Check new calf"
    )

    result = dispatcher.send(
        notification
    )

    assert result.status == "NEW"



def test_alert_creation():

    engine = AlertEngine()

    alert = engine.create_alert(
        "ANIMAL_HEALTH",
        "High temperature detected",
        "HIGH"
    )

    assert alert.priority == "HIGH"
'@ | Set-Content tests\core\test_notifications.py



# Verification

Write-Host "[6/6] Running verification..."

pytest


Write-Host ""
Write-Host "====================================="
Write-Host " CORE-005 BUILD COMPLETE"
Write-Host "====================================="