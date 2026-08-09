$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-071 Culling Management Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\culling\models",
"dairyos\herd\culling\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class CullingDecision:


    animal_id: str

    production_status: str

    health_status: str

    replacement_available: bool

    recommendation: str

    action: str
'@ | Set-Content `
"dairyos\herd\culling\models\culling_decision.py"



@'
from ..models.culling_decision import CullingDecision



class CullingManagementService:



    def evaluate(

        self,

        animal_id,

        production_status,

        health_status,

        replacement_available

    ):


        if (

            production_status.lower() == "below target"

            and health_status.lower() == "repeated issues"

            and replacement_available

        ):

            recommendation = "CONSIDER CULLING"

            action = "Veterinary and economic assessment"



        elif health_status.lower() == "repeated issues":

            recommendation = "REVIEW"

            action = "Health intervention required"



        else:

            recommendation = "RETAIN"

            action = "Continue normal management"



        return CullingDecision(

            animal_id,

            production_status,

            health_status,

            replacement_available,

            recommendation,

            action

        )
'@ | Set-Content `
"dairyos\herd\culling\services\culling_management_service.py"



@'
from dairyos.herd.culling.services.culling_management_service import CullingManagementService



def test_animal_id():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.animal_id == "HF-1040"



def test_production_status():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.production_status == "Below Target"



def test_health_status():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.health_status == "Repeated Issues"



def test_replacement_status():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.replacement_available is True



def test_culling_recommendation():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.recommendation == "CONSIDER CULLING"



def test_culling_action():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.action == "Veterinary and economic assessment"



def test_health_review():

    result = CullingManagementService().evaluate(

        "HF-1041",

        "Normal",

        "Repeated Issues",

        False

    )

    assert result.recommendation == "REVIEW"



def test_retain_animal():

    result = CullingManagementService().evaluate(

        "HF-1042",

        "On Target",

        "Healthy",

        False

    )

    assert result.recommendation == "RETAIN"



def test_action_exists():

    result = CullingManagementService().evaluate(

        "HF-1043",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert len(result.action) > 0



def test_culling_flow():

    result = CullingManagementService().evaluate(

        "HF-1044",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.recommendation == "CONSIDER CULLING"
'@ | Set-Content `
"tests\core\test_culling_management.py"



Write-Host "HERD-071 Culling Management Build Complete"