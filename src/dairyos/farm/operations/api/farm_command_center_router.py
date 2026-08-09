from fastapi import APIRouter, Depends


from dairyos.farm.operations.dashboard.farm_command_center_service import (
    FarmCommandCenterService,
)


router = APIRouter(
    prefix="/farm/command-center",
    tags=[
        "Farm Command Center",
    ],
)


def get_command_center_service():
    return FarmCommandCenterService()



@router.get("")
def get_farm_command_center(
    service: FarmCommandCenterService = Depends(
        get_command_center_service
    ),
):

    """
    Farm Command Center read endpoint.

    Exposes operational awareness:

    - current farm status
    - task visibility
    - heads-up notifications
    - readiness
    - execution tracking
    - compliance intelligence

    Read-only projection.

    Does not:
        - create events
        - modify state
        - complete activities
    """


    read_model = (
        service.get_read_model()
    )


    return {

        "farm_id":
            read_model.farm_id,


        "operational_date":
            read_model.operational_date,


        "operational_status":
            read_model.operational_status,


        "milk_status":
            read_model.milk_status,


        "feeding_status":
            read_model.feeding_status,


        "health_alert_count":
            read_model.health_alert_count,


        "open_tasks":
            read_model.open_tasks,


        "completed_tasks":
            read_model.completed_tasks,


        "heads_up_notifications":
            read_model.heads_up_notifications,


        "readiness": {

            "status":
                read_model.readiness_status,

            "risks":
                read_model.readiness_risks,

        },


        "execution_tracking": {

            "status":
                read_model.execution_status,


            "total_activities":
                read_model.execution_total_activities,


            "completed_activities":
                read_model.execution_completed_activities,


            "missed_activities":
                read_model.execution_missed_activities,


            "details":
                read_model.execution_details,

        },


        "execution_history_compliance":

            read_model.execution_history_compliance,

    }
