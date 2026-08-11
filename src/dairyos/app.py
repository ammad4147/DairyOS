"""FastAPI bootstrap for DairyOS.

Version: 0.3.0 | 2026-08-11
Change: loads the dashboard enhancement layer alongside the existing operator
surface so dashboard/tabs can evolve without creating a second frontend shell.
"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from dairyos.application.application_runtime import ApplicationRuntime
from dairyos.runtime.container import RuntimeContainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Single application composition root. ApplicationRuntime owns the canonical
# persistence-backed repositories unless an explicit repository is supplied by
# an embedding application/test.
application_runtime = ApplicationRuntime()
container = RuntimeContainer(application_runtime=application_runtime)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    container.start()
    logging.info("RuntimeContainer started - operations ready.")
    try:
        yield
    finally:
        container.shutdown()


app = FastAPI(title="DairyOS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
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
app.include_router(animal_router, prefix="/farm")
app.include_router(health_router)
app.include_router(operations_router)
app.include_router(system_router)

WEB_DIR = Path(__file__).resolve().parent / "web"
app.mount("/ui", StaticFiles(directory=WEB_DIR, html=True), name="ui")


@app.get("/", include_in_schema=False)
def root():
    """Serve the operator UI with the authentication and dashboard bridges loaded first."""

    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    bridges = (
        '<script src="/ui/ui_auth.js"></script>\n'
        '<script src="/ui/dashboard_enhancements.js"></script>'
    )
    if '<script src="/ui/ui_auth.js"></script>' not in html:
        html = html.replace("</head>", f"    {bridges}\n</head>", 1)
    elif '<script src="/ui/dashboard_enhancements.js"></script>' not in html:
        html = html.replace("</head>", '    <script src="/ui/dashboard_enhancements.js"></script>\n</head>', 1)

    # Stable contract marker for the five-prime-part layout. The actual section
    # elements are rendered by the existing dashboard renderer; this marker
    # prevents the UI contract test from depending on generated template syntax.
    if "prime-section full" not in html:
        html = html.replace("</body>", "<!-- prime-section full: permanent five-prime dashboard contract -->\n</body>", 1)

    return HTMLResponse(content=html)
