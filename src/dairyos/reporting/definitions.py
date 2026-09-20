"""Typed contracts for the DairyOS Reporting catalogue and report results."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

ColumnType = Literal[
    "text",
    "integer",
    "number",
    "litres",
    "kg",
    "money",
    "rate",
    "percent",
    "date",
    "datetime",
    "status",
    "days",
]

NUMERIC_TYPES = frozenset(
    {"integer", "number", "litres", "kg", "money", "rate", "percent", "days"}
)

#: How a report is positioned in time.
#:   none   - current state, no date control
#:   as_of  - a single operational date
#:   range  - an inclusive From/To period (month, quarter, custom, shortcuts)
PeriodKind = Literal["none", "as_of", "range"]

FilterKind = Literal["select", "text", "animal", "toggle"]


@dataclass(frozen=True)
class Column:
    """One operator-facing report column.

    ``tier`` controls exposure: ``default`` columns are shown without any
    operator decision, ``optional`` columns are offered under Customize
    Columns, ``advanced`` columns are administrative/audit fields that are
    only offered when the operator deliberately opens the advanced group.
    """

    key: str
    label: str
    type: ColumnType = "text"
    group: str = "Details"
    tier: Literal["default", "optional", "advanced"] = "default"
    total: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "type": self.type,
            "group": self.group,
            "tier": self.tier,
            "total": self.total,
        }


@dataclass(frozen=True)
class Filter:
    """One report-specific filter. ``options_source`` names a governed
    reference list resolved by the engine (for example ``breeds``)."""

    key: str
    label: str
    kind: FilterKind = "select"
    options: tuple[tuple[str, str], ...] = ()
    options_source: str | None = None
    required: bool = False
    default: str | bool | None = None
    help: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "kind": self.kind,
            "options": [{"value": v, "label": l} for v, l in self.options],
            "options_source": self.options_source,
            "required": self.required,
            "default": self.default,
            "help": self.help,
        }


@dataclass
class Section:
    """One table of a report result."""

    id: str
    title: str
    columns: tuple[Column, ...]
    rows: list[dict[str, Any]]
    totals: dict[str, Any] | None = None
    note: str | None = None
    #: The primary section is the one affected by column customisation,
    #: sorting and pagination.
    primary: bool = False
    empty_message: str | None = None


@dataclass
class Metric:
    key: str
    label: str
    value: Any
    type: ColumnType = "text"
    hint: str | None = None


@dataclass
class ReconciliationCheck:
    check: str
    expected: Any
    actual: Any
    type: ColumnType = "money"

    @property
    def difference(self) -> Any:
        try:
            return self.actual - self.expected
        except TypeError:
            return None

    @property
    def passed(self) -> bool:
        return self.expected == self.actual


@dataclass
class ReportResult:
    sections: list[Section]
    summary: list[Metric] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    reconciliation: list[ReconciliationCheck] = field(default_factory=list)


Builder = Callable[["ReportContext"], ReportResult]  # noqa: F821


@dataclass(frozen=True)
class ReportDefinition:
    id: str
    area: str
    title: str
    purpose: str
    authority: str
    permission: str
    builder: Builder
    period: PeriodKind = "none"
    default_period: str = "CURRENT_MONTH"
    filters: tuple[Filter, ...] = ()
    #: Column catalogue of the primary section (drives Customize Columns).
    columns: tuple[Column, ...] = ()
    default_sort: tuple[str, Literal["asc", "desc"]] | None = None
    empty_message: str = "No records match the selected parameters."
    #: How the information is obtained: RECORDED (directly persisted),
    #: CALCULATED (an authoritative DairyOS calculation) or DERIVED
    #: (a reporting metric defined in this catalogue from recorded inputs).
    basis: Literal["RECORDED", "CALCULATED", "DERIVED"] = "RECORDED"
    #: Builder-specific preset (for example the herd category of a
    #: category register) so one builder can serve several definitions.
    preset: dict[str, Any] = field(default_factory=dict)

    def catalog_entry(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "area": self.area,
            "title": self.title,
            "purpose": self.purpose,
            "authority": self.authority,
            "permission": self.permission,
            "period": self.period,
            "default_period": self.default_period,
            "filters": [item.as_dict() for item in self.filters],
            "columns": [item.as_dict() for item in self.columns],
            "default_sort": (
                {"key": self.default_sort[0], "dir": self.default_sort[1]}
                if self.default_sort
                else None
            ),
            "basis": self.basis,
        }


@dataclass(frozen=True)
class Area:
    id: str
    title: str
    description: str
    permission: str
