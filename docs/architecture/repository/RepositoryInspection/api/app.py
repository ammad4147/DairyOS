from fastapi import FastAPI

from dairyos.api.routers.health import router as health_router
from dairyos.api.routers.version import router as version_router
from dairyos.api.routers.readiness import router as readiness_router
from dairyos.api.routers.operations import router as operations_router
from dairyos.api.routers.dashboard import router as dashboard_router
from dairyos.api.routers.commands import router as commands_router
from dairyos.api.routers.command_center import router as command_center_router
from dairyos.api.routers.executive import router as executive_router


app = FastAPI(
    title="DairyOS Enterprise API",
    version="0.10.0",
    description="Enterprise Dairy Operating System",
)


@app.get("/")
def root():

    return {
        "system": "DairyOS",
        "status": "ONLINE",
        "version": "0.10.0",
    }


app.include_router(
    health_router
)

app.include_router(
    readiness_router
)

app.include_router(
    version_router
)

app.include_router(
    operations_router
)

app.include_router(
    dashboard_router
)

app.include_router(
    commands_router
)

app.include_router(
    command_center_router
)


app.include_router(
    executive_router
)
