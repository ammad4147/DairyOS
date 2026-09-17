"""The DairyOS report catalogue."""

from __future__ import annotations

from typing import Any

from dairyos.reporting.areas import breeding, cost, feed, finance, health, herd, management, milk
from dairyos.reporting.definitions import Area, ReportDefinition

AREAS: tuple[Area, ...] = (
    Area("herd", "Herd", "Who is on the farm: registers, categories, movement, exits and identification.", "animals.view"),
    Area("milk", "Milk", "What the herd produced, by day, animal and session, and where the milk went.", "milk.view"),
    Area("feed", "Feed", "Rations, feed cost, stock on hand and stock movement.", "feed.view"),
    Area("breeding", "Breeding", "Reproductive status, work due, outcomes, technicians and semen.", "breeding.view"),
    Area("health", "Health", "Cases, treatments, milk withdrawal and vaccination.", "health.view"),
    Area("finance", "Finance", "Revenue, expenses, reconciliation, receivables, payables and audit trail.", "finance.view"),
    Area("cost", "Cost of Milk", "Feed cost, OPEX and cost of production per litre.", "coml.view"),
    Area("management", "Management", "Cross-module summaries and the items that need attention.", "settings.view"),
)

_MODULES = (herd, milk, feed, breeding, health, finance, cost, management)

REPORTS: tuple[ReportDefinition, ...] = tuple(
    definition for module in _MODULES for definition in module.REPORTS
)

REPORT_BY_ID: dict[str, ReportDefinition] = {}
for _definition in REPORTS:
    if _definition.id in REPORT_BY_ID:
        raise RuntimeError(f"Duplicate report id: {_definition.id}")
    REPORT_BY_ID[_definition.id] = _definition

_AREA_IDS = {area.id for area in AREAS}
for _definition in REPORTS:
    if _definition.area not in _AREA_IDS:
        raise RuntimeError(f"Report {_definition.id} names an unknown area: {_definition.area}")


def get_report(report_id: str | None) -> ReportDefinition | None:
    return REPORT_BY_ID.get(str(report_id or "").strip().lower())


def catalog() -> dict[str, Any]:
    return {
        "areas": [
            {
                "id": area.id,
                "title": area.title,
                "description": area.description,
                "permission": area.permission,
                "reports": [d.catalog_entry() for d in REPORTS if d.area == area.id],
            }
            for area in AREAS
        ],
    }
