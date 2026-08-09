from fastapi import APIRouter, Depends

from dairyos.api.dependencies import get_container


router = APIRouter(
    tags=["System"]
)



@router.get("/readiness")
def readiness(
    container = Depends(get_container),
):

    return {

        "system":
            "DairyOS",

        "status":
            "READY",

        "database":
            "READY",

        "runtime":
            "ACTIVE",

        "events":
            container.event_journal.count(),

    }



@router.get("/version")
def version():

    return {

        "system":
            "DairyOS",

        "version":
            "0.10.0",

        "api":
            "Enterprise API",

        "status":
            "stable",

    }
