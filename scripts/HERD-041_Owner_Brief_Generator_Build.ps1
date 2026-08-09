$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-041 Owner Brief Generator Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class OwnerBrief:


    farm_name: str

    status: str

    primary_issue: str

    risk_level: str

    recommendation: str

    owner_action: str

    confidence: int
'@ | Set-Content `
"dairyos\herd\dashboard\models\owner_brief.py"



@'
from ..models.owner_brief import OwnerBrief



class OwnerBriefService:



    def generate(

        self,

        farm_name,

        issue,

        risk_level,

        recommendation,

        confidence

    ):


        if risk_level in (

            "CRITICAL",

            "HIGH"

        ):

            status = "ATTENTION REQUIRED"

            owner_action = "Review and act on recommendation"

        else:

            status = "STABLE"

            owner_action = "Continue monitoring"



        return OwnerBrief(

            farm_name,

            status,

            issue,

            risk_level,

            recommendation,

            owner_action,

            confidence

        )



    def format_summary(

        self,

        brief

    ):


        return (

            f"{brief.farm_name}\n"

            f"Status: {brief.status}\n"

            f"Issue: {brief.primary_issue}\n"

            f"Action: {brief.owner_action}"

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\owner_brief_service.py"



@'
from dairyos.herd.dashboard.services.owner_brief_service import OwnerBriefService



def test_owner_brief_creation():

    brief = OwnerBriefService().generate(

        "Trident Dairies",

        "Replacement shortage",

        "HIGH",

        "Begin acquisition planning",

        85

    )

    assert brief.farm_name == "Trident Dairies"



def test_attention_status():

    brief = OwnerBriefService().generate(

        "Farm",

        "Issue",

        "HIGH",

        "Action",

        80

    )

    assert brief.status == "ATTENTION REQUIRED"



def test_critical_status():

    brief = OwnerBriefService().generate(

        "Farm",

        "Issue",

        "CRITICAL",

        "Action",

        90

    )

    assert brief.status == "ATTENTION REQUIRED"



def test_stable_status():

    brief = OwnerBriefService().generate(

        "Farm",

        "Issue",

        "NORMAL",

        "Monitor",

        60

    )

    assert brief.status == "STABLE"



def test_owner_action():

    brief = OwnerBriefService().generate(

        "Farm",

        "Issue",

        "HIGH",

        "Action",

        90

    )

    assert "Review" in brief.owner_action



def test_confidence():

    brief = OwnerBriefService().generate(

        "Farm",

        "Issue",

        "HIGH",

        "Action",

        85

    )

    assert brief.confidence == 85



def test_recommendation():

    brief = OwnerBriefService().generate(

        "Farm",

        "Issue",

        "HIGH",

        "Feed review",

        75

    )

    assert brief.recommendation == "Feed review"



def test_summary():

    brief = OwnerBriefService().generate(

        "Farm",

        "Issue",

        "HIGH",

        "Action",

        80

    )


    result = OwnerBriefService().format_summary(brief)


    assert "Farm" in result



def test_issue():

    brief = OwnerBriefService().generate(

        "Farm",

        "Milk decline",

        "HIGH",

        "Review production",

        80

    )

    assert brief.primary_issue == "Milk decline"



def test_model():

    brief = OwnerBriefService().generate(

        "Farm",

        "Issue",

        "NORMAL",

        "Monitor",

        50

    )

    assert brief.risk_level == "NORMAL"
'@ | Set-Content `
"tests\core\test_owner_brief.py"



Write-Host "HERD-041 Owner Brief Generator Build Complete"