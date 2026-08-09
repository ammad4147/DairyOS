from typing import List, Optional

from dairyos.operations.models.daily_operation import DailyOperation


class DailyOperationsService:
    """
    Service layer for daily farm operations management.

    Foundation service for:
    - Daily Operations Board
    - Farm Command Center
    - Future workflow automation
    """

    def __init__(self):
        self._operations: List[DailyOperation] = []

    def add_operation(
        self,
        operation: DailyOperation,
    ) -> DailyOperation:
        """
        Register a new daily farm operation.
        """

        self._operations.append(operation)

        return operation

    def get_operations(self) -> List[DailyOperation]:
        """
        Return all registered operations.
        """

        return self._operations

    def get_operation(
        self,
        operation_id: str,
    ) -> Optional[DailyOperation]:
        """
        Find operation by ID.
        """

        for operation in self._operations:
            if operation.operation_id == operation_id:
                return operation

        return None

    def complete_operation(
        self,
        operation_id: str,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Complete an operational task.
        """

        operation = self.get_operation(operation_id)

        if operation is None:
            return False

        operation.complete(notes)

        return True
