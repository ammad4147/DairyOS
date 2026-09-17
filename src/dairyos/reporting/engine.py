"""Report execution: validate parameters, build, project, sort, paginate."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from dairyos.reporting.context import ReportContext, ReportParameterError
from dairyos.reporting.definitions import (
    NUMERIC_TYPES,
    Column,
    ReportDefinition,
    ReportResult,
    Section,
)
from dairyos.reporting.periods import PeriodError, resolve_period

MAX_PAGE_SIZE = 500
DEFAULT_PAGE_SIZE = 100


@dataclass
class ReportRequest:
    report_id: str
    period: dict[str, Any] = field(default_factory=dict)
    filters: dict[str, Any] = field(default_factory=dict)
    columns: list[str] | None = None
    sort_key: str | None = None
    sort_dir: str = "asc"
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    #: Exports and certification read the complete row set.
    all_rows: bool = False


def json_value(value: Any) -> Any:
    """Operator-safe JSON scalar. Never leaks objects or binary content."""
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray, memoryview)):
        return None
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(json_value(item)) for item in value if item is not None)
    return str(value)


def _validated_filters(definition: ReportDefinition, raw: dict[str, Any]) -> dict[str, Any]:
    allowed = {item.key: item for item in definition.filters}
    unsupported = sorted(set(raw or {}) - set(allowed))
    if unsupported:
        raise ReportParameterError(
            "This report does not support the filter(s): " + ", ".join(unsupported) + "."
        )
    filters: dict[str, Any] = {}
    for key, spec in allowed.items():
        value = (raw or {}).get(key, spec.default)
        if spec.kind == "toggle":
            filters[key] = (
                value if isinstance(value, bool)
                else str(value or "").strip().lower() in {"1", "true", "yes", "on"}
            )
            continue
        text = str(value).strip() if value is not None else ""
        if not text:
            if spec.required:
                raise ReportParameterError(f"{spec.label} is required for this report.")
            continue
        if spec.options and text.upper() != "ALL":
            valid = {option for option, _ in spec.options}
            if text not in valid:
                raise ReportParameterError(f"Unsupported value for {spec.label}.")
        filters[key] = text
    return filters


def _sort_value(value: Any, numeric: bool):
    if value is None or value == "":
        return (1, 0 if numeric else "")
    if numeric:
        try:
            return (0, float(value))
        except (TypeError, ValueError):
            return (1, 0)
    return (0, str(value).lower())


def _project_primary(
    section: Section,
    definition: ReportDefinition,
    request: ReportRequest,
) -> tuple[Section, dict[str, Any]]:
    available = {column.key: column for column in section.columns}

    if request.columns is not None:
        selected = [str(key).strip() for key in request.columns if str(key).strip()]
        if not selected:
            raise ReportParameterError("Select at least one column.")
        if len(selected) != len(set(selected)):
            raise ReportParameterError("Selected columns must be unique.")
        unknown = [key for key in selected if key not in available]
        if unknown:
            raise ReportParameterError("Unsupported column(s): " + ", ".join(unknown) + ".")
        # Keep catalogue order so exports are stable and predictable.
        columns = tuple(c for c in section.columns if c.key in set(selected))
    else:
        columns = tuple(c for c in section.columns if c.tier == "default")

    rows = list(section.rows)
    sort_key = request.sort_key or (definition.default_sort[0] if definition.default_sort else None)
    sort_dir = request.sort_dir if request.sort_key else (
        definition.default_sort[1] if definition.default_sort else "asc"
    )
    if sort_key:
        if sort_key not in available:
            raise ReportParameterError("Unsupported sort column.")
        numeric = available[sort_key].type in NUMERIC_TYPES
        rows.sort(key=lambda row: _sort_value(row.get(sort_key), numeric))
        if str(sort_dir).lower() == "desc":
            present = [r for r in rows if r.get(sort_key) not in (None, "")]
            missing = [r for r in rows if r.get(sort_key) in (None, "")]
            rows = list(reversed(present)) + missing

    total_rows = len(rows)
    if request.all_rows:
        page, page_size, pages = 1, max(total_rows, 1), 1
    else:
        page_size = max(1, min(int(request.page_size or DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE))
        pages = max(1, -(-total_rows // page_size))
        page = max(1, min(int(request.page or 1), pages))
        rows = rows[(page - 1) * page_size: page * page_size]

    paging = {
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "total_rows": total_rows,
        "sort_key": sort_key,
        "sort_dir": str(sort_dir).lower() if sort_key else None,
    }
    projected = Section(
        id=section.id,
        title=section.title,
        columns=columns,
        rows=rows,
        totals=section.totals,
        note=section.note,
        primary=True,
        empty_message=section.empty_message,
    )
    return projected, paging


def _section_payload(section: Section, paging: dict[str, Any] | None) -> dict[str, Any]:
    keys = [column.key for column in section.columns]
    rows = []
    for row in section.rows:
        item = {key: json_value(row.get(key)) for key in keys}
        if row.get("_drill"):
            item["_drill"] = row["_drill"]
        if row.get("_emphasis"):
            item["_emphasis"] = row["_emphasis"]
        rows.append(item)
    totals = None
    if section.totals is not None:
        totals = {key: json_value(section.totals.get(key)) for key in keys}
        totals["_label"] = section.totals.get("_label", "Total")
    return {
        "id": section.id,
        "title": section.title,
        "note": section.note,
        "primary": section.primary,
        "columns": [column.as_dict() for column in section.columns],
        "rows": rows,
        "totals": totals,
        "row_count": paging["total_rows"] if paging else len(rows),
        "paging": paging,
        "empty_message": section.empty_message,
    }


def run_report(
    definition: ReportDefinition,
    request: ReportRequest,
    container: Any,
) -> dict[str, Any]:
    factory = container.repository_factory
    factory.session.expire_all()

    authority = OperationalDateAuthority(repository_factory=factory)
    today = authority.current_date()
    generated_at = authority.current_datetime()

    try:
        period = resolve_period(
            definition.period,
            request.period,
            operational_today=today,
            default_mode=definition.default_period,
        )
    except PeriodError as exc:
        raise ReportParameterError(str(exc)) from exc

    filters = _validated_filters(definition, request.filters)
    context = ReportContext(
        definition=definition,
        container=container,
        factory=factory,
        period=period,
        filters=filters,
        today=today,
        generated_at=generated_at,
    )
    result: ReportResult = definition.builder(context)

    sections = []
    for section in result.sections:
        if section.primary:
            projected, paging = _project_primary(section, definition, request)
            if projected.empty_message is None:
                projected.empty_message = definition.empty_message
            sections.append(_section_payload(projected, paging))
        else:
            sections.append(_section_payload(section, None))

    labels = {item.key: item for item in definition.filters}
    applied = []
    for key, value in filters.items():
        spec = labels[key]
        if spec.kind == "toggle":
            if value:
                applied.append({"label": spec.label, "value": "Yes"})
            continue
        display = dict(spec.options).get(value, value)
        applied.append({"label": spec.label, "value": display})

    return {
        "report": {
            "id": definition.id,
            "area": definition.area,
            "title": definition.title,
            "purpose": definition.purpose,
            "authority": definition.authority,
            "basis": definition.basis,
        },
        "period": period.as_dict(),
        "generated_at": generated_at.replace(microsecond=0).isoformat(),
        "filters_applied": applied,
        "summary": [
            {
                "key": metric.key,
                "label": metric.label,
                "value": json_value(metric.value),
                "type": metric.type,
                "hint": metric.hint,
            }
            for metric in result.summary
        ],
        "sections": sections,
        "notes": list(result.notes),
        "reconciliation": [
            {
                "check": item.check,
                "expected": json_value(item.expected),
                "actual": json_value(item.actual),
                "difference": json_value(item.difference),
                "type": item.type,
                "status": "PASS" if item.passed else "DIFFERENCE",
            }
            for item in result.reconciliation
        ],
    }


def column_set(*columns: Column) -> tuple[Column, ...]:
    keys = [column.key for column in columns]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate report column key.")
    return tuple(columns)
