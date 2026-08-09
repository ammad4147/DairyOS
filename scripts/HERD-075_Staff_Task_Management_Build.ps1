$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-075 Staff Task Management Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\operations\staff\models",
"dairyos\operations\staff\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class StaffTask:


    task_id: str

    task_name: str

    assigned_team: str

    priority: str

    status: str

    action: str
'@ | Set-Content `
"dairyos\operations\staff\models\staff_task.py"



@'
from ..models.staff_task import StaffTask



class StaffTaskManagementService:



    def evaluate(

        self,

        task_id,

        task_name,

        assigned_team,

        urgency

    ):


        if urgency.lower() == "high":

            priority = "HIGH"

            status = "PENDING"

            action = "Complete immediately"



        elif urgency.lower() == "medium":

            priority = "MEDIUM"

            status = "SCHEDULED"

            action = "Complete according to schedule"



        else:

            priority = "NORMAL"

            status = "PLANNED"

            action = "Continue routine monitoring"



        return StaffTask(

            task_id,

            task_name,

            assigned_team,

            priority,

            status,

            action

        )
'@ | Set-Content `
"dairyos\operations\staff\services\staff_task_management_service.py"



@'
from dairyos.operations.staff.services.staff_task_management_service import StaffTaskManagementService



def test_task_id():

    result = StaffTaskManagementService().evaluate(

        "TASK-001",

        "Morning Milking",

        "Milker Team A",

        "High"

    )

    assert result.task_id == "TASK-001"



def test_task_name():

    result = StaffTaskManagementService().evaluate(

        "TASK-001",

        "Morning Milking",

        "Milker Team A",

        "High"

    )

    assert result.task_name == "Morning Milking"



def test_team_assignment():

    result = StaffTaskManagementService().evaluate(

        "TASK-001",

        "Morning Milking",

        "Milker Team A",

        "High"

    )

    assert result.assigned_team == "Milker Team A"



def test_high_priority():

    result = StaffTaskManagementService().evaluate(

        "TASK-001",

        "Morning Milking",

        "Milker Team A",

        "High"

    )

    assert result.priority == "HIGH"



def test_high_status():

    result = StaffTaskManagementService().evaluate(

        "TASK-001",

        "Morning Milking",

        "Milker Team A",

        "High"

    )

    assert result.status == "PENDING"



def test_high_action():

    result = StaffTaskManagementService().evaluate(

        "TASK-001",

        "Morning Milking",

        "Milker Team A",

        "High"

    )

    assert result.action == "Complete immediately"



def test_medium_task():

    result = StaffTaskManagementService().evaluate(

        "TASK-002",

        "Feed Distribution",

        "Feed Team",

        "Medium"

    )

    assert result.priority == "MEDIUM"



def test_low_task():

    result = StaffTaskManagementService().evaluate(

        "TASK-003",

        "Cleaning",

        "Farm Team",

        "Low"

    )

    assert result.priority == "NORMAL"



def test_action_exists():

    result = StaffTaskManagementService().evaluate(

        "TASK-004",

        "Inspection",

        "Supervisor",

        "Medium"

    )

    assert len(result.action) > 0



def test_staff_flow():

    result = StaffTaskManagementService().evaluate(

        "TASK-005",

        "Morning Milking",

        "Milker Team A",

        "High"

    )

    assert result.status == "PENDING"
'@ | Set-Content `
"tests\core\test_staff_task_management.py"



Write-Host "HERD-075 Staff Task Management Build Complete"