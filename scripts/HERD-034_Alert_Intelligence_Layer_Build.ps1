$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-034 Alert Intelligence Layer Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class IntelligentAlert:


    category: str

    issue: str

    severity: str

    urgency: str

    priority_score: int

    recommended_action: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\intelligent_alert.py"



@'
from ..models.intelligent_alert import IntelligentAlert



class AlertIntelligenceService:



    def generate_alert(

        self,

        category,

        issue,

        severity="LOW"

    ):


        if severity == "HIGH":

            urgency = "IMMEDIATE"

            score = 90


        elif severity == "MEDIUM":

            urgency = "ATTENTION"

            score = 60


        else:

            urgency = "MONITOR"

            score = 30



        action_map = {

            "HEALTH": "Review animal health alerts",

            "REPRODUCTION": "Review breeding performance",

            "HERD STRATEGY": "Review replacement pipeline",

            "PRODUCTION": "Review production performance",

            "FINANCE": "Review financial indicators"

        }



        action = action_map.get(

            category,

            "Review farm condition"

        )



        return IntelligentAlert(

            category,

            issue,

            severity,

            urgency,

            score,

            action

        )



    def rank_alerts(

        self,

        alerts

    ):


        return sorted(

            alerts,

            key=lambda x: x.priority_score,

            reverse=True

        )



    def highest_priority(

        self,

        alerts

    ):


        ranked = self.rank_alerts(alerts)


        if not ranked:

            return None


        return ranked[0]
'@ | Set-Content `
"dairyos\herd\dashboard\services\alert_intelligence_service.py"



@'
from dairyos.herd.dashboard.services.alert_intelligence_service import AlertIntelligenceService



def test_high_alert_creation():

    alert = AlertIntelligenceService().generate_alert(

        "HEALTH",

        "Disease warning",

        "HIGH"

    )

    assert alert.severity == "HIGH"



def test_high_alert_urgency():

    alert = AlertIntelligenceService().generate_alert(

        "REPRODUCTION",

        "Open cows",

        "HIGH"

    )

    assert alert.urgency == "IMMEDIATE"



def test_low_alert():

    alert = AlertIntelligenceService().generate_alert(

        "PRODUCTION",

        "Monitor output"

    )

    assert alert.priority_score == 30



def test_health_action():

    alert = AlertIntelligenceService().generate_alert(

        "HEALTH",

        "Issue"

    )

    assert alert.recommended_action == "Review animal health alerts"



def test_reproduction_action():

    alert = AlertIntelligenceService().generate_alert(

        "REPRODUCTION",

        "Issue"

    )

    assert alert.recommended_action == "Review breeding performance"



def test_alert_ranking():

    service = AlertIntelligenceService()

    alerts = [

        service.generate_alert(

            "HEALTH",

            "Issue",

            "LOW"

        ),

        service.generate_alert(

            "HERD STRATEGY",

            "Issue",

            "HIGH"

        )

    ]


    ranked = service.rank_alerts(alerts)


    assert ranked[0].severity == "HIGH"



def test_highest_priority():

    service = AlertIntelligenceService()

    alerts = [

        service.generate_alert(

            "FINANCE",

            "Issue",

            "MEDIUM"

        ),

        service.generate_alert(

            "HEALTH",

            "Issue",

            "HIGH"

        )

    ]


    assert service.highest_priority(alerts).category == "HEALTH"



def test_empty_alerts():

    assert AlertIntelligenceService().highest_priority([]) is None



def test_score_generation():

    alert = AlertIntelligenceService().generate_alert(

        "FINANCE",

        "Cash warning",

        "MEDIUM"

    )

    assert alert.priority_score == 60



def test_alert_model():

    alert = AlertIntelligenceService().generate_alert(

        "HERD STRATEGY",

        "Replacement shortage",

        "HIGH"

    )

    assert alert.category == "HERD STRATEGY"
'@ | Set-Content `
"tests\core\test_alert_intelligence.py"



Write-Host "HERD-034 Alert Intelligence Layer Build Complete"