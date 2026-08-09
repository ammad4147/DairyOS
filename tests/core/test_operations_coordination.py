from dairyos.herd.dashboard.services.operations_coordination_service import OperationsCoordinationService



def test_task_creation():

    task = OperationsCoordinationService().create_task(

        "Review feed quality",

        "Farm Manager",

        "HIGH",

        "Today"

    )

    assert task.task == "Review feed quality"



def test_assignment():

    task = OperationsCoordinationService().create_task(

        "Check health",

        "Veterinarian",

        "HIGH",

        "Today"

    )

    assert task.assigned_to == "Veterinarian"



def test_priority():

    task = OperationsCoordinationService().create_task(

        "Review feed",

        "Manager",

        "HIGH",

        "Today"

    )

    assert task.priority == "HIGH"



def test_initial_status():

    task = OperationsCoordinationService().create_task(

        "Action",

        "Manager",

        "MEDIUM",

        "Tomorrow"

    )

    assert task.status == "PENDING"



def test_due_date():

    task = OperationsCoordinationService().create_task(

        "Action",

        "Manager",

        "LOW",

        "Tomorrow"

    )

    assert task.due == "Tomorrow"



def test_complete_task():

    service = OperationsCoordinationService()

    task = service.create_task(

        "Action",

        "Manager",

        "HIGH",

        "Today"

    )

    result = service.complete_task(task)

    assert result.status == "COMPLETED"



def test_pending_check():

    service = OperationsCoordinationService()

    task = service.create_task(

        "Action",

        "Manager",

        "HIGH",

        "Today"

    )

    assert service.is_pending(task)



def test_completed_not_pending():

    service = OperationsCoordinationService()

    task = service.create_task(

        "Action",

        "Manager",

        "HIGH",

        "Today"

    )

    service.complete_task(task)

    assert not service.is_pending(task)



def test_model_fields():

    task = OperationsCoordinationService().create_task(

        "Action",

        "Manager",

        "HIGH",

        "Today"

    )

    assert task.priority == "HIGH"



def test_operations_flow():

    service = OperationsCoordinationService()

    task = service.create_task(

        "Review feed quality",

        "Farm Manager",

        "HIGH",

        "Today"

    )

    service.complete_task(task)

    assert task.status == "COMPLETED"
