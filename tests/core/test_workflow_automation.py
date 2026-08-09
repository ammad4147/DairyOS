from dairyos.herd.dashboard.services.workflow_automation_service import WorkflowAutomationService



def test_production_workflow_creation():

    workflow = WorkflowAutomationService().generate_workflow(

        "Production decline detected"

    )

    assert workflow.workflow_name == "Production Decline Investigation"



def test_trigger_saved():

    workflow = WorkflowAutomationService().generate_workflow(

        "Production decline"

    )

    assert workflow.trigger == "Production decline"



def test_production_priority():

    workflow = WorkflowAutomationService().generate_workflow(

        "Production decline"

    )

    assert workflow.priority == "HIGH"



def test_production_steps():

    workflow = WorkflowAutomationService().generate_workflow(

        "Production decline"

    )

    assert len(workflow.steps) == 4



def test_first_step():

    workflow = WorkflowAutomationService().generate_workflow(

        "Production decline"

    )

    assert workflow.steps[0] == "Review ration"



def test_health_step():

    workflow = WorkflowAutomationService().generate_workflow(

        "Production decline"

    )

    assert "Check health records" in workflow.steps



def test_general_workflow():

    workflow = WorkflowAutomationService().generate_workflow(

        "Routine observation"

    )

    assert workflow.workflow_name == "General Farm Review"



def test_general_priority():

    workflow = WorkflowAutomationService().generate_workflow(

        "Routine observation"

    )

    assert workflow.priority == "MEDIUM"



def test_general_step():

    workflow = WorkflowAutomationService().generate_workflow(

        "Routine observation"

    )

    assert workflow.steps[0] == "Review condition"



def test_model():

    workflow = WorkflowAutomationService().generate_workflow(

        "Condition"

    )

    assert isinstance(workflow.steps, list)
