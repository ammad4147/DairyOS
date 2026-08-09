"""FastAPI bootstrap for DairyOS."""

from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dairyos.application.application_runtime import ApplicationRuntime
from dairyos.runtime.container import RuntimeContainer
from dairyos.repositories.memory_milk_repository import MemoryMilkRepository


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


# ---------------------------------------------------------------------------
# Single application composition root
# ---------------------------------------------------------------------------

memory_repo = MemoryMilkRepository()

application_runtime = ApplicationRuntime(
    milk_repository=memory_repo,
)

container = RuntimeContainer(
    application_runtime=application_runtime,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Start the canonical runtime before serving requests."""

    container.start()
    logging.info("RuntimeContainer started - operations ready.")
    try:
        yield
    finally:
        container.shutdown()


app = FastAPI(
    title="DairyOS API",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from dairyos.api.auth import router as auth_router
from dairyos.api.command_center import router as command_router
from dairyos.api.dashboard import router as dashboard_router
from dairyos.api.farm_data_entry import router as farm_router
from dairyos.api.animal_management.router import router as animal_router
from dairyos.api.health import router as health_router
from dairyos.api.operations import router as operations_router
from dairyos.api.system import router as system_router


app.include_router(auth_router)
app.include_router(command_router)
app.include_router(dashboard_router)
app.include_router(farm_router)

app.include_router(
    animal_router,
    prefix="/farm",
)

app.include_router(health_router)
app.include_router(operations_router)
app.include_router(system_router)


# ---------------------------------------------------------------------------
# Real operator UI
# ---------------------------------------------------------------------------

WEB_DIR = Path(__file__).resolve().parent / "web"

app.mount(
    "/ui",
    StaticFiles(directory=WEB_DIR, html=True),
    name="ui",
)


@app.get("/", include_in_schema=False)
def root():
    """Open the real operator dashboard rather than exposing backend-only APIs."""

    return FileResponse(WEB_DIR / "index.html")
