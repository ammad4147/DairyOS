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
    """Report layered operational readiness.

    ``/health`` is the liveness endpoint and intentionally remains cheap.
    ``/readiness`` is the deployment/traffic gate proving:
      1. Application runtime is started (process health).
      2. PostgreSQL accepts a trivial query (database reachability).
      3. Schema is at the expected migration head (schema health).
      4. Desktop session token is configured when running packaged (auth readiness).
    """
    import os
    import sys

    layers: dict[str, str] = {}
    errors: dict[str, str] = {}

    # 1. Process health
    runtime_ready = bool(getattr(container, "started", False))
    layers["process"] = "ACTIVE" if runtime_ready else "INACTIVE"

    # 2. Database reachability
    database_ready = False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_ready = True
        layers["database"] = "READY"
    except Exception as exc:
        layers["database"] = "NOT_READY"
        errors["database_error"] = str(exc)

    # 3. Schema head verification
    if database_ready:
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                )
                current_heads = sorted(row[0] for row in result.fetchall())
                layers["schema"] = "VERIFIED"
                layers["schema_heads"] = ",".join(current_heads) if current_heads else "NONE"
        except Exception:
            layers["schema"] = "UNKNOWN"
    else:
        layers["schema"] = "UNAVAILABLE"

    # 4. Desktop session readiness
    is_packaged = bool(getattr(sys, "frozen", False))
    session_token = os.environ.get("DAIRYOS_DESKTOP_SESSION_TOKEN", "")
    if is_packaged:
        layers["desktop_session"] = "CONFIGURED" if session_token else "NOT_CONFIGURED"
    else:
        layers["desktop_session"] = "DEVELOPMENT"

    overall_ready = runtime_ready and database_ready
    status = "READY" if overall_ready else "NOT_READY"

    response = {
        "system": "DairyOS",
        "status": status,
        # Preserve the established readiness API while exposing the richer
        # layered diagnostics below. Existing deployment and operator clients
        # depend on these top-level fields.
        "database": "READY" if database_ready else "NOT_READY",
        "runtime": "ACTIVE" if runtime_ready else "INACTIVE",
        "layers": layers,
    }
    if errors:
        response["errors"] = errors
    if overall_ready:
        response["events"] = container.event_journal.count()

    if not overall_ready:
        raise HTTPException(status_code=503, detail=response)

    return response


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
