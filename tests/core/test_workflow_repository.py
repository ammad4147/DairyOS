from dairyos.intelligence.workflow.models.workflow import (
    Workflow,
)

from dairyos.intelligence.workflow.repository.adapters.memory_workflow_repository import (
    MemoryWorkflowRepository,
)


def test_repository_save():

    repository = MemoryWorkflowRepository()

    workflow = Workflow(
        workflow_type="feeding",
        description="Morning Feeding",
        status="pending",
        initiated_by="decision_engine",
    )

    repository.save(workflow)

    assert len(repository.get_all()) == 1


def test_repository_returns_saved_workflow():

    repository = MemoryWorkflowRepository()

    workflow = Workflow(
        workflow_type="feeding",
        description="Morning Feeding",
        status="pending",
        initiated_by="decision_engine",
    )

    repository.save(workflow)

    saved = repository.get_all()[0]

    assert saved.workflow_type == "feeding"
    assert saved.description == "Morning Feeding"
    assert saved.status == "pending"
