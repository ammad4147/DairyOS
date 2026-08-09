from ..models.staff_task import StaffTask



class StaffTaskManagementService:



    def evaluate(

        self,

        task_id,

        task_name,

        assigned_team,

        urgency

    ):


        if urgency.lower() == "high":

            priority = "HIGH"

            status = "PENDING"

            action = "Complete immediately"



        elif urgency.lower() == "medium":

            priority = "MEDIUM"

            status = "SCHEDULED"

            action = "Complete according to schedule"



        else:

            priority = "NORMAL"

            status = "PLANNED"

            action = "Continue routine monitoring"



        return StaffTask(

            task_id,

            task_name,

            assigned_team,

            priority,

            status,

            action

        )
