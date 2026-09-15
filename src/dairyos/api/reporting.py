"""Governed read-only Reporting API foundation for DairyOS."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from dairyos.api.dependencies import get_container
from dairyos.farm.herd.services.animal_classification_service import (
    AnimalClassificationError,
    AnimalClassificationService,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


router = APIRouter(prefix="/farm/reporting", tags=["Reporting"])


DomainKey = Literal[
    "ANIMALS",
    "MILK",
    "MILK_QUALITY",
    "FEED",
    "FINANCE",
    "BREEDING",
    "SEMEN",
    "HEALTH",
    "VACCINATION",
    "COML",
    "WHOLE_FARM",
]


PeriodMode = Literal[
    "TODAY",
    "YESTERDAY",
    "OPERATIONAL_DATE",
    "CURRENT_HERD",
    "AS_OF_DATE",
    "DATE_RANGE",
    "MONTH",
    "CUSTOM_PERIOD",
    "CURRENT_YEAR",
    "SNAPSHOT_DATE",
]


class ReportDefinition(BaseModel):
    id: str
    domain: DomainKey
    name: str
    authority: str
    period_modes: tuple[PeriodMode, ...]
    filters: tuple[str, ...]
    scope_note: str
    required_permissions: tuple[str, ...]
    historical_capability: Literal[
        "CURRENT_ONLY",
        "HISTORICAL",
        "SNAPSHOT",
    ]


REPORTS: tuple[ReportDefinition, ...] = (
    ReportDefinition(
        id="animal-register",
        domain="ANIMALS",
        name="Animal Register",
        authority=(
            "Animal master records, lifecycle status, disposition history, "
            "and governed category mapping."
        ),
        period_modes=("CURRENT_HERD",),
        filters=("category", "status"),
        scope_note=(
            "Supports the current herd across all six canonical DairyOS "
            "categories. Historical herd reconstruction is not currently "
            "authoritative."
        ),
        required_permissions=("animals.view",),
        historical_capability="CURRENT_ONLY",
    ),
    ReportDefinition(
        id="animal-population",
        domain="ANIMALS",
        name="Animal Population by Category",
        authority=(
            "Animal category authority with active/inactive disposition "
            "semantics."
        ),
        period_modes=("CURRENT_HERD",),
        filters=("status",),
        scope_note=(
            "Counts the current herd as Milking Cows, Dry Cows, Heifers, "
            "Female Calves, Male Calves, and Bulls. Historical population "
            "reconstruction is not currently authoritative."
        ),
        required_permissions=("animals.view",),
        historical_capability="CURRENT_ONLY",
    ),
    ReportDefinition(
        id="animal-lifecycle",
        domain="ANIMALS",
        name="Animal Entry / Lifecycle Report",
        authority=(
            "Animal registration, acquisition, lifecycle, disposition, "
            "and operational event records."
        ),
        period_modes=("DATE_RANGE", "CUSTOM_PERIOD"),
        filters=("category", "event_type"),
        scope_note=(
            "Shows additions, category transitions, exits, and governed "
            "lifecycle events where authority exists."
        ),
        required_permissions=("animals.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="animal-passport",
        domain="ANIMALS",
        name="Individual Animal Passport",
        authority=(
            "Lifetime Animal Passport read model and animal-scoped "
            "operational histories."
        ),
        period_modes=("AS_OF_DATE", "CURRENT_HERD"),
        filters=("animal_id",),
        scope_note=(
            "Generates Passport output from the selected animal authority "
            "rather than modal chrome."
        ),
        required_permissions=("animals.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="daily-milk",
        domain="MILK",
        name="Daily Milk Production",
        authority=(
            "Milk production rows, milking session records, corrections, "
            "and disposition authority."
        ),
        period_modes=(
            "TODAY",
            "YESTERDAY",
            "OPERATIONAL_DATE",
            "DATE_RANGE",
        ),
        filters=(
            "session",
            "category",
            "animal_id",
            "milking_cohort",
        ),
        scope_note=(
            "Keeps MORNING, AFTERNOON, EVENING, and all-session views "
            "distinct."
        ),
        required_permissions=("milk.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="milk-animal",
        domain="MILK",
        name="Milk Production by Animal",
        authority=(
            "Per-animal milk production and milking-frequency history."
        ),
        period_modes=("DATE_RANGE", "MONTH", "CUSTOM_PERIOD"),
        filters=("animal_id", "milking_cohort"),
        scope_note=(
            "Prevents misleading comparison of twice- and "
            "thrice-milked animals."
        ),
        required_permissions=("milk.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="milk-disposition",
        domain="MILK",
        name="Milk Disposition / Reconciliation",
        authority=(
            "Milk production, sold/domestic/calf/wastage/withdrawal "
            "disposition records, and correction history."
        ),
        period_modes=("DATE_RANGE", "MONTH"),
        filters=("disposition_type", "status"),
        scope_note=(
            "Separates saleable, withdrawal, wastage, and unaccounted milk."
        ),
        required_permissions=("milk.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="milk-quality-log",
        domain="MILK_QUALITY",
        name="Milk Quality Log",
        authority=(
            "Milk quality samples with recorded status, operator, "
            "timestamps, and revision history."
        ),
        period_modes=("DATE_RANGE", "OPERATIONAL_DATE", "MONTH"),
        filters=("sample_type", "status"),
        scope_note=(
            "Central replacement for the former popup-dependent "
            "Milk Quality print path."
        ),
        required_permissions=("milk.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="quality-summary",
        domain="MILK_QUALITY",
        name="Milk Quality Summary",
        authority=(
            "Recorded milk quality samples and governed quality thresholds."
        ),
        period_modes=("DATE_RANGE", "MONTH"),
        filters=("sample_type",),
        scope_note=(
            "Summarizes available fat, SNF, and quality classification "
            "fields only."
        ),
        required_permissions=("milk.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="current-tmr",
        domain="FEED",
        name="Current TMR",
        authority=(
            "Governed TMR stage/category authority and Finance-backed "
            "ingredient pricing where available."
        ),
        period_modes=("CURRENT_HERD", "OPERATIONAL_DATE"),
        filters=("category", "ingredient"),
        scope_note=(
            "Distinguishes formulation, ration, cost, consumption, "
            "and inventory movement."
        ),
        required_permissions=("feed.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="historical-tmr",
        domain="FEED",
        name="Historical TMR / Feed Cost",
        authority=(
            "Daily TMR snapshots, feed records, feed inventory movements, "
            "and cost basis."
        ),
        period_modes=("AS_OF_DATE", "DATE_RANGE"),
        filters=("category", "ingredient"),
        scope_note=(
            "Uses historical TMR/feed authority instead of today's ration "
            "for old dates."
        ),
        required_permissions=("feed.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="finance-ledger",
        domain="FINANCE",
        name="Transaction Ledger",
        authority=(
            "Finance ledger, classifier, settlement status, VOID rules, "
            "and COP attribution."
        ),
        period_modes=("DATE_RANGE", "MONTH", "CUSTOM_PERIOD"),
        filters=(
            "transaction_type",
            "status",
            "category",
            "counterparty",
        ),
        scope_note=(
            "VOID rows remain available for audit while excluded from "
            "active totals."
        ),
        required_permissions=("finance.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="financial-summary",
        domain="FINANCE",
        name="Income and Expense Summary",
        authority=(
            "Governed Finance calculations and transaction classifier."
        ),
        period_modes=("DATE_RANGE", "MONTH", "CURRENT_YEAR"),
        filters=("category", "payment_state"),
        scope_note=(
            "Requires Finance permission and must reconcile independently "
            "to source rows."
        ),
        required_permissions=("finance.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="breeding-cycle",
        domain="BREEDING",
        name="Reproductive Cycle History",
        authority=(
            "Breeding lifecycle records, cycle attribution, PD results, "
            "pregnancy loss, and calving events."
        ),
        period_modes=("DATE_RANGE", "AS_OF_DATE"),
        filters=("animal_id", "technician", "event_type"),
        scope_note=(
            "Does not merge failed historical cycles into later "
            "successful cycles."
        ),
        required_permissions=("breeding.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="breeding-performance",
        domain="BREEDING",
        name="Pregnancy and AI Performance",
        authority=(
            "Cycle-aware breeding analytics and semen usage links."
        ),
        period_modes=("DATE_RANGE", "CUSTOM_PERIOD"),
        filters=("technician", "semen_type", "semen_lot"),
        scope_note=(
            "Pregnancy ratio must use governed successful-cycle attribution."
        ),
        required_permissions=("breeding.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="semen-stock",
        domain="SEMEN",
        name="Semen Stock Balance",
        authority=(
            "Semen lots, purchases, stock movements, breeding usage, "
            "and Finance purchase links."
        ),
        period_modes=("AS_OF_DATE", "DATE_RANGE"),
        filters=("semen_type", "lot", "supplier"),
        scope_note=(
            "Purchased, used, and available balances reconcile to "
            "stock movements."
        ),
        required_permissions=("breeding.view", "finance.view"),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="health-cases",
        domain="HEALTH",
        name="Health Cases and Treatments",
        authority=(
            "Health cases, observations, treatments, withdrawal "
            "references, and animal IDs."
        ),
        period_modes=("DATE_RANGE", "AS_OF_DATE"),
        filters=("animal_id", "case_status", "severity"),
        scope_note=(
            "Animal-specific reports include only records attributed "
            "to the selected animal."
        ),
        required_permissions=("health.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="withdrawal",
        domain="HEALTH",
        name="Withdrawal Periods",
        authority=(
            "Treatment records, withdrawal calculation source, "
            "and active health state."
        ),
        period_modes=("OPERATIONAL_DATE", "DATE_RANGE"),
        filters=("animal_id", "status"),
        scope_note=(
            "Separates active withdrawal from resolved clinical history."
        ),
        required_permissions=("health.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="vaccination-schedule",
        domain="VACCINATION",
        name="Vaccination Schedule and Due Status",
        authority=(
            "Vaccination records, administered state, schedule rows, "
            "due and overdue dates."
        ),
        period_modes=(
            "OPERATIONAL_DATE",
            "DATE_RANGE",
            "CUSTOM_PERIOD",
        ),
        filters=("animal_id", "vaccine", "schedule_status"),
        scope_note=(
            "Future schedules stay in Reporting and do not alter today's "
            "Dashboard attention rules."
        ),
        required_permissions=("health.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="coml-period",
        domain="COML",
        name="Period COML / COP",
        authority=(
            "Locked COML records, historical TMR snapshots, milk "
            "denominator, and Finance OPEX attribution."
        ),
        period_modes=("MONTH", "CUSTOM_PERIOD"),
        filters=("lock_status", "cost_component"),
        scope_note=(
            "Missing authority stays incomplete rather than being "
            "treated as zero."
        ),
        required_permissions=("coml.view",),
        historical_capability="HISTORICAL",
    ),
    ReportDefinition(
        id="whole-farm-snapshot",
        domain="WHOLE_FARM",
        name="Complete Farm Snapshot",
        authority=(
            "Cross-domain authoritative projections as of the selected "
            "operational date."
        ),
        period_modes=("SNAPSHOT_DATE",),
        filters=("major_sections",),
        scope_note=(
            "Central report: herd, milk, quality, feed, finance, breeding, "
            "semen, health, vaccination, COML/COP, and operational attention."
        ),
        required_permissions=(
            "animals.view",
            "milk.view",
            "feed.view",
            "finance.view",
            "breeding.view",
            "health.view",
            "coml.view",
            "analytics.view",
        ),
        historical_capability="SNAPSHOT",
    ),
)


REPORT_BY_ID = {
    report.id: report
    for report in REPORTS
}


class ReportingRequest(BaseModel):
    report_id: str = Field(min_length=1)
    domain: DomainKey
    period_mode: PeriodMode
    operational_date: date | None = None
    as_of_date: date | None = None
    snapshot_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    filters: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict
    )

    @field_validator("report_id")
    @classmethod
    def normalize_report_id(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_report_contract(self):
        definition = REPORT_BY_ID.get(self.report_id)

        if definition is None:
            raise ValueError(
                f"Unknown report_id: {self.report_id}"
            )

        if self.domain != definition.domain:
            raise ValueError(
                "domain does not match the selected report"
            )

        if self.period_mode not in definition.period_modes:
            raise ValueError(
                "period_mode is not supported by the selected report"
            )

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError(
                "start_date must be on or before end_date"
            )

        range_modes = {
            "DATE_RANGE",
            "CUSTOM_PERIOD",
        }

        if self.period_mode in range_modes:
            if self.start_date is None or self.end_date is None:
                raise ValueError(
                    "start_date and end_date are required "
                    "for the selected period_mode"
                )

        if (
            self.period_mode == "AS_OF_DATE"
            and self.as_of_date is None
        ):
            raise ValueError(
                "as_of_date is required for AS_OF_DATE"
            )

        if (
            self.period_mode == "OPERATIONAL_DATE"
            and self.operational_date is None
        ):
            raise ValueError(
                "operational_date is required for OPERATIONAL_DATE"
            )

        if (
            self.period_mode == "SNAPSHOT_DATE"
            and self.snapshot_date is None
        ):
            raise ValueError(
                "snapshot_date is required for SNAPSHOT_DATE"
            )

        unsupported_filters = sorted(
            set(self.filters) - set(definition.filters)
        )

        if unsupported_filters:
            raise ValueError(
                "Unsupported filter(s) for report: "
                + ", ".join(unsupported_filters)
            )

        return self


def reporting_permission_for_request(
    report_id: str | None,
) -> str | None:
    """
    Return the middleware permission for a Reporting request.

    Reports requiring one permission can be enforced directly by the
    existing request middleware.

    Multi-authority reports are deliberately not reduced to one weaker
    permission. Their complete permission set remains part of the report
    definition and must be enforced when the canonical dataset is enabled.
    """
    if not report_id:
        return "settings.view"

    definition = REPORT_BY_ID.get(
        str(report_id).strip().lower()
    )

    if definition is None:
        return "settings.view"

    if len(definition.required_permissions) == 1:
        return definition.required_permissions[0]

    return "settings.view"


def _resolved_period(
    request: ReportingRequest,
    *,
    operational_today: date,
) -> dict[str, str | None]:
    if request.period_mode == "TODAY":
        return {
            "start_date": operational_today.isoformat(),
            "end_date": operational_today.isoformat(),
            "as_of_date": operational_today.isoformat(),
        }

    if request.period_mode == "YESTERDAY":
        from datetime import timedelta

        selected = operational_today - timedelta(days=1)

        return {
            "start_date": selected.isoformat(),
            "end_date": selected.isoformat(),
            "as_of_date": selected.isoformat(),
        }

    if request.period_mode == "OPERATIONAL_DATE":
        selected = request.operational_date

        return {
            "start_date": selected.isoformat(),
            "end_date": selected.isoformat(),
            "as_of_date": selected.isoformat(),
        }

    if request.period_mode == "AS_OF_DATE":
        return {
            "start_date": None,
            "end_date": request.as_of_date.isoformat(),
            "as_of_date": request.as_of_date.isoformat(),
        }

    if request.period_mode in {
        "DATE_RANGE",
        "CUSTOM_PERIOD",
    }:
        return {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "as_of_date": request.end_date.isoformat(),
        }

    if request.period_mode == "SNAPSHOT_DATE":
        return {
            "start_date": None,
            "end_date": request.snapshot_date.isoformat(),
            "as_of_date": request.snapshot_date.isoformat(),
        }

    if request.period_mode == "CURRENT_HERD":
        return {
            "start_date": None,
            "end_date": operational_today.isoformat(),
            "as_of_date": operational_today.isoformat(),
        }

    if request.period_mode == "MONTH":
        selected = (
            request.as_of_date
            or request.operational_date
            or operational_today
        )

        if selected.month == 12:
            next_month = date(selected.year + 1, 1, 1)
        else:
            next_month = date(
                selected.year,
                selected.month + 1,
                1,
            )

        from datetime import timedelta

        month_start = selected.replace(day=1)
        month_end = next_month - timedelta(days=1)

        return {
            "start_date": month_start.isoformat(),
            "end_date": month_end.isoformat(),
            "as_of_date": month_end.isoformat(),
        }

    if request.period_mode == "CURRENT_YEAR":
        return {
            "start_date": date(
                operational_today.year,
                1,
                1,
            ).isoformat(),
            "end_date": date(
                operational_today.year,
                12,
                31,
            ).isoformat(),
            "as_of_date": operational_today.isoformat(),
        }

    raise HTTPException(
        status_code=422,
        detail="Unsupported Reporting period mode.",
    )


TERMINAL_ANIMAL_LIFECYCLE_STATUSES = {
    "SOLD",
    "CULLED",
    "DECEASED",
}

ANIMAL_CATEGORY_ORDER = (
    "Milking",
    "Dry",
    "Heifer",
    "Female Calf",
    "Male Calf",
    "Bull",
)

ANIMAL_CATEGORY_TOTAL_LABELS = {
    "Milking": "Milking Cows",
    "Dry": "Dry Cows",
    "Heifer": "Heifers",
    "Female Calf": "Female Calves",
    "Male Calf": "Male Calves",
    "Bull": "Bulls",
}

ANIMAL_CATEGORY_FILTER_ALIASES = {
    "MILKING": "Milking",
    "MILKING COW": "Milking",
    "MILKING COWS": "Milking",
    "DRY": "Dry",
    "DRY COW": "Dry",
    "DRY COWS": "Dry",
    "HEIFER": "Heifer",
    "HEIFERS": "Heifer",
    "FEMALE CALF": "Female Calf",
    "FEMALE CALVES": "Female Calf",
    "MALE CALF": "Male Calf",
    "MALE CALVES": "Male Calf",
    "BULL": "Bull",
    "BULLS": "Bull",
}


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _date_or_none(value: Any) -> str | None:
    if value is None:
        return None

    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()

    return str(value)


def _normalise_category_filter(value: Any) -> str:
    key = str(value).strip().upper()

    category = ANIMAL_CATEGORY_FILTER_ALIASES.get(key)
    if category is None:
        allowed = ", ".join(ANIMAL_CATEGORY_ORDER)
        raise HTTPException(
            status_code=422,
            detail=(
                "Unsupported Animal Reporting category filter. "
                f"Allowed canonical categories: {allowed}."
            ),
        )

    return category


def _animal_status_matches(animal: Any, requested: Any) -> bool:
    if requested is None:
        return True

    expected = str(requested).strip().upper()
    if not expected or expected == "ALL":
        return True

    actual = _text_or_none(getattr(animal, "status", None))
    if actual is None:
        return False

    return actual.upper() == expected


def _classify_current_animal(animal: Any) -> str | None:
    lifecycle = _text_or_none(
        getattr(animal, "lifecycle_status", None)
    )

    if lifecycle and lifecycle.upper() in TERMINAL_ANIMAL_LIFECYCLE_STATUSES:
        return None

    try:
        classification = AnimalClassificationService.classify(
            lifecycle,
            getattr(animal, "sex", None),
        )
    except AnimalClassificationError as exc:
        animal_id = _text_or_none(
            getattr(animal, "animal_id", None)
        ) or "<unknown>"

        raise HTTPException(
            status_code=409,
            detail={
                "code": "ANIMAL_REPORTING_AUTHORITY_INTEGRITY_ERROR",
                "animal_id": animal_id,
                "message": str(exc),
            },
        ) from exc

    category = classification.category.value

    if category == "Exited":
        return None

    if category not in ANIMAL_CATEGORY_ORDER:
        animal_id = _text_or_none(
            getattr(animal, "animal_id", None)
        ) or "<unknown>"

        raise HTTPException(
            status_code=409,
            detail={
                "code": "ANIMAL_REPORTING_CATEGORY_NOT_GOVERNED",
                "animal_id": animal_id,
                "category": category,
            },
        )

    return category


def _animal_register_row(
    animal: Any,
    *,
    category: str,
) -> dict[str, Any]:
    return {
        "animal_id": _text_or_none(
            getattr(animal, "animal_id", None)
        ),
        "legacy_animal_id": _text_or_none(
            getattr(animal, "legacy_animal_id", None)
        ),
        "ear_tag": _text_or_none(
            getattr(animal, "ear_tag", None)
        ),
        "rfid": _text_or_none(
            getattr(animal, "rfid", None)
        ),
        "category": category,
        "lifecycle_status": _text_or_none(
            getattr(animal, "lifecycle_status", None)
        ),
        "status": _text_or_none(
            getattr(animal, "status", None)
        ),
        "sex": _text_or_none(
            getattr(animal, "sex", None)
        ),
        "breed": _text_or_none(
            getattr(animal, "breed", None)
        ),
        "date_of_birth": _date_or_none(
            getattr(animal, "date_of_birth", None)
        ),
        "date_of_acquisition": _date_or_none(
            getattr(animal, "date_of_acquisition", None)
        ),
        "dam_id": _text_or_none(
            getattr(animal, "dam_id", None)
        ),
        "sire_id": _text_or_none(
            getattr(animal, "sire_id", None)
        ),
        "is_currently_milking": bool(
            getattr(animal, "is_currently_milking", False)
        ),
        "milking_frequency": _text_or_none(
            getattr(animal, "milking_frequency", None)
        ),
        "active": bool(
            getattr(animal, "active", False)
        ),
    }


def _current_animal_rows(
    payload: ReportingRequest,
    *,
    container: Any,
) -> list[dict[str, Any]]:
    repository = getattr(container, "animal_repository", None)

    if repository is None:
        raise HTTPException(
            status_code=503,
            detail="Authoritative Animal repository is not available.",
        )

    get_all = getattr(repository, "get_all", None)

    if not callable(get_all):
        raise HTTPException(
            status_code=503,
            detail="Authoritative Animal repository cannot list animals.",
        )

    animals = list(get_all() or [])

    category_filter = None
    if payload.filters.get("category") is not None:
        category_filter = _normalise_category_filter(
            payload.filters["category"]
        )

    rows: list[dict[str, Any]] = []

    for animal in animals:
        category = _classify_current_animal(animal)

        if category is None:
            continue

        if category_filter is not None and category != category_filter:
            continue

        if not _animal_status_matches(
            animal,
            payload.filters.get("status"),
        ):
            continue

        rows.append(
            _animal_register_row(
                animal,
                category=category,
            )
        )

    rows.sort(
        key=lambda row: (
            row["animal_id"] is None,
            row["animal_id"] or "",
        )
    )

    return rows


def _animal_category_counts(
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    counts = {
        category: 0
        for category in ANIMAL_CATEGORY_ORDER
    }

    for row in rows:
        category = row["category"]
        counts[category] += 1

    return counts


def _animal_register_dataset(
    payload: ReportingRequest,
    *,
    container: Any,
) -> dict[str, Any]:
    rows = _current_animal_rows(
        payload,
        container=container,
    )

    counts = _animal_category_counts(rows)

    herd_totals = {
        ANIMAL_CATEGORY_TOTAL_LABELS[category]: counts[category]
        for category in ANIMAL_CATEGORY_ORDER
    }

    return {
        "dataset_status": "AUTHORITATIVE_CURRENT_DATASET",
        "authority_status": "CURRENT_AUTHORITY_AVAILABLE",
        "columns": [
            "animal_id",
            "legacy_animal_id",
            "ear_tag",
            "rfid",
            "category",
            "lifecycle_status",
            "status",
            "sex",
            "breed",
            "date_of_birth",
            "date_of_acquisition",
            "dam_id",
            "sire_id",
            "is_currently_milking",
            "milking_frequency",
            "active",
        ],
        "rows": rows,
        "summary": {
            "total_current_animals": len(rows),
            "category_counts": counts,
            "herd_totals": herd_totals,
        },
        "warnings": (
            []
            if rows
            else [
                "No current Animal Register records match the selected filters."
            ]
        ),
    }


def _animal_population_dataset(
    payload: ReportingRequest,
    *,
    container: Any,
) -> dict[str, Any]:
    rows = _current_animal_rows(
        payload,
        container=container,
    )

    counts = _animal_category_counts(rows)

    population_rows = [
        {
            "category": category,
            "herd_total_label": ANIMAL_CATEGORY_TOTAL_LABELS[category],
            "count": counts[category],
        }
        for category in ANIMAL_CATEGORY_ORDER
    ]

    return {
        "dataset_status": "AUTHORITATIVE_CURRENT_DATASET",
        "authority_status": "CURRENT_AUTHORITY_AVAILABLE",
        "columns": [
            "category",
            "herd_total_label",
            "count",
        ],
        "rows": population_rows,
        "summary": {
            "total_current_animals": len(rows),
            "category_counts": counts,
            "herd_totals": {
                ANIMAL_CATEGORY_TOTAL_LABELS[category]: counts[category]
                for category in ANIMAL_CATEGORY_ORDER
            },
        },
        "warnings": (
            []
            if rows
            else [
                "No current Animal Register records match the selected filters."
            ]
        ),
    }


def _canonical_dataset(
    payload: ReportingRequest,
    *,
    container: Any,
) -> dict[str, Any] | None:
    if payload.report_id == "animal-register":
        return _animal_register_dataset(
            payload,
            container=container,
        )

    if payload.report_id == "animal-population":
        return _animal_population_dataset(
            payload,
            container=container,
        )

    return None


@router.get("/catalog")
def reporting_catalog():
    return {
        "data_status": "REPORTING_CATALOG",
        "read_only": True,
        "reports": [
            report.model_dump()
            for report in REPORTS
        ],
    }


@router.post("/preview")
def reporting_preview(
    payload: ReportingRequest,
    container=Depends(get_container),
):
    definition = REPORT_BY_ID[payload.report_id]

    authority = OperationalDateAuthority()
    operational_today = authority.current_date()
    generated_at = authority.current_datetime()

    period = _resolved_period(
        payload,
        operational_today=operational_today,
    )

    dataset = _canonical_dataset(
        payload,
        container=container,
    )

    if dataset is None:
        dataset = {
            "dataset_status": "DATASET_NOT_IMPLEMENTED",
            "authority_status": "DATASET_NOT_IMPLEMENTED",
            "columns": [],
            "rows": [],
            "summary": {},
            "warnings": [
                (
                    "Canonical dataset generation is not implemented "
                    "for this report yet. No farm values have been "
                    "fabricated."
                )
            ],
        }

    rows = dataset["rows"]

    return {
        "data_status": "REPORTING_DATASET",
        "dataset_status": dataset["dataset_status"],
        "read_only": True,
        "report_id": definition.id,
        "domain": definition.domain,
        "title": definition.name,
        "authority": definition.authority,
        "authority_status": dataset["authority_status"],
        "historical_capability": definition.historical_capability,
        "required_permissions": list(
            definition.required_permissions
        ),
        "period_mode": payload.period_mode,
        "period": period,
        "filters": payload.filters,
        "generated_at": generated_at.isoformat(),
        "record_count": len(rows),
        "columns": dataset["columns"],
        "rows": rows,
        "summary": dataset["summary"],
        "warnings": dataset["warnings"],
    }
