from dairyos.operations.models.daily_operation import DailyOperation
from dairyos.operations.staff.services.staff_task_management_service import (
    StaffTaskManagementService,
)


class OperationsTaskBridge:
    """
    Bridge between DailyOperation and StaffTask.

    Converts operational work into staff tasks while keeping
    both domains independent.
    """

    def __init__(self):
        self.staff_service = StaffTaskManagementService()

    def create_staff_task(
        self,
        operation: DailyOperation,
        assigned_team: str,
        urgency: str = "medium",
    ):
        """
        Convert a DailyOperation into a StaffTask.
        """

        return self.staff_service.evaluate(
            task_id=operation.operation_id,
            task_name=operation.description,
            assigned_team=assigned_team,
            urgency=urgency,
        )