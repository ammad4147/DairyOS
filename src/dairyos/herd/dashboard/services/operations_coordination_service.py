from ..models.operations_coordination import OperationsCoordination



class OperationsCoordinationService:



    def create_task(

        self,

        task,

        assigned_to,

        priority,

        due

    ):


        return OperationsCoordination(

            task,

            assigned_to,

            priority,

            "PENDING",

            due

        )



    def complete_task(

        self,

        operation

    ):


        operation.status = "COMPLETED"

        return operation



    def is_pending(

        self,

        operation

    ):


        return operation.status == "PENDING"
