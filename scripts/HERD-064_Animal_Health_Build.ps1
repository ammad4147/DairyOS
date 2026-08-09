$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-064 Animal Health Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\health\models",
"dairyos\herd\health\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class AnimalHealth:


    animal_id: str

    condition: str

    severity: str

    priority: str

    required_actions: list
'@ | Set-Content `
"dairyos\herd\health\models\animal_health.py"



@'
from ..models.animal_health import AnimalHealth



class AnimalHealthService:



    def evaluate(

        self,

        animal_id,

        condition,

        severity

    ):


        if severity.upper() == "HIGH":

            priority = "HIGH"

            actions = [

                "Veterinary examination",

                "Treatment plan",

                "Monitor milk impact"

            ]



        elif severity.upper() == "MEDIUM":

            priority = "MEDIUM"

            actions = [

                "Review condition",

                "Schedule follow-up"

            ]



        else:

            priority = "NORMAL"

            actions = [

                "Routine monitoring"

            ]



        return AnimalHealth(

            animal_id,

            condition,

            severity,

            priority,

            actions

        )
'@ | Set-Content `
"dairyos\herd\health\services\animal_health_service.py"



@'
from dairyos.herd.health.services.animal_health_service import AnimalHealthService



def test_animal_id():

    result = AnimalHealthService().evaluate(

        "HF-1025",

        "Mastitis suspicion",

        "HIGH"

    )

    assert result.animal_id == "HF-1025"



def test_condition():

    result = AnimalHealthService().evaluate(

        "HF-1025",

        "Mastitis suspicion",

        "HIGH"

    )

    assert result.condition == "Mastitis suspicion"



def test_high_severity():

    result = AnimalHealthService().evaluate(

        "HF-1025",

        "Mastitis suspicion",

        "HIGH"

    )

    assert result.severity == "HIGH"



def test_high_priority():

    result = AnimalHealthService().evaluate(

        "HF-1025",

        "Mastitis suspicion",

        "HIGH"

    )

    assert result.priority == "HIGH"



def test_vet_action():

    result = AnimalHealthService().evaluate(

        "HF-1025",

        "Mastitis suspicion",

        "HIGH"

    )

    assert "Veterinary examination" in result.required_actions



def test_treatment_action():

    result = AnimalHealthService().evaluate(

        "HF-1025",

        "Mastitis suspicion",

        "HIGH"

    )

    assert "Treatment plan" in result.required_actions



def test_medium_priority():

    result = AnimalHealthService().evaluate(

        "HF-1026",

        "Minor issue",

        "MEDIUM"

    )

    assert result.priority == "MEDIUM"



def test_low_priority():

    result = AnimalHealthService().evaluate(

        "HF-1027",

        "Observation",

        "LOW"

    )

    assert result.priority == "NORMAL"



def test_actions_exist():

    result = AnimalHealthService().evaluate(

        "HF-1028",

        "Check",

        "HIGH"

    )

    assert len(result.required_actions) > 0



def test_health_flow():

    result = AnimalHealthService().evaluate(

        "HF-1029",

        "Mastitis suspicion",

        "HIGH"

    )

    assert result.priority == "HIGH"
'@ | Set-Content `
"tests\core\test_animal_health.py"



Write-Host "HERD-064 Animal Health Build Complete"