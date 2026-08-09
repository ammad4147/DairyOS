$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-065 Breeding Management Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\breeding\models",
"dairyos\herd\breeding\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class BreedingManagement:


    animal_id: str

    breeding_event: str

    pregnancy_status: str

    priority: str

    next_action: str
'@ | Set-Content `
"dairyos\herd\breeding\models\breeding_management.py"



@'
from ..models.breeding_management import BreedingManagement



class BreedingManagementService:



    def evaluate(

        self,

        animal_id,

        breeding_event,

        pregnant=False

    ):


        if pregnant:

            pregnancy_status = "PREGNANT"

            priority = "NORMAL"

            next_action = "Prepare calving schedule"



        elif breeding_event.lower() == "ai completed":

            pregnancy_status = "PENDING CONFIRMATION"

            priority = "MEDIUM"

            next_action = "Schedule pregnancy check"



        else:

            pregnancy_status = "NOT BRED"

            priority = "HIGH"

            next_action = "Review breeding plan"



        return BreedingManagement(

            animal_id,

            breeding_event,

            pregnancy_status,

            priority,

            next_action

        )
'@ | Set-Content `
"dairyos\herd\breeding\services\breeding_management_service.py"



@'
from dairyos.herd.breeding.services.breeding_management_service import BreedingManagementService



def test_animal_id():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.animal_id == "HF-1030"



def test_event_saved():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.breeding_event == "AI completed"



def test_pregnancy_confirmed():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.pregnancy_status == "PREGNANT"



def test_pregnancy_priority():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.priority == "NORMAL"



def test_calving_action():

    result = BreedingManagementService().evaluate(

        "HF-1030",

        "AI completed",

        pregnant=True

    )

    assert result.next_action == "Prepare calving schedule"



def test_ai_pending():

    result = BreedingManagementService().evaluate(

        "HF-1031",

        "AI completed",

        pregnant=False

    )

    assert result.pregnancy_status == "PENDING CONFIRMATION"



def test_pending_priority():

    result = BreedingManagementService().evaluate(

        "HF-1031",

        "AI completed",

        pregnant=False

    )

    assert result.priority == "MEDIUM"



def test_not_bred():

    result = BreedingManagementService().evaluate(

        "HF-1032",

        "No breeding",

        pregnant=False

    )

    assert result.pregnancy_status == "NOT BRED"



def test_not_bred_action():

    result = BreedingManagementService().evaluate(

        "HF-1032",

        "No breeding",

        pregnant=False

    )

    assert result.next_action == "Review breeding plan"



def test_breeding_flow():

    result = BreedingManagementService().evaluate(

        "HF-1033",

        "AI completed",

        pregnant=True

    )

    assert result.pregnancy_status == "PREGNANT"
'@ | Set-Content `
"tests\core\test_breeding_management.py"



Write-Host "HERD-065 Breeding Management Build Complete"