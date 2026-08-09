$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-062 Animal Lifecycle Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\lifecycle\models",
"dairyos\herd\lifecycle\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class AnimalLifecycle:


    animal_id: str

    age_months: int

    stage: str

    priority: str

    required_actions: list
'@ | Set-Content `
"dairyos\herd\lifecycle\models\animal_lifecycle.py"



@'
from ..models.animal_lifecycle import AnimalLifecycle



class AnimalLifecycleService:



    def evaluate(

        self,

        animal_id,

        age_months,

        pregnant=False,

        lactating=False,

        dry=False

    ):


        if age_months < 12:

            stage = "CALF"

            priority = "NORMAL"

            actions = [

                "Monitor growth",

                "Maintain calf nutrition"

            ]



        elif pregnant and age_months >= 22:

            stage = "PREGNANT HEIFER"

            priority = "HIGH"

            actions = [

                "Prepare maternity area",

                "Confirm ration adjustment",

                "Schedule health check"

            ]



        elif lactating:

            stage = "LACTATING COW"

            priority = "HIGH"

            actions = [

                "Monitor milk production",

                "Review health status"

            ]



        elif dry:

            stage = "DRY COW"

            priority = "MEDIUM"

            actions = [

                "Prepare calving plan"

            ]



        else:

            stage = "HEIFER"

            priority = "NORMAL"

            actions = [

                "Monitor development"

            ]



        return AnimalLifecycle(

            animal_id,

            age_months,

            stage,

            priority,

            actions

        )
'@ | Set-Content `
"dairyos\herd\lifecycle\services\animal_lifecycle_service.py"



@'
from dairyos.herd.lifecycle.services.animal_lifecycle_service import AnimalLifecycleService



def test_calf_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-001",

        6

    )

    assert animal.stage == "CALF"



def test_heifer_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-002",

        18

    )

    assert animal.stage == "HEIFER"



def test_pregnant_heifer_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-003",

        26,

        pregnant=True

    )

    assert animal.stage == "PREGNANT HEIFER"



def test_pregnant_priority():

    animal = AnimalLifecycleService().evaluate(

        "HF-003",

        26,

        pregnant=True

    )

    assert animal.priority == "HIGH"



def test_maternity_action():

    animal = AnimalLifecycleService().evaluate(

        "HF-003",

        26,

        pregnant=True

    )

    assert "Prepare maternity area" in animal.required_actions



def test_lactating_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-004",

        36,

        lactating=True

    )

    assert animal.stage == "LACTATING COW"



def test_lactating_action():

    animal = AnimalLifecycleService().evaluate(

        "HF-004",

        36,

        lactating=True

    )

    assert "Monitor milk production" in animal.required_actions



def test_dry_stage():

    animal = AnimalLifecycleService().evaluate(

        "HF-005",

        40,

        dry=True

    )

    assert animal.stage == "DRY COW"



def test_animal_id_saved():

    animal = AnimalLifecycleService().evaluate(

        "HF-006",

        20

    )

    assert animal.animal_id == "HF-006"



def test_lifecycle_flow():

    animal = AnimalLifecycleService().evaluate(

        "HF-007",

        26,

        pregnant=True

    )

    assert animal.priority == "HIGH"
'@ | Set-Content `
"tests\core\test_animal_lifecycle.py"



Write-Host "HERD-062 Animal Lifecycle Build Complete"