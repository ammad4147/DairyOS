from dairyos.intelligence.execution.models.execution_plan import (
    ExecutionPlan,
)

from dairyos.intelligence.execution.repository.adapters.memory_execution_repository import (
    MemoryExecutionRepository,
)


def test_repository_save():

    repository = MemoryExecutionRepository()

    plan = ExecutionPlan(
        workflow_type="health",
        objective="Treatment",
        priority="high",
        status="planned",
    )

    repository.save(plan)

    assert len(repository.get_all()) == 1


def test_repository_returns_saved_execution():

    repository = MemoryExecutionRepository()

    plan = ExecutionPlan(
        workflow_type="health",
        objective="Treatment",
        priority="high",
        status="planned",
    )

    repository.save(plan)

    assert repository.get_all()[0] == plan
