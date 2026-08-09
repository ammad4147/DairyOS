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
