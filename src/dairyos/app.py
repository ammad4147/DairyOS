from dairyos.middleware.enum_normalizer import PayloadNormalizationMiddleware
"""FastAPI application bootstrap for DairyOS."""
from contextlib import asynccontextmanager
from datetime import date
import json
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dairyos.application.application_runtime import ApplicationRuntime
from dairyos.runtime.container import RuntimeContainer
from dairyos.data.database.migrations import (
    migrate_finance_feed_opex,
    migrate_feed_inventory,
    migrate_milk_quality,
    migrate_coml,
    migrate_operational_finding_audit,
    migrate_payroll,
)
from dairyos.farm.production.services.milk_cycle_monitoring_service import MilkCycleMonitoringService
from dairyos.farm.production.services.milk_herd_drop_monitoring_service import MilkHerdDailyDropMonitoringService
from dairyos.farm.production.services.milk_reconciliation_service import MilkReconciliationService
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
from dairyos.email.scheduler import NightlyEmailScheduler
from dairyos.feed_storage_scheduler import FeedStorageScheduler
from dairyos.missed_milking_scheduler import DailyMissedMilkingScheduler
from dairyos.frontend import frontend_index_response, mount_frontend
from dairyos.windows.startup_integrity import record_successful_start

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
application_runtime = ApplicationRuntime()
container = RuntimeContainer(application_runtime=application_runtime)
email_scheduler = NightlyEmailScheduler(container=container)
feed_storage_scheduler = FeedStorageScheduler(interval_seconds=60)
missed_milking_scheduler = DailyMissedMilkingScheduler(interval_seconds=30)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    migrated = migrate_finance_feed_opex()
    inventory_migrated = migrate_feed_inventory()
    quality_migrated = migrate_milk_quality()
    coml_migrated = migrate_coml()
    finding_audit_migrated = migrate_operational_finding_audit()
    payroll_migrated = migrate_payroll()
    if migrated:
        logging.info("Finance Feed/OPEX migration added columns: %s", ", ".join(migrated))
    if inventory_migrated:
        logging.info("Feed inventory migration created/updated: %s", ", ".join(inventory_migrated))
    if quality_migrated:
        logging.info("Milk quality migration created: %s", ", ".join(quality_migrated))
    if coml_migrated:
        logging.info("COML migration created: %s", ", ".join(coml_migrated))
    if finding_audit_migrated:
        logging.info("Operational finding audit migration added columns: %s", ", ".join(finding_audit_migrated))
    if payroll_migrated:
        logging.info("Finance payroll migration created: %s", ", ".join(payroll_migrated))
    container.start()
    feed_storage_scheduler.start()
    missed_milking_scheduler.start()
    email_scheduler.start()
    marker = record_successful_start()
    if marker is not None:
        logging.info("DairyOS successful packaged installation marker written: %s", marker)
    logging.info("RuntimeContainer and operational schedulers started - operations ready.")
    try:
        yield
    finally:
        feed_storage_scheduler.stop()
        missed_milking_scheduler.stop()
        email_scheduler.stop()
        container.shutdown()


app = FastAPI(title="DairyOS API", lifespan=lifespan)
app.add_middleware(PayloadNormalizationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):517[3-9]",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"] ,
)

ANIMAL_LINKED_POSTS = {"/farm/milk", "/farm/health-observations", "/farm/treatments", "/farm/breeding", "/farm/feed/records", "/farm/welfare/observations"}


@app.middleware("http")
async def enforce_animal_identity(request: Request, call_next):
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
            factory = container.repository_factory
            exists = factory.animal().exists(str(animal_id))
            if not exists:
                return JSONResponse(status_code=422, content={"detail": "Unknown Animal ID. Select an existing system-generated permanent Animal ID.", "animal_id": animal_id})
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive

    response = await call_next(request)

    if response.status_code < 300 and request.method == "POST" and request.url.path == "/farm/milk" and payload.get("animal_id") and payload.get("milking_session"):
        try:
            raw_date = payload.get("production_date")
            operational_date = date.fromisoformat(str(raw_date)[:10]) if raw_date else OperationalDateAuthority().current_date()
            MilkCycleMonitoringService().monitor(animal_id=str(payload["animal_id"]), milking_session=str(payload["milking_session"]), production_date=operational_date)
            MilkHerdDailyDropMonitoringService().monitor(operational_date)
            MilkReconciliationService().reconcile(operational_date)
        except Exception:
            logging.exception("Milk post-write monitoring failed after a successful milk write.")

    return response

