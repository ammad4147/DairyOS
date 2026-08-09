$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-070 Replacement Planning Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\replacement\models",
"dairyos\herd\replacement\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class ReplacementPlan:


    current_lactating_cows: int

    culling_rate: float

    required_replacements: int

    available_heifers: int

    status: str

    action: str
'@ | Set-Content `
"dairyos\herd\replacement\models\replacement_plan.py"



@'
from ..models.replacement_plan import ReplacementPlan



class ReplacementPlanningService:



    def evaluate(

        self,

        current_lactating_cows,

        culling_rate,

        available_heifers

    ):


        required_replacements = int(

            current_lactating_cows * culling_rate

        )



        if available_heifers >= required_replacements:

            status = "SECURE"

            action = "Continue development program"


        else:

            status = "SHORTAGE"

            action = "Increase replacement planning"



        return ReplacementPlan(

            current_lactating_cows,

            culling_rate,

            required_replacements,

            available_heifers,

            status,

            action

        )
'@ | Set-Content `
"dairyos\herd\replacement\services\replacement_planning_service.py"



@'
from dairyos.herd.replacement.services.replacement_planning_service import ReplacementPlanningService



def test_current_cows():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.current_lactating_cows == 25



def test_culling_rate():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.culling_rate == 0.15



def test_required_replacements():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.required_replacements == 3



def test_available_heifers():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.available_heifers == 8



def test_secure_status():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.status == "SECURE"



def test_secure_action():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.action == "Continue development program"



def test_shortage_status():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        2

    )

    assert result.status == "SHORTAGE"



def test_shortage_action():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        2

    )

    assert result.action == "Increase replacement planning"



def test_growth_scenario():

    result = ReplacementPlanningService().evaluate(

        50,

        0.15,

        10

    )

    assert result.required_replacements == 7



def test_replacement_flow():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.status == "SECURE"
'@ | Set-Content `
"tests\core\test_replacement_planning.py"



Write-Host "HERD-070 Replacement Planning Build Complete"