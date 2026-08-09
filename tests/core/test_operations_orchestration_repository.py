from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)

from dairyos.intelligence.operations.orchestration.models.action_assignment import (
    ActionAssignment,
)

from dairyos.intelligence.operations.orchestration.models.execution_record import (
    ExecutionRecord,
)

from dairyos.intelligence.operations.orchestration.models.action_outcome import (
    ActionOutcome,
)

from dairyos.intelligence.operations.orchestration.repository.adapters.memory_action_repository import (
    MemoryActionRepository,
)

from dairyos.intelligence.operations.orchestration.repository.adapters.memory_assignment_repository import (
    MemoryAssignmentRepository,
)

from dairyos.intelligence.operations.orchestration.repository.adapters.memory_execution_repository import (
    MemoryExecutionRepository,
)

from dairyos.intelligence.operations.orchestration.repository.adapters.memory_outcome_repository import (
    MemoryOutcomeRepository,
)



def test_memory_action_repository():

    repository = MemoryActionRepository()

    action = OperationalAction(
        action_type="feeding_adjustment",
        description="Increase ration",
        priority="high",
        status="created",
        source_decision="herd_intelligence",
    )

    repository.save(action)

    assert len(repository.get_all()) == 1
    assert repository.get_all()[0].action_type == "feeding_adjustment"



def test_memory_assignment_repository():

    repository = MemoryAssignmentRepository()

    assignment = ActionAssignment(
        action_type="feeding_adjustment",
        assigned_to="farm_manager",
        assigned_role="operations",
        status="assigned",
    )

    repository.save(assignment)

    assert len(repository.get_all()) == 1
    assert repository.get_all()[0].assigned_to == "farm_manager"



def test_memory_execution_repository():

    repository = MemoryExecutionRepository()

    record = ExecutionRecord(
        action_type="feeding_adjustment",
        performed_by="farm_manager",
        execution_status="completed",
        notes="Done",
    )

    repository.save(record)

    assert len(repository.get_all()) == 1
    assert repository.get_all()[0].execution_status == "completed"



def test_memory_outcome_repository():

    repository = MemoryOutcomeRepository()

    outcome = ActionOutcome(
        action_type="feeding_adjustment",
        result="Improved intake",
        success=True,
        feedback="Positive",
    )

    repository.save(outcome)

    assert len(repository.get_all()) == 1
    assert repository.get_all()[0].success is True
