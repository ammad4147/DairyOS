from fastapi import APIRouter


router = APIRouter(
    tags=["System"],
)


@router.get("/version")
def version():

    return {
        "system": "DairyOS",
        "version": "0.10.0",
        "api": "Enterprise API",
    }
