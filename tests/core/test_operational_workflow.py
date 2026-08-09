from dairyos.herd.dashboard.services.operational_workflow_service import OperationalWorkflowService



def test_workflow_creation():

    workflow = OperationalWorkflowService().create_workflow(

        "Production Investigation",

        [

            "Review feed",

            "Check health"

        ]

    )

    assert workflow.name == "Production Investigation"



def test_steps_created():

    workflow = OperationalWorkflowService().create_workflow(

        "Investigation",

        [

            "Step 1",

            "Step 2"

        ]

    )

    assert len(workflow.steps) == 2



def test_initial_status():

    workflow = OperationalWorkflowService().create_workflow(

        "Investigation",

        [

            "Step"

        ]

    )

    assert workflow.status == "PENDING"



def test_complete_first_step():

    service = OperationalWorkflowService()

    workflow = service.create_workflow(

        "Investigation",

        [

            "Feed",

            "Health"

        ]

    )

    service.complete_step(

        workflow,

        "Feed"

    )

    assert len(workflow.steps) == 1



def test_complete_workflow():

    service = OperationalWorkflowService()

    workflow = service.create_workflow(

        "Investigation",

        [

            "Feed"

        ]

    )

    service.complete_step(

        workflow,

        "Feed"

    )

    assert workflow.status == "COMPLETED"



def test_completion_check():

    service = OperationalWorkflowService()

    workflow = service.create_workflow(

        "Investigation",

        [

            "Feed"

        ]

    )

    service.complete_step(

        workflow,

        "Feed"

    )

    assert service.is_complete(workflow)



def test_pending_workflow():

    workflow = OperationalWorkflowService().create_workflow(

        "Investigation",

        [

            "Feed"

        ]

    )

    assert workflow.status == "PENDING"



def test_multiple_steps():

    workflow = OperationalWorkflowService().create_workflow(

        "Health Review",

        [

            "Check temperature",

            "Review records",

            "Schedule visit"

        ]

    )

    assert len(workflow.steps) == 3



def test_remaining_steps():

    service = OperationalWorkflowService()

    workflow = service.create_workflow(

        "Workflow",

        [

            "A",

            "B"

        ]

    )

    service.complete_step(

        workflow,

        "A"

    )

    assert "B" in workflow.steps



def test_model():

    workflow = OperationalWorkflowService().create_workflow(

        "Routine",

        []

    )

    assert workflow.name == "Routine"
