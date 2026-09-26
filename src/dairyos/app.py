from dairyos.middleware.enum_normalizer import PayloadNormalizationMiddleware

"""FastAPI application bootstrap for DairyOS."""
import json
import logging
import os
import re
from contextlib import asynccontextmanager
from datetime import date
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dairyos.application.application_runtime import ApplicationRuntime
from dairyos.email.scheduler import NightlyEmailScheduler
from dairyos.farm.production.services.milk_cycle_monitoring_service import (
    MilkCycleMonitoringService,
)
from dairyos.farm.production.services.milk_herd_drop_monitoring_service import (
    MilkHerdDailyDropMonitoringService,
)
from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from dairyos.feed_storage_scheduler import FeedStorageScheduler
from dairyos.frontend import frontend_index_response, mount_frontend
from dairyos.missed_milking_scheduler import DailyMissedMilkingScheduler
from dairyos.platform.runtime_mode import RuntimeMode, resolve_runtime_mode
from dairyos.platform.runtime_startup import record_successful_start
from dairyos.runtime.container import RuntimeContainer
from dairyos.tmr_daily_cost_scheduler import DailyTMRCostScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
application_runtime = ApplicationRuntime()
container = RuntimeContainer(application_runtime=application_runtime)
email_scheduler = NightlyEmailScheduler(container=container)
feed_storage_scheduler = FeedStorageScheduler(interval_seconds=60)
missed_milking_scheduler = DailyMissedMilkingScheduler(interval_seconds=30)
tmr_daily_cost_scheduler = DailyTMRCostScheduler(interval_seconds=30)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Database schema is prepared before backend startup by the governed
    # Windows migration gate / Alembic lifecycle. Normal application
    # startup must never create, alter, or repair database schema.
    container.start()
    feed_storage_scheduler.start()
    missed_milking_scheduler.start()
    tmr_daily_cost_scheduler.start()
    email_scheduler.start()
    marker = record_successful_start(resolve_runtime_mode())
    if marker is not None:
        logging.info("DairyOS successful packaged installation marker written: %s", marker)
    logging.info("RuntimeContainer and operational schedulers started - operations ready.")
    try:
        yield
    finally:
        feed_storage_scheduler.stop()
        tmr_daily_cost_scheduler.stop()
        missed_milking_scheduler.stop()
        email_scheduler.stop()
        container.shutdown()


app = FastAPI(title="DairyOS API", lifespan=lifespan)

from dairyos.core.inventory_units import InventoryIntegrityError


