from dairyos.operations.accountability_integration.services.accountability_bridge import (
    AccountabilityBridge,
)


class OperationalAssignmentAccountabilityService:
    """
    Converts operational assignments
    into execution accountability records.
    """


    def __init__(
        self,
        assignment_service,
        accountability_bridge,
    ):

        self.assignment_service = (
            assignment_service
        )

        self.accountability_bridge = (
            accountability_bridge
        )



    def assign_and_track(
        self,
        user_id: str,
        action_id: str,
        execution,
        task_name: str,
    ):

        assignment = (
            self.assignment_service.assign_action(
                user_id=user_id,
                action_id=action_id,
            )
        )


        accountability = (
            self.accountability_bridge
            .create_accountability_record(
                execution=execution,
                task_name=task_name,
            )
        )


        return {

            "assignment": assignment,

            "accountability": accountability,

        }



    def get_accountability_records(
        self,
    ):

        return (
            self.accountability_bridge
            .get_records()
        )
