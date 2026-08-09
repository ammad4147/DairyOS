from fastapi import APIRouter

from sqlalchemy import text

from dairyos.data.database.session import SessionLocal


router = APIRouter(
    tags=["System"],
)


@router.get("/readiness")
def readiness():

    database_status = "READY"

    try:

        session = SessionLocal()

        session.execute(
            text("SELECT 1")
        )

        session.close()

    except Exception:

        database_status = "UNAVAILABLE"


    if database_status == "READY":

        status = "READY"

    else:

        status = "NOT_READY"


    return {
        "system": "DairyOS",
        "status": status,
        "database": database_status,
    }
