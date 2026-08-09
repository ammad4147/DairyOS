$root = "C:\DairyOS"

Write-Host "Starting HERD-014 Intelligence Integration Build..." -ForegroundColor Cyan


# Create directories

$directories = @(
    "dairyos\herd\events\services",
    "dairyos\herd\intelligence\models",
    "dairyos\herd\intelligence\services",
    "tests\core"
)

foreach ($dir in $directories) {

    $path = Join-Path $root $dir

    if (!(Test-Path $path)) {

        New-Item -ItemType Directory -Path $path -Force | Out-Null

    }

}


# HERD Decision Model

@'
from dataclasses import dataclass


@dataclass
class HerdDecision:

    risk_level: str

    attention_required: bool

    recommendations: list
'@ | Set-Content `
"$root\dairyos\herd\intelligence\models\herd_decision.py"


# Decision Service

@'
from dairyos.herd.intelligence.models.herd_decision import HerdDecision


class DecisionService:


    def evaluate(
        self,
        open_cows=0,
        health_alerts=0,
        replacement_shortage=False
    ):

        recommendations = []

        risk = "LOW"

        attention = False


        if health_alerts > 0:

            attention = True

            recommendations.append(
                "Review animal health alerts"
            )


        if open_cows > 3:

            attention = True

            recommendations.append(
                "Review reproductive performance"
            )


        if replacement_shortage:

            risk = "HIGH"

            attention = True

            recommendations.append(
                "Replacement pipeline shortage detected"
            )


        elif attention:

            risk = "MEDIUM"


        return HerdDecision(

            risk_level=risk,

            attention_required=attention,

            recommendations=recommendations

        )
'@ | Set-Content `
"$root\dairyos\herd\intelligence\services\decision_service.py"



# Event Intelligence Bridge

@'
class EventIntelligenceBridge:


    def analyze(self, event_type):

        impacts = {

            "BIRTH": [
                "New calf registered"
            ],

            "CALVING": [
                "Lactation cycle started"
            ],

            "MORTALITY": [
                "Animal loss recorded"
            ],

            "SALE": [
                "Animal inventory reduced"
            ]

        }


        return impacts.get(

            event_type,

            []

        )
'@ | Set-Content `
"$root\dairyos\herd\events\services\event_intelligence_bridge.py"



# Integration Tests

@'
from dairyos.herd.intelligence.services.decision_service import DecisionService
from dairyos.herd.events.services.event_intelligence_bridge import EventIntelligenceBridge


def test_low_risk_decision():

    service = DecisionService()

    result = service.evaluate()

    assert result.risk_level == "LOW"

    assert result.attention_required is False



def test_health_alert_decision():

    service = DecisionService()

    result = service.evaluate(
        health_alerts=2
    )

    assert result.attention_required is True

    assert "Review animal health alerts" in result.recommendations



def test_reproduction_warning():

    service = DecisionService()

    result = service.evaluate(
        open_cows=5
    )

    assert result.risk_level == "MEDIUM"



def test_replacement_shortage():

    service = DecisionService()

    result = service.evaluate(
        replacement_shortage=True
    )

    assert result.risk_level == "HIGH"



def test_event_birth_bridge():

    bridge = EventIntelligenceBridge()

    result = bridge.analyze(
        "BIRTH"
    )

    assert "New calf registered" in result



def test_event_calving_bridge():

    bridge = EventIntelligenceBridge()

    result = bridge.analyze(
        "CALVING"
    )

    assert "Lactation cycle started" in result
'@ | Set-Content `
"$root\tests\core\test_herd_intelligence_integration.py"



Write-Host ""
Write-Host "HERD-014 Build Completed Successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Run tests with:"
Write-Host "pytest tests/core/test_herd_intelligence_integration.py -v"