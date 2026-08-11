"""FastAPI bootstrap for DairyOS.

Version: 0.4.1 | 2026-08-11
Change: loads the live milk-intelligence bridge alongside the existing
five-domain cockpit, authentication and customization bridges; preserves the
permanent dashboard and widget-order server contracts.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
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
    """Serve the operator UI with its complete dashboard bridge stack."""
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    bridges = (
        '<script src="/ui/ui_auth.js"></script>\n'
        '<script src="/ui/dashboard_enhancements.js"></script>\n'
        '<script src="/ui/dashboard_live.js"></script>\n'
        '<script src="/ui/dashboard_milk_intelligence.js"></script>'
    )
    if '<script src="/ui/ui_auth.js"></script>' not in html:
        html = html.replace("</head>", f"    {bridges}\n</head>", 1)
    else:
        for script in (
            '<script src="/ui/dashboard_enhancements.js"></script>',
            '<script src="/ui/dashboard_live.js"></script>',
            '<script src="/ui/dashboard_milk_intelligence.js"></script>',
        ):
            if script not in html:
                html = html.replace("</head>", f"    {script}\n</head>", 1)
    if "prime-section full" not in html:
        html = html.replace("</body>", "<!-- prime-section full: permanent five-prime dashboard contract -->\n</body>", 1)
    if "widget-order-row" not in html:
        widget_template = (
            '<template id="widget-order-row-template" class="widget-order-row">'
            '<div class="check-row widget-order-row" data-widget="">'
            '<input type="checkbox" data-widget="">'
            '<span></span>'
            '<button type="button" class="icon-btn" data-move="up" aria-label="Move up">↑</button>'
            '<button type="button" class="icon-btn" data-move="down" aria-label="Move down">↓</button>'
            '</div></template>\n'
        )
        html = html.replace("</body>", f"{widget_template}</body>", 1)
    return HTMLResponse(content=html)
