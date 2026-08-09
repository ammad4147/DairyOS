from datetime import time


from dairyos.operations.models.work_shift import WorkShift

from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from dairyos.operations.scheduler_integration.services.schedule_execution_bridge import (
    ScheduleExecutionBridge,
)



def test_schedule_creates_execution():

    shift = WorkShift(
        shift_id="SHIFT-001",
        name="Morning Milking",
        start_time=time(5, 0),
        end_time=time(7, 0),
        assigned_role="Milking Operator",
        task_category="Milking",
    )


    action_service = OperationalActionService()

    execution_service = OperationalExecutionService()


    bridge = ScheduleExecutionBridge(
        action_service,
        execution_service,
    )


    execution = bridge.create_execution_from_shift(
        shift
    )


    assert execution.action_id == "ACT-0001"

    assert execution.assigned_to == "Milking Operator"

    assert execution.status == "CREATED"