@app.exception_handler(InventoryIntegrityError)
async def inventory_integrity_error(request: Request, exc: InventoryIntegrityError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

app.add_middleware(PayloadNormalizationMiddleware)


def _cors_configuration(mode: RuntimeMode, raw_origins: str) -> tuple[list[str], str | None]:
    origins: list[str] = []
    for candidate in (origin.strip() for origin in raw_origins.split(",")):
        if not candidate:
            continue
        parsed = urlsplit(candidate)
        allowed_schemes = {"https"}
        if mode in {RuntimeMode.DEVELOPMENT, RuntimeMode.BROWSER_CLIENT}:
            allowed_schemes.add("http")
        if (
            candidate == "*"
            or parsed.scheme not in allowed_schemes
            or not parsed.netloc
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError(
                "DAIRYOS_ALLOWED_ORIGINS must contain exact origins; hosted origins must use HTTPS"
            )
        try:
            hostname = parsed.hostname
            port = parsed.port
        except ValueError as exc:
            raise ValueError("DAIRYOS_ALLOWED_ORIGINS contains an invalid port") from exc
        if not hostname:
            raise ValueError("DAIRYOS_ALLOWED_ORIGINS must contain a hostname")
        if parsed.scheme == "http" and hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("HTTP CORS origins are allowed only on loopback in development")
        normalized_host = f"[{hostname.lower()}]" if ":" in hostname else hostname.lower()
        origin = f"{parsed.scheme}://{normalized_host}"
        if port is not None:
            origin += f":{port}"
        if origin not in origins:
            origins.append(origin)
    development_origin_regex = (
        r"https?://(localhost|127\.0\.0\.1):517[3-9]"
        if mode in {RuntimeMode.DEVELOPMENT, RuntimeMode.BROWSER_CLIENT}
        else None
    )
    return origins, development_origin_regex


_configured_origins, _configured_origin_regex = _cors_configuration(
    resolve_runtime_mode(), os.getenv("DAIRYOS_ALLOWED_ORIGINS", "")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_configured_origins,
    allow_origin_regex=_configured_origin_regex,
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

from dairyos.api.authorization import permission_for_request
from dairyos.api.human_access import _current_session
from dairyos.auth.permissions import permissions_for_role
from dairyos.middleware.desktop_session import enforce_desktop_session

_HUMAN_ACCESS_PUBLIC_EXACT = {
    ("GET", "/"),
    ("GET", "/index.html"),
    ("GET", "/health"),
    ("GET", "/readiness"),
    ("GET", "/version"),
    ("GET", "/favicon.ico"),
    ("GET", "/manifest.json"),
    ("GET", "/dairyos-cow.svg"),
    ("GET", "/serviceWorker.js"),
    ("HEAD", "/"),
    ("HEAD", "/index.html"),
    ("HEAD", "/health"),
    ("HEAD", "/readiness"),
    ("HEAD", "/version"),
    ("HEAD", "/favicon.ico"),
    ("HEAD", "/manifest.json"),
    ("HEAD", "/dairyos-cow.svg"),
    ("HEAD", "/serviceWorker.js"),
    ("GET", "/human-access/status"),
    ("GET", "/human-access/people"),
    ("POST", "/human-access/help"),
    ("POST", "/human-access/bootstrap"),
    ("POST", "/human-access/login"),
    ("POST", "/auth/login"),
    ("POST", "/login"),
}


def _is_public_human_access_request(method: str, path: str) -> bool:
    """Explicitly identify resources needed before a human session exists."""
    method = method.upper()
    if (method, path) in _HUMAN_ACCESS_PUBLIC_EXACT:
        return True
    if method in {"GET", "HEAD"} and path.startswith("/assets/"):
        return True
    return False


@app.middleware("http")
async def enforce_human_access(request: Request, call_next):
    """Require a named human session for every non-public production route."""
    production = (
        bool(getattr(__import__('sys'), "frozen", False))
        or resolve_runtime_mode() is RuntimeMode.HOSTED
        or os.getenv("DAIRYOS_ENV", "development").lower() != "development"
    )
    path = request.url.path
    if production and not _is_public_human_access_request(request.method, path):
        token = request.headers.get("X-DairyOS-Human-Session")
        try:
            _, identity = _current_session(token)
            required = permission_for_request(request.method, request.url.path)
            if required and required not in permissions_for_role(identity.role):
                return JSONResponse({"detail": f"Permission required: {required}"}, status_code=403)
        except Exception as exc:
            from fastapi import HTTPException
            if isinstance(exc, HTTPException):
                return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
            return JSONResponse({"detail": "Human authentication required."}, status_code=401)
    return await call_next(request)

# Register after identity middleware so authentication runs before any farm reads.
app.middleware("http")(enforce_desktop_session)

from dairyos.api.analytics import router as analytics_router
from dairyos.api.animal_management.router import router as animal_router
from dairyos.api.animal_passport import router as animal_passport_router
from dairyos.api.animal_registration import router as animal_registration_router
from dairyos.api.animal_welfare import router as animal_welfare_router
from dairyos.api.auth import router as auth_router
from dairyos.api.authorization import router as authorization_router
from dairyos.api.breeding_biology import router as breeding_biology_router
from dairyos.api.clinical_inventory import router as clinical_inventory_router
from dairyos.api.coml import router as coml_router
from dairyos.api.command_center import router as command_router
from dairyos.api.dairy_kpi import router as dairy_kpi_router
from dairyos.api.dashboard import router as dashboard_router
from dairyos.api.equipment_management import router as equipment_router
from dairyos.api.farm_data_entry import router as farm_router
from dairyos.api.farm_intelligence import router as farm_intelligence_router
from dairyos.api.farm_planning import router as farm_planning_router
from dairyos.api.feed_equipment import router as feed_equipment_router
from dairyos.api.feed_inventory import router as feed_inventory_router
from dairyos.api.feed_inventory_projection import (
    router as feed_inventory_projection_router,
)
from dairyos.api.feed_management import router as feed_management_router
from dairyos.api.finance_ledger import router as finance_ledger_router
from dairyos.api.financial_intelligence import router as financial_intelligence_router
from dairyos.api.health import router as health_router
from dairyos.api.heat_stress_intelligence import (
    router as heat_stress_intelligence_router,
)
from dairyos.api.human_access import router as human_access_router
from dairyos.api.live_analytics import router as live_analytics_router
from dairyos.api.milk_legacy_compat import router as milk_legacy_compat_router
from dairyos.api.milk_production_analytics import (
    router as milk_production_analytics_router,
)
from dairyos.api.milk_production_summary import router as milk_production_summary_router
from dairyos.api.milk_quality import router as milk_quality_router
from dairyos.api.milk_traceability import router as milk_traceability_router
from dairyos.api.operational_findings import router as operational_findings_router
from dairyos.api.operations import router as operations_router
from dairyos.api.payroll import router as payroll_router
from dairyos.api.reference_data import router as reference_data_router
from dairyos.api.reports import router as reports_router
from dairyos.api.reproduction_management import router as reproduction_management_router
from dairyos.api.settings import router as settings_router
from dairyos.api.system import router as system_router
from dairyos.api.tab_state import router as tab_state_router
from dairyos.api.tmr import router as tmr_router
from dairyos.api.veterinary_non_milking import router as veterinary_non_milking_router
from dairyos.api.youngstock_management import router as youngstock_management_router


def _unmount_duplicate_routes(router, paths: set[str]) -> None:
    """Keep compatibility functions importable without mounting duplicate APIs."""
    router.routes[:] = [
        route
        for route in router.routes
        if str(getattr(route, "path", "")) not in paths
    ]


# Keep one public handler for each duplicated method/path. These source
# functions remain importable for internal compatibility, but mounting them
# alongside another router made runtime dispatch and OpenAPI select different
# handlers. The milk disposition duplicate also allowed a client-supplied
# recorded_by value to become durable instead of using the authenticated user.
_unmount_duplicate_routes(
    farm_router,
    {"/farm/breeding", "/farm/equipment"},
)
_unmount_duplicate_routes(
    animal_passport_router,
    {"/farm/animals/{animal_id}/reproduction"},
)
_unmount_duplicate_routes(
    farm_intelligence_router,
    {"/farm/animals/{animal_id}/passport"},
)
_unmount_duplicate_routes(
    farm_planning_router,
    {"/farm/animals/{animal_id}/reproduction"},
)
_unmount_duplicate_routes(breeding_biology_router, {"/dashboard"})
_unmount_duplicate_routes(dairy_kpi_router, {"/farm/kpis"})
_unmount_duplicate_routes(milk_legacy_compat_router, {"/farm/milk/capacity"})
_unmount_duplicate_routes(
    milk_production_analytics_router,
    {"/farm/milk/dispositions"},
)

app.include_router(command_router)
app.include_router(clinical_inventory_router)
app.include_router(dashboard_router)
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
app.include_router(human_access_router)
app.include_router(authorization_router)
app.include_router(reports_router)

FRONTEND_URL = os.getenv("DAIRYOS_FRONTEND_URL", "/")


@app.get("/", include_in_schema=False)
def root(request: Request):
    frontend = frontend_index_response()
    accept = request.headers.get("accept", "")
    if frontend is not None and "text/html" in accept.lower():
        return frontend
    return JSONResponse({"system": "DairyOS", "surface": "api", "operator_ui": {"application": "DairyOS.Web", "technology": "React/Vite", "url": FRONTEND_URL, "authoritative": True}, "legacy_static_ui": {"served": False, "reason": "React/Vite operator shell is authoritative; FastAPI exposes the API/runtime surface."}})

mount_frontend(app)
