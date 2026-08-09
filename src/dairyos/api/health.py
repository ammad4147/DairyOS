from fastapi import APIRouter

router = APIRouter(
    tags=["Health"]
)


@router.get("/health")
def health():

    return {

        "system": "DairyOS",

        "status": "healthy",

        "runtime": "active",

    }
