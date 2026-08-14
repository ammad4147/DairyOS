"""FastAPI application bootstrap for DairyOS.

The operator UI is the React/Vite application under ``src/DairyOS.Web``.
FastAPI is the API/runtime surface and deliberately does not serve the retired
static operator UI. Animal-linked operational writes are checked against the
persisted Animal Register before they reach domain handlers.
"""
from contextlib import asynccontextmanager
from datetime import date
import json
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dairyos.application.application_runtime import ApplicationRuntime
from dairyos.runtime.container import RuntimeContainer
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.production.services.milk_cycle_monitoring_service import MilkCycleMonitoringService
from dairyos.farm.production.services.milk_herd_drop_monitoring_service import MilkHerdDailyDropMonitoringService
from dairyos.farm.production.services.milk_reconciliation_service import MilkReconciliationService

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
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):517[3-9]",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ANIMAL_LINKED_POSTS = {"/farm/milk", "/farm/health-observations", "/farm/treatments", "/farm/breeding", "/farm/feed/records", "/farm/welfare/observations"}


@app.middleware("http")
async def enforce_animal_identity(request, call_next):
    body = None
    payload = {}
    if request.method == "POST" and request.url.path in ANIMAL_LINKED_POSTS:
        body = await request.body()
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = {}
        animal_id = payload.get("animal_id")
        if animal_id:
            factory = RepositoryFactory.create()
            try:
                exists = factory.animal().exists(str(animal_id))
            finally:
                factory.close()
            if not exists:
                return JSONResponse(status_code=422, content={"detail": "Unknown Animal ID. Select an existing system-generated permanent Animal ID.", "animal_id": animal_id})
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive

    response = await call_next(request)

    # Derived monitoring never blocks the persisted milk fact. The write has
    # already succeeded; these observers only raise traceable findings.
    if (
        response.status_code < 300
        and request.method == "POST"
        and request.url.path == "/farm/milk"
        and payload.get("animal_id")
        and payload.get("milking_session")
    ):
        try:
            raw_date = payload.get("production_date")
            operational_date = date.fromisoformat(str(raw_date)[:10]) if raw_date else date.today()
            MilkCycleMonitoringService().monitor(
                animal_id=str(payload["animal_id"]),
                milking_session=str(payload["milking_session"]),
                production_date=operational_date,
            )
            MilkHerdDailyDropMonitoringService().monitor(operational_date)
            MilkReconciliationService().reconcile(operational_date)
        except Exception:
            logging.exception("Milk post-write monitoring failed after a successful milk write.")

    return response


from dairyos.api.auth import router as auth_router
from dairyos.api.command_center import router as command_router
from dairyos.api.dashboard import router as dashboard_router
from dairyos.api.farm_data_entry import router as farm_router
from dairyos.api.milk_production_analytics import router as milk_production_analytics_router
from dairyos.api.animal_registration import router as animal_registration_router
from dairyos.api.animal_management.router import router as animal_router
from dairyos.api.animal_passport import router as animal_passport_router
from dairyos.api.farm_intelligence import router as farm_intelligence_router
from dairyos.api.heat_stress_intelligence import router as heat_stress_intelligence_router
from dairyos.api.animal_welfare import router as animal_welfare_router
from dairyos.api.financial_intelligence import router as financial_intelligence_router
from dairyos.api.farm_planning import router as farm_planning_router
from dairyos.api.health import router as health_router
from dairyos.api.milk_traceability import router as milk_traceability_router
from dairyos.api.operations import router as operations_router
from dairyos.api.tab_state import router as tab_state_router
from dairyos.api.reference_data import router as reference_data_router
from dairyos.api.reproduction_management import router as reproduction_management_router
from dairyos.api.youngstock_management import router as youngstock_management_router
from dairyos.api.feed_management import router as feed_management_router
from dairyos.api.dairy_kpi import router as dairy_kpi_router
from dairyos.api.system import router as system_router
from dairyos.api.operational_findings import router as operational_findings_router
from dairyos.api.settings import router as settings_router

app.include_router(auth_router)
app.include_router(command_router)
app.include_router(dashboard_router)
app.include_router(farm_router)
app.include_router(milk_production_analytics_router)
app.include_router(animal_registration_router)
app.include_router(animal_router, prefix="/farm")
app.include_router(animal_passport_router)
app.include_router(farm_intelligence_router)
app.include_router(heat_stress_intelligence_router)
app.include_router(animal_welfare_router)
app.include_router(financial_intelligence_router)
app.include_router(farm_planning_router)
app.include_router(health_router)
app.include_router(milk_traceability_router)
app.include_router(operations_router)
app.include_router(tab_state_router)
app.include_router(reference_data_router)
app.include_router(reproduction_management_router)
app.include_router(youngstock_management_router)
app.include_router(feed_management_router)
app.include_router(dairy_kpi_router)
app.include_router(system_router)
app.include_router(operational_findings_router)
app.include_router(settings_router)

FRONTEND_URL = os.getenv("DAIRYOS_FRONTEND_URL", "http://localhost:5173/")


@app.get("/", include_in_schema=False)
def root():
    return JSONResponse({"system": "DairyOS", "surface": "api", "operator_ui": {"application": "DairyOS.Web", "technology": "React/Vite", "url": FRONTEND_URL, "authoritative": True}, "legacy_static_ui": {"served": False, "reason": "Retired; the React/Vite operator shell is authoritative."}})
