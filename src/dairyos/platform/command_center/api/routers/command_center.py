from fastapi import APIRouter



router = APIRouter(

    prefix="/command-center",

    tags=["Command Center"],

)



@router.get("/executive")
def executive():

    return {

        "farm": "Trident Dairies",

        "health_score": 0,

        "status": "unknown",

    }



@router.get("/status")
def status():

    return {

        "departments": []

    }



@router.get("/rooms")
def rooms():

    return {

        "rooms": []

    }



@router.get("/timeline")
def timeline():

    return {

        "events": []

    }

