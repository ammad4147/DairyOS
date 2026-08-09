from fastapi import APIRouter, Depends

from dairyos.api.dependencies import get_container


router = APIRouter(
    tags=["Readiness"],
)


@router.get("/readiness")
def readiness(
    container = Depends(get_container),
):

    return {

        "system":
            "DairyOS",

        "ready":
            True,

        "runtime":
            "ACTIVE",

        "events":
            container.event_journal.count(),

    }
