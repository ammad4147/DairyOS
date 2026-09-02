from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from dairyos.api.dependencies import get_container
from dairyos.data.database.automatic_backups import read_backup_health
from dairyos.data.database.session import engine


router = APIRouter(
    tags=["System"]
)


@router.get("/readiness")
def readiness(
    container=Depends(get_container),
):
    """Report whether the runtime and database are actually ready.

    ``/health`` is the liveness endpoint and intentionally remains cheap.
    ``/readiness`` is the deployment/traffic gate: it must prove that the
    application runtime is started and that PostgreSQL accepts a trivial
    query before returning HTTP 200.
    """

    runtime_ready = bool(getattr(container, "started", False))
    database_ready = False
    database_error = None

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_ready = True
    except Exception as exc:  # pragma: no cover - exact driver error varies
        database_error = str(exc)

    if not runtime_ready or not database_ready:
        detail = {
            "system": "DairyOS",
            "status": "NOT_READY",
            "database": "READY" if database_ready else "NOT_READY",
            "runtime": "ACTIVE" if runtime_ready else "INACTIVE",
        }
        if database_error:
            detail["database_error"] = database_error
        raise HTTPException(status_code=503, detail=detail)

    return {
        "system": "DairyOS",
        "status": "READY",
        "database": "READY",
        "runtime": "ACTIVE",
        "events": container.event_journal.count(),
    }


@router.get("/backup-health")
def backup_health():
    """Expose the latest automatic-backup protection state to the operator UI.

    The response is deliberately read-only and contains no credentials.  It is
    backed by the durable backup-health record written by the autonomous backup
    worker, so a broken scheduler or failed backup remains visible even after an
    application restart.
    """

    health = dict(read_backup_health())
    return {
        "system": "DairyOS",
        "protection": health,
    }


@router.get("/version")
def version():
    return {
        "system": "DairyOS",
        "version": "0.10.0",
        "api": "Enterprise API",
        "status": "stable",
    }