from dairyos.api.command_center import router as command_router
from dairyos.api.dashboard import router as dashboard_router
from dairyos.api.breeding_biology import router as breeding_biology_router
from dairyos.api.equipment_management import router as equipment_router
from dairyos.api.farm_data_entry import router as farm_router
from dairyos.api.veterinary_non_milking import router as veterinary_non_milking_router
from dairyos.api.milk_production_analytics import router as milk_production_analytics_router
from dairyos.api.animal_registration import router as animal_registration_router
from dairyos.api.animal_management.router import router as animal_router
from dairyos.api.analytics import router as analytics_router
from dairyos.api.live_analytics import router as live_analytics_router
from dairyos.api.animal_passport import router as animal_passport_router
from dairyos.api.farm_intelligence import router as farm_intelligence_router
from dairyos.api.heat_stress_intelligence import router as heat_stress_intelligence_router
from dairyos.api.animal_welfare import router as animal_welfare_router
from dairyos.api.financial_intelligence import router as financial_intelligence_router
from dairyos.api.finance_ledger import router as finance_ledger_router
from dairyos.api.farm_planning import router as farm_planning_router
from dairyos.api.health import router as health_router
from dairyos.api.milk_traceability import router as milk_traceability_router
from dairyos.api.operations import router as operations_router
from dairyos.api.tab_state import router as tab_state_router
from dairyos.api.reference_data import router as reference_data_router
from dairyos.api.reproduction_management import router as reproduction_management_router
from dairyos.api.youngstock_management import router as youngstock_management_router
from dairyos.api.feed_management import router as feed_management_router
from dairyos.api.feed_inventory import router as feed_inventory_router
from dairyos.api.feed_inventory_projection import router as feed_inventory_projection_router
from dairyos.api.feed_equipment import router as feed_equipment_router
from dairyos.api.dairy_kpi import router as dairy_kpi_router
from dairyos.api.system import router as system_router
from dairyos.api.operational_findings import router as operational_findings_router
from dairyos.api.settings import router as settings_router
from dairyos.api.milk_production_summary import router as milk_production_summary_router
from dairyos.api.milk_legacy_compat import router as milk_legacy_compat_router
from dairyos.api.milk_quality import router as milk_quality_router
from dairyos.api.tmr import router as tmr_router
from dairyos.api.coml import router as coml_router
from dairyos.api.payroll import router as payroll_router
from dairyos.api.auth import router as auth_router
from dairyos.api.authorization import router as authorization_router

app.include_router(command_router)
app.include_router(dashboard_router)
# Governed breeding routes must be registered before the generic farm-data
# compatibility router and Animal Passport compatibility reproduction route.
# FastAPI resolves duplicate method/path routes in registration order, so this
# ordering makes form-governed breeding biology the live authority.
app.include_router(breeding_biology_router)
app.include_router(equipment_router)
app.include_router(farm_router)
app.include_router(veterinary_non_milking_router)
app.include_router(milk_production_analytics_router)
app.include_router(animal_registration_router)
app.include_router(animal_router, prefix="/farm")
app.include_router(animal_passport_router)
app.include_router(analytics_router)
app.include_router(live_analytics_router)
app.include_router(farm_intelligence_router)
app.include_router(heat_stress_intelligence_router)
app.include_router(animal_welfare_router)
app.include_router(financial_intelligence_router)
app.include_router(finance_ledger_router)
app.include_router(farm_planning_router)
app.include_router(health_router)
app.include_router(milk_traceability_router)
app.include_router(operations_router)
app.include_router(tab_state_router)
app.include_router(reference_data_router)
app.include_router(reproduction_management_router)
app.include_router(youngstock_management_router)
app.include_router(feed_management_router)
app.include_router(feed_inventory_router)
app.include_router(feed_inventory_projection_router)
app.include_router(feed_equipment_router)
app.include_router(dairy_kpi_router)
app.include_router(system_router)
app.include_router(operational_findings_router)
app.include_router(settings_router)
app.include_router(milk_production_summary_router)
app.include_router(milk_legacy_compat_router)
app.include_router(milk_quality_router)
app.include_router(tmr_router)
app.include_router(coml_router)
app.include_router(payroll_router)
app.include_router(auth_router)
app.include_router(authorization_router)

FRONTEND_URL = os.getenv("DAIRYOS_FRONTEND_URL", "/")


@app.get("/", include_in_schema=False)
def root(request: Request):
    frontend = frontend_index_response()
    accept = request.headers.get("accept", "")
    if frontend is not None and "text/html" in accept.lower():
        return frontend
    return JSONResponse({"system": "DairyOS", "surface": "api", "operator_ui": {"application": "DairyOS.Web", "technology": "React/Vite", "url": FRONTEND_URL, "authoritative": True}, "legacy_static_ui": {"served": False, "reason": "React/Vite operator shell is authoritative; FastAPI exposes the API/runtime surface."}})

mount_frontend(app)