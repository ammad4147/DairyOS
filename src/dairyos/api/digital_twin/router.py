from fastapi import APIRouter


router = APIRouter()



@router.get(
    "/digital-twin/state"
)
def digital_twin_state():

    return {

        "farm_id": "farm001",

        "status": "operational",

        "state": {

            "animals": 0,

            "milk_today": 0,

            "feed_today": 0

        }

    }



@router.post(
    "/digital-twin/simulate"
)
def simulate(payload: dict):


    return {

        "farm_id":
            payload.get(
                "farm_id",
                "farm001"
            ),


        "metric":
            payload.get(
                "metric"
            ),


        "current_value":
            payload.get(
                "current_value",
                0
            ),


        "change":
            payload.get(
                "change_percent",
                0
            )

    }
