"""Read-only management Reporting API.

Workflow served: Reporting Area -> Report -> Parameters -> Generate ->
Analyse -> Export / Print. The catalogue, every report and every export are
produced by ``dairyos.reporting``; this module only adapts HTTP.

Mounted at ``/farm/reports``. The previous ``/farm/reporting`` API stays
mounted until the Reporting screen is switched over, so the running
application is never left with a broken Reporting tab.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from dairyos.api.dependencies import get_container
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
from dairyos.reporting import export as exporters
from dairyos.reporting.context import ReportParameterError
from dairyos.reporting.engine import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, ReportRequest, run_report
from dairyos.reporting.periods import PERIOD_MODE_LABELS, PERIOD_MODES, QUARTER_LABELS
from dairyos.reporting.registry import catalog, get_report

router = APIRouter(prefix="/farm/reports", tags=["Reports"])

ExportFormat = Literal["PDF", "XLSX", "CSV"]
_MEDIA = {
    "PDF": ("application/pdf", "pdf"),
    "XLSX": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
    "CSV": ("text/csv; charset=utf-8", "csv"),
}


class ReportingRunRequest(BaseModel):
    report_id: str = Field(min_length=1, max_length=80)
    period: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    columns: list[str] | None = None
    sort_key: str | None = None
    sort_dir: Literal["asc", "desc"] = "asc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)

    @field_validator("report_id")
    @classmethod
    def _normalise_report_id(cls, value: str) -> str:
        return value.strip().lower()


def report_permission_for_request(report_id: str | None) -> str | None:
    """Permission required to run one report (consumed by ``authorization``)."""
    definition = get_report(report_id)
    return definition.permission if definition is not None else "settings.view"


def _definition_or_404(report_id: str):
    definition = get_report(report_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="This report is not in the DairyOS report catalogue.")
    return definition


def _execute(payload: ReportingRunRequest, container: Any, *, all_rows: bool) -> dict[str, Any]:
    definition = _definition_or_404(payload.report_id)
    request = ReportRequest(
        report_id=definition.id, period=payload.period, filters=dict(payload.filters), columns=payload.columns,
        sort_key=payload.sort_key, sort_dir=payload.sort_dir, page=payload.page, page_size=payload.page_size,
        all_rows=all_rows,
    )
    try:
        return run_report(definition, request, container)
    except ReportParameterError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _distinct(container: Any, attribute: str) -> list[str]:
    from dairyos.data.models.animal import Animal

    session = container.repository_factory.session
    column = getattr(Animal, attribute)
    values = session.query(column).filter(column.isnot(None)).distinct().all()
    return sorted({str(value).strip() for (value,) in values if str(value or "").strip()}, key=str.lower)


def _option_sources(container: Any) -> dict[str, list[dict[str, str]]]:
    from dairyos.api.reference_data import GOVERNED

    def options(values):
        return [{"value": value, "label": value} for value in values]

    severities = [str(v) for v in GOVERNED.get("health_severities", [])]
    return {
        "breeds": options(_distinct(container, "breed")),
        "production_groups": options(_distinct(container, "production_group")),
        "locations": options(_distinct(container, "location")),
        "health_severities": [{"value": v, "label": v.replace("_", " ").title()} for v in severities],
    }


@router.get("/catalog")
def reporting_catalog(container=Depends(get_container)):
    today = OperationalDateAuthority(repository_factory=container.repository_factory).current_date()
    return {
        "read_only": True,
        "operational_today": today.isoformat(),
        "currency": "PKR",
        "period_modes": [{"value": mode, "label": PERIOD_MODE_LABELS[mode]} for mode in PERIOD_MODES],
        "quarters": [{"value": number, "label": label} for number, label in QUARTER_LABELS.items()],
        "option_sources": _option_sources(container),
        "export_formats": list(_MEDIA),
        **catalog(),
    }


@router.post("/run")
def reporting_run(payload: ReportingRunRequest, container=Depends(get_container)):
    return _execute(payload, container, all_rows=False)


@router.post("/export")
def reporting_export(payload: ReportingRunRequest, format: ExportFormat, container=Depends(get_container)):
    result = _execute(payload, container, all_rows=True)
    farm_name = FarmSettingsService(container.repository_factory.app_settings()).get_farm_name() or "DairyOS"
    if format == "CSV":
        content = exporters.csv_bytes(result, farm_name)
    elif format == "XLSX":
        content = exporters.xlsx_bytes(result, farm_name)
    else:
        content = exporters.pdf_bytes(result, farm_name)
    media_type, extension = _MEDIA[format]
    primary = next((s for s in result["sections"] if s["primary"]), None)
    headers = {
        "Content-Disposition": f'attachment; filename="{exporters.file_stem(result)}.{extension}"',
        "X-DairyOS-Report-Id": result["report"]["id"],
        "X-DairyOS-Record-Count": str(primary["row_count"] if primary else 0),
        "X-DairyOS-Column-Count": str(len(primary["columns"]) if primary else 0),
        "Access-Control-Expose-Headers": "Content-Disposition, X-DairyOS-Report-Id, X-DairyOS-Record-Count, X-DairyOS-Column-Count",
    }
    return Response(content=content, media_type=media_type, headers=headers)
