"""Read-only operational evidence tools for the DairyOS AI Assistant.

The knowledge corpus and the operational database are deliberately separate
authorities.  This module is the bridge between them: it opens a short-lived
transaction in PostgreSQL read-only mode, invokes only read paths, and
returns bounded, sanitised evidence to the Assistant planner.

No handler in this module adds, updates, deletes, truncates, migrates, or
repairs a record.  The database read-only transaction is a second safety
boundary in addition to the tool registry contract.
"""

from __future__ import annotations

import math
import os
import re
from calendar import monthrange
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import sqlalchemy as sa

from dairyos.api.coml import get_integrated_coml
from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.database.models.operational_event_model import OperationalEventModel
from dairyos.data.models.animal import Animal
from dairyos.data.models.breeding_propagation_outbox import BreedingPropagationOutbox
from dairyos.data.models.feed_ration import FeedRation
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.health_case import HealthCase
from dairyos.data.models.health_observation import HealthObservation
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.operational_finding import OperationalFinding
from dairyos.data.models.operational_finding_lifecycle_event import (
    OperationalFindingLifecycleEvent,
)
from dairyos.data.models.operational_write import (
    OperationalProjectionOutbox,
    OperationalWrite,
)
from dairyos.data.models.treatment_record import TreatmentRecord
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from dairyos.finance.classification.transaction_classifier import is_expense, is_income
from dairyos.herd.reproduction.services.reproductive_event_classifier import is_calving
from dairyos.platform.paths import logs_dir

_MONTHS = {
    name.lower(): number
    for number, name in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}
_MONTH_ALIASES = {**_MONTHS, **{name[:3]: value for name, value in _MONTHS.items()}}
_SENSITIVE_WORDS = (
    "password",
    "secret",
    "token",
    "credential",
    "private_key",
    "api_key",
    "access_key",
)
_MAX_LIMIT = 100
_TABLE_ROW_MAX = 100
_FILE_LOG_MAX_BYTES = 256_000
_FILE_LOG_LINE_MAX = 4_000
_DOMAIN_MODELS = {
    "animals": Animal,
    "milk_production": MilkProduction,
    "feed_records": FeedRecord,
    "feed_rations": FeedRation,
    "financial_transactions": FinancialTransaction,
    "health_observations": HealthObservation,
    "health_cases": HealthCase,
    "treatments": TreatmentRecord,
    "breeding_records": BreedingRecordModel,
    "inventory_transactions": InventoryTransaction,
    "milk_dispositions": MilkDisposition,
    "operational_findings": OperationalFinding,
    "operational_writes": OperationalWrite,
    "event_journal": EventJournalModel,
    "operational_events": OperationalEventModel,
    "projection_outbox": OperationalProjectionOutbox,
    "breeding_propagation_outbox": BreedingPropagationOutbox,
    "finding_lifecycle_events": OperationalFindingLifecycleEvent,
}


@dataclass(frozen=True)
class DateWindow:
    requested_start: date | None
    requested_end: date | None
    effective_start: date | None
    effective_end: date | None
    operational_date: date
    completed_only: bool = False

    @property
    def is_empty(self) -> bool:
        """Whether an explicitly requested period has no completed dates."""
        return (
            (self.requested_start is not None or self.requested_end is not None)
            and self.effective_start is None
            and self.effective_end is None
        )

    def contains(self, value: date | None) -> bool:
        if value is None or self.is_empty:
            return False
        return not (
            self.effective_start is not None and value < self.effective_start
        ) and not (self.effective_end is not None and value > self.effective_end)

    def as_dict(self) -> dict[str, Any]:
        return {
            "requested_start": (
                self.requested_start.isoformat() if self.requested_start else None
            ),
            "requested_end": (
                self.requested_end.isoformat() if self.requested_end else None
            ),
            "effective_start": (
                self.effective_start.isoformat() if self.effective_start else None
            ),
            "effective_end": (
                self.effective_end.isoformat() if self.effective_end else None
            ),
            "operational_date": self.operational_date.isoformat(),
            "completed_only": self.completed_only,
            "clamped_to_operational_date": (
                self.requested_end is not None
                and self.requested_end > self.operational_date
            ),
            "empty_effective_window": self.is_empty,
        }


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _parse_date(value: Any, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    parsed = _as_date(value)
    if parsed is None:
        raise ValueError(f"{field_name} must be an ISO date.")
    return parsed


def _month_window(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def _resolve_window(
    question: str = "",
    *,
    operational_date: date,
    start_date: Any = None,
    end_date: Any = None,
    month: Any = None,
    year: Any = None,
    completed_only: bool = False,
    default_to_month: bool = False,
) -> DateWindow:
    explicit_start = _parse_date(start_date, "start_date")
    explicit_end = _parse_date(end_date, "end_date")
    cleaned = str(question or "").lower()
    iso_dates = [
        _as_date(value) for value in re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", cleaned)
    ]
    iso_dates = [value for value in iso_dates if value is not None]
    month_day_patterns = (
        r"\b("
        + "|".join(_MONTH_ALIASES)
        + r")\s+(\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(20\d{2})\b",
        r"\b(\d{1,2})\s+(" + "|".join(_MONTH_ALIASES) + r")\s+(20\d{2})\b",
    )
    named_date: date | None = None
    for pattern_index, pattern in enumerate(month_day_patterns):
        match = re.search(pattern, cleaned)
        if not match:
            continue
        try:
            if pattern_index == 0:
                month_name, day_number, year_number = match.groups()
            else:
                day_number, month_name, year_number = match.groups()
            named_date = date(
                int(year_number),
                _MONTH_ALIASES[month_name.lower()],
                int(day_number),
            )
        except (KeyError, TypeError, ValueError):
            named_date = None
        if named_date is not None:
            break

    start = explicit_start
    end = explicit_end
    if start is None and end is None and iso_dates:
        start = iso_dates[0]
        end = iso_dates[1] if len(iso_dates) > 1 else iso_dates[0]
    elif start is None and end is None and named_date is not None:
        start = end = named_date
    elif start is None and end is not None:
        start = end
    elif start is not None and end is None:
        end = start

    selected_month: int | None = None
    if month not in (None, ""):
        if isinstance(month, int) or str(month).strip().isdigit():
            selected_month = int(month)
        else:
            selected_month = _MONTH_ALIASES.get(str(month).strip().lower())
        if selected_month not in range(1, 13):
            raise ValueError("month must be between 1 and 12 or a month name.")

    if start is None and end is None and selected_month is None:
        # A bare month is accepted for operator shorthand ("milk in July"),
        # while the English modal "may" must not silently become May.
        for token, number in _MONTH_ALIASES.items():
            match = re.search(rf"\b{re.escape(token)}\b", cleaned)
            if not match:
                continue
            if token == "may":
                before = cleaned[: match.start()]
                after = cleaned[match.end() :]
                has_period_context = bool(
                    re.search(
                        r"\b(?:in|during|for|of|from|through|throughout|month)\s*$",
                        before,
                    )
                    or re.match(r"\s+20\d{2}\b", after)
                )
                if not has_period_context:
                    continue
            selected_month = number
            break

    if start is None and end is None and selected_month is not None:
        selected_year = int(year) if year not in (None, "") else operational_date.year
        start, end = _month_window(selected_year, selected_month)
    elif start is None and end is None:
        selected_year = int(year) if year not in (None, "") else operational_date.year
        if "last month" in cleaned:
            anchor = operational_date.replace(day=1) - timedelta(days=1)
            start, end = _month_window(anchor.year, anchor.month)
        elif "this month" in cleaned:
            start, end = _month_window(operational_date.year, operational_date.month)
        elif "yesterday" in cleaned:
            start = end = operational_date - timedelta(days=1)
        elif re.search(r"\b(today|current day)\b", cleaned):
            start = end = operational_date
        elif default_to_month:
            start, end = _month_window(selected_year, operational_date.month)

    if start is not None and end is None:
        end = start
    if end is not None and start is None:
        start = end
    if start is not None and end is not None and end < start:
        raise ValueError("end_date must be on or after start_date.")

    upper_bound = (
        operational_date - timedelta(days=1) if completed_only else operational_date
    )
    effective_start = start
    effective_end = min(end, upper_bound) if end is not None else None
    if (
        effective_start is not None
        and effective_end is not None
        and effective_end < effective_start
    ):
        effective_start = None
        effective_end = None

    return DateWindow(
        requested_start=start,
        requested_end=end,
        effective_start=effective_start,
        effective_end=effective_end,
        operational_date=operational_date,
        completed_only=completed_only,
    )


def _record_date(row: Any, *fields: str) -> date | None:
    for field in fields:
        value = getattr(row, field, None)
        parsed = _as_date(value)
        if parsed is not None:
            return parsed
    return None


def _json_safe(value: Any, *, context_key: str = "") -> Any:
    key = context_key.lower()
    if any(word in key for word in _SENSITIVE_WORDS):
        return "[REDACTED]"
    if isinstance(value, dict):
        context = str(value.get("key", "")) if "key" in value else ""
        return {
            str(k): _json_safe(
                v, context_key=(context if str(k) == "value" else str(k))
            )
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, context_key=context_key) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _row_mapping(row: Any) -> dict[str, Any]:
    if hasattr(row, "_mapping"):
        raw = dict(row._mapping)
    elif isinstance(row, dict):
        raw = dict(row)
    else:
        raw = {
            column.name: getattr(row, column.name, None)
            for column in getattr(row, "__table__", ()).columns
        }
    setting_key = str(raw.get("key") or "")
    return {
        key: _json_safe(
            value,
            context_key=(
                setting_key
                if key == "value"
                and any(word in setting_key.lower() for word in _SENSITIVE_WORDS)
                else key
            ),
        )
        for key, value in raw.items()
    }


def _sanitised_model_row(row: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {
        field: _json_safe(getattr(row, field, None), context_key=field)
        for field in fields
    }


def _with_read_only(callback: Callable[[RepositoryFactory], Any]) -> Any:
    """Run one bounded callback in a transaction PostgreSQL cannot write."""
    factory = RepositoryFactory.create()
    try:
        with factory.session.begin():
            bind = factory.session.get_bind()
            if (
                getattr(bind, "dialect", None) is not None
                and bind.dialect.name == "postgresql"
            ):
                factory.session.execute(sa.text("SET TRANSACTION READ ONLY"))
            return callback(factory)
    finally:
        factory.close()


def _period_filter(window: DateWindow, value: date | None) -> bool:
    if window.is_empty:
        return False
    if window.effective_start is None or window.effective_end is None:
        return True
    return window.contains(value)


def _health_history_requested(question: str) -> bool:
    """Recognise health-record questions that need history, not a differential."""
    lowered = str(question or "").lower()
    explicit_history = (
        "health case",
        "health observation",
        "health history",
        "treatment history",
        "treatments recorded",
        "observations recorded",
        "cases recorded",
    )
    if any(term in lowered for term in explicit_history):
        return True
    return any(term in lowered for term in ("how many", "count", "number of")) and any(
        term in lowered
        for term in ("health", "observation", "treatment", "case")
    )


def _milk_summary(factory: RepositoryFactory, window: DateWindow) -> dict[str, Any]:
    rows = factory.milk().get_all() or []
    daily: Counter[str] = Counter()
    daily_records: Counter[str] = Counter()
    missing_yield = 0
    included = 0
    total = 0.0
    for row in rows:
        status = str(getattr(row, "status", "RECORDED") or "RECORDED").upper()
        if status in {"VOID", "NOT_MILKED"}:
            continue
        row_date = _record_date(row, "production_date", "recorded_at")
        if not _period_filter(window, row_date):
            continue
        value = getattr(row, "total_yield", None)
        if value is None:
            entered = [
                getattr(row, field, None)
                for field in ("morning_yield", "afternoon_yield", "evening_yield")
                if getattr(row, field, None) is not None
            ]
            value = sum(float(item) for item in entered) if entered else None
        if value is None:
            missing_yield += 1
            continue
        litres = float(value or 0.0)
        total += litres
        included += 1
        if row_date is not None:
            key = row_date.isoformat()
            daily[key] += litres
            daily_records[key] += 1
    return {
        "metric": "milk_production",
        "total_litres": round(total, 4),
        "unit": "litres",
        "record_count": included,
        "missing_yield_records": missing_yield,
        "days_with_production": len(daily),
        "daily": [
            {
                "date": key,
                "litres": round(daily[key], 4),
                "record_count": daily_records[key],
            }
            for key in sorted(daily)
        ],
        "basis": "milk_litres_for_period; VOID and NOT_MILKED excluded",
        "source_tables": ["milk_production", "milking_session_records"],
    }


def _event_rows(factory: RepositoryFactory) -> list[EventJournalModel]:
    return (
        factory.session.query(EventJournalModel)
        .order_by(EventJournalModel.id.asc())
        .all()
    )


def _reproductive_summary(
    factory: RepositoryFactory, window: DateWindow
) -> dict[str, Any]:
    breeding = factory.breeding().get_all() or []
    calvings = []
    event_counts: Counter[str] = Counter()
    selected_records = []
    undated = 0
    for row in breeding:
        row_date = _as_date(getattr(row, "timestamp", None))
        if row_date is None:
            if is_calving(row):
                undated += 1
            continue
        if not _period_filter(window, row_date):
            continue
        event_type = str(getattr(row, "event_type", "UNKNOWN") or "UNKNOWN").lower()
        event_counts[event_type] += 1
        selected_records.append(
            {
                "record_id": getattr(row, "record_id", None),
                "animal_id": getattr(row, "animal_id", None),
                "event_type": getattr(row, "event_type", None),
                "result": getattr(row, "result", None),
                "date": row_date.isoformat(),
            }
        )
        if is_calving(row):
            calvings.append(
                {
                    "record_id": getattr(row, "record_id", None),
                    "animal_id": getattr(row, "animal_id", None),
                    "event_type": getattr(row, "event_type", None),
                    "result": getattr(row, "result", None),
                    "date": row_date.isoformat(),
                }
            )

    animals = factory.animal().get_all() or []
    calf_rows = []
    for row in animals:
        animal_type = str(getattr(row, "animal_type", "") or "").upper()
        lifecycle = str(getattr(row, "lifecycle_status", "") or "").upper()
        if "CALF" not in {animal_type, lifecycle} and "CALF" not in animal_type:
            continue
        created_date = _record_date(
            row, "date_of_acquisition", "date_of_birth", "created_at"
        )
        if _period_filter(window, created_date):
            calf_rows.append(
                {
                    "animal_id": getattr(row, "animal_id", None),
                    "animal_type": getattr(row, "animal_type", None),
                    "date_of_birth": _json_safe(getattr(row, "date_of_birth", None)),
                    "date_of_acquisition": _json_safe(
                        getattr(row, "date_of_acquisition", None)
                    ),
                }
            )

    return {
        "metric": "reproduction_and_calf_lifecycle",
        "actual_calving_events": len(calvings),
        "calving_events": calvings,
        "breeding_event_count": len(selected_records),
        "breeding_event_counts": dict(sorted(event_counts.items())),
        "breeding_records": selected_records[:_MAX_LIMIT],
        "calf_animal_records": len(calf_rows),
        "calf_animals": calf_rows,
        "undated_calving_records": undated,
        "basis": "actual persisted breeding events classified as calving; calf master records reported separately",
        "source_tables": ["breeding_records", "animal"],
    }


def _finance_summary(factory: RepositoryFactory, window: DateWindow) -> dict[str, Any]:
    rows = factory.finance().get_all() or []
    selected = []
    income = 0.0
    expenses = 0.0
    for row in rows:
        row_date = _record_date(row, "transaction_date")
        if not _period_filter(window, row_date):
            continue
        amount = float(getattr(row, "amount", 0) or 0)
        if is_income(row):
            income += amount
        if is_expense(row):
            expenses += amount
        selected.append(
            _sanitised_model_row(
                row,
                (
                    "id",
                    "transaction_type",
                    "category",
                    "amount",
                    "transaction_date",
                    "currency",
                    "status",
                    "master_category",
                    "sub_category",
                    "cop_classification",
                    "cop_attribution_method",
                    "cop_service_date",
                    "cop_coverage_start",
                    "cop_coverage_end",
                ),
            )
        )
    return {
        "metric": "finance_transactions",
        "transaction_count": len(selected),
        "income_total": round(income, 2),
        "expense_total": round(expenses, 2),
        "net_cash_flow": round(income - expenses, 2),
        "transactions": selected[:_MAX_LIMIT],
        "basis": "persisted financial_transactions; VOID/CANCELLED/DELETED excluded by classifier",
        "source_tables": ["financial_transactions"],
    }


def _feed_summary(factory: RepositoryFactory, window: DateWindow) -> dict[str, Any]:
    rows = factory.feed().get_all() or []
    selected = []
    quantity = 0.0
    cost = 0.0
    for row in rows:
        row_date = _record_date(row, "feeding_date")
        if not _period_filter(window, row_date):
            continue
        quantity += float(getattr(row, "quantity_kg", 0) or 0)
        cost += float(getattr(row, "total_feed_cost", 0) or 0)
        selected.append(
            _sanitised_model_row(
                row,
                (
                    "id",
                    "animal_id",
                    "group_or_pen",
                    "feed_type",
                    "quantity_kg",
                    "feeding_date",
                    "status",
                    "unit_cost_per_kg",
                    "total_feed_cost",
                    "cost_basis",
                    "cost_source_financial_transaction_id",
                ),
            )
        )
    return {
        "metric": "feed_records",
        "feed_record_count": len(selected),
        "quantity_kg": round(quantity, 4),
        "recorded_feed_cost": round(cost, 2),
        "feed_records": selected[:_MAX_LIMIT],
        "basis": "persisted feed_record entries; governed historical COP uses daily TMR snapshots separately",
        "source_tables": ["feed_record", "feed_ration"],
    }


def _animal_summary(factory: RepositoryFactory, window: DateWindow) -> dict[str, Any]:
    rows = factory.animal().get_all() or []
    selected = []
    status_counts: Counter[str] = Counter()
    lifecycle_counts: Counter[str] = Counter()
    for row in rows:
        anchor = _record_date(row, "created_at", "date_of_acquisition", "date_of_birth")
        if window.requested_start is not None and not _period_filter(window, anchor):
            continue
        status_counts[str(getattr(row, "status", "UNKNOWN") or "UNKNOWN").upper()] += 1
        lifecycle_counts[
            str(getattr(row, "lifecycle_status", "UNKNOWN") or "UNKNOWN").upper()
        ] += 1
        selected.append(
            _sanitised_model_row(
                row,
                (
                    "id",
                    "animal_id",
                    "animal_type",
                    "breed",
                    "sex",
                    "date_of_birth",
                    "dam_id",
                    "sire_id",
                    "lifecycle_status",
                    "status",
                    "is_currently_milking",
                    "production_group",
                    "location",
                    "active",
                    "created_at",
                    "updated_at",
                ),
            )
        )
    return {
        "metric": "animal_register",
        "animal_count": len(selected),
        "status_counts": dict(sorted(status_counts.items())),
        "lifecycle_counts": dict(sorted(lifecycle_counts.items())),
        "animals": selected[:_MAX_LIMIT],
        "basis": "persisted animal master records; no animal is deleted to answer a query",
        "source_tables": ["animal"],
    }


def _mortality_summary(
    factory: RepositoryFactory, window: DateWindow
) -> dict[str, Any]:
    events = []
    for row in _event_rows(factory):
        if row.event_type != "OperationalInputReceived":
            continue
        payload = row.payload if isinstance(row.payload, dict) else {}
        if str(payload.get("input_type") or "").lower() != "animal_disposition":
            continue
        business = (
            payload.get("payload")
            if isinstance(payload.get("payload"), dict)
            else payload
        )
        if str(business.get("disposition") or "").upper() != "DECEASED":
            continue
        event_date = _as_date(business.get("effective_date")) or _as_date(row.timestamp)
        if not _period_filter(window, event_date):
            continue
        events.append(
            {
                "event_id": row.event_id,
                "animal_id": business.get("animal_id"),
                "date": event_date.isoformat() if event_date else None,
                "cause": business.get("cause"),
                "reason": business.get("reason"),
            }
        )

    deceased = [
        row
        for row in (factory.animal().get_all() or [])
        if str(getattr(row, "lifecycle_status", "") or "").upper() == "DECEASED"
        or str(getattr(row, "status", "") or "").upper() == "DECEASED"
    ]
    return {
        "metric": "mortality",
        "mortality_events": len(events),
        "mortality_records": events,
        "currently_deceased_animals": len(deceased),
        "basis": "durable animal_disposition events with DECEASED outcome; current master status shown separately",
        "source_tables": ["event_journal", "animal"],
    }


def _health_insight(
    factory: RepositoryFactory,
    question: str,
    window: DateWindow,
    animal_id: str | None = None,
) -> dict[str, Any]:
    observations = []
    lowered = str(question or "").lower()
    history_requested = _health_history_requested(question)
    requested_animal = str(animal_id or "").strip()
    for row in factory.health().get_all() or []:
        if requested_animal and str(getattr(row, "animal_id", "")) != requested_animal:
            continue
        row_date = _record_date(row, "observed_at")
        if not _period_filter(window, row_date):
            continue
        text = " ".join(
            str(getattr(row, field, "") or "")
            for field in ("observation", "symptom", "notes", "severity", "status")
        ).strip()
        if (
            not requested_animal
            and not history_requested
            and lowered
            and not any(
                token in text.lower()
                for token in re.findall(r"[a-z0-9]+", lowered)
                if len(token) > 3
            )
        ):
            continue
        observations.append(
            _sanitised_model_row(
                row,
                (
                    "id",
                    "animal_id",
                    "observed_at",
                    "observation",
                    "symptom",
                    "temperature",
                    "temperature_c",
                    "severity",
                    "status",
                    "notes",
                ),
            )
        )

    treatments = []
    for row in factory.treatment().get_all() or []:
        if requested_animal and str(getattr(row, "animal_id", "")) != requested_animal:
            continue
        row_date = _record_date(row, "treated_at")
        if not _period_filter(window, row_date):
            continue
        treatments.append(
            _sanitised_model_row(
                row,
                (
                    "id",
                    "animal_id",
                    "diagnosis",
                    "medicine",
                    "dose",
                    "treated_at",
                    "milk_withdrawal_days",
                    "milk_withdrawal_until",
                    "withdrawal_source",
                    "notes",
                ),
            )
        )

    cases = []
    for row in factory.health_cases().get_all() or []:
        if requested_animal and str(getattr(row, "animal_id", "")) != requested_animal:
            continue
        row_date = _record_date(row, "opened_at", "resolved_at")
        if not _period_filter(window, row_date):
            continue
        cases.append(
            _sanitised_model_row(
                row,
                (
                    "id",
                    "case_id",
                    "animal_id",
                    "severity",
                    "diagnosis",
                    "notes",
                    "status",
                    "opened_at",
                    "opened_by",
                    "follow_up_due_at",
                    "withdrawal_until",
                    "resolution",
                    "resolved_at",
                    "resolved_by",
                ),
            )
        )

    from dairyos.assistant.knowledge import GroundedAssistant

    disease_candidates = [
        record for record in GroundedAssistant().search_health(question, limit=5)
    ]
    probable_conditions = [
        {
            "condition": record.title,
            "classification": record.clinical_class,
            "assessment": "possible candidate from symptom-pattern retrieval; not a diagnosis",
            "recognition": record.answer,
            "diagnostic_path": record.steps,
            "treatment_guidance": record.clinical_management
            or "Follow the veterinarian-authorised treatment and supportive-care plan.",
            "management_guidance": record.clinical_management
            or record.expanded_explanation,
            "urgent_signs": record.exceptions,
            "review_status": record.review_status,
            "sources": record.source_authority,
        }
        for record in disease_candidates
    ]
    urgent_signs = []
    for candidate in probable_conditions:
        urgent_signs.extend(candidate["urgent_signs"])
    return {
        "metric": "health_insight",
        "history_requested": history_requested,
        "probable_conditions": probable_conditions,
        "persisted_health_observations": observations[:_MAX_LIMIT],
        "matching_observation_count": len(observations),
        "persisted_treatments": treatments[:_MAX_LIMIT],
        "treatment_count": len(treatments),
        "persisted_health_cases": cases[:_MAX_LIMIT],
        "health_case_count": len(cases),
        "urgent_signs": list(dict.fromkeys(urgent_signs))[:20],
        "assessment_boundary": (
            "These are educational differentials grounded in the local disease reference. "
            "A veterinarian must examine the animal, confirm the diagnosis, choose treatment, "
            "set dose and withdrawal, and record the authorised plan."
        ),
        "source_tables": [
            "health_observation",
            "health_cases",
            "treatment_record",
            "disease-reference-catalog.json",
        ],
        "read_only": True,
    }


def _domain_snapshot(factory: RepositoryFactory) -> dict[str, Any]:
    catalog = _database_catalog(factory.session.connection())
    table_counts = {item["table"]: item["row_count"] for item in catalog}
    counts: dict[str, int | None] = {}
    for name, model in _DOMAIN_MODELS.items():
        if isinstance(model, str):
            counts[name] = None
            continue
        counts[name] = table_counts.get(getattr(model, "__tablename__", ""))
    return {
        "metric": "operational_data_catalog",
        "domain_counts": counts,
        "table_counts": table_counts,
        "available_domains": sorted(counts),
        "available_tables": sorted(table_counts),
        "database_scope": "current DairyOS application database",
        "read_only": True,
        "database_read": True,
    }


def _database_catalog(connection) -> list[dict[str, Any]]:
    inspector = sa.inspect(connection)
    schema = "public" if connection.dialect.name == "postgresql" else None
    table_names = inspector.get_table_names(schema=schema)
    catalog = []
    for table_name in sorted(table_names):
        columns = []
        try:
            with connection.begin_nested():
                columns = [
                    column["name"]
                    for column in inspector.get_columns(table_name, schema=schema)
                ]
        except sa.exc.SQLAlchemyError:
            columns = []
        row_count: int | None = None
        try:
            with connection.begin_nested():
                table = sa.Table(
                    table_name,
                    sa.MetaData(),
                    schema=schema,
                    autoload_with=connection,
                )
                row_count = int(
                    connection.execute(
                        sa.select(sa.func.count()).select_from(table)
                    ).scalar_one()
                )
        except sa.exc.SQLAlchemyError:
            row_count = None
        catalog.append(
            {
                "table": table_name,
                "columns": columns,
                "row_count": row_count,
            }
        )
    return catalog


def _table_rows(
    connection, table_name: str, limit: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    catalog = _database_catalog(connection)
    selected = next(
        (
            item
            for item in catalog
            if item["table"].lower() == table_name.strip().lower()
        ),
        None,
    )
    if selected is None:
        raise ValueError(f"Unknown DairyOS database table: {table_name}")
    schema = "public" if connection.dialect.name == "postgresql" else None
    table = sa.Table(
        selected["table"],
        sa.MetaData(),
        schema=schema,
        autoload_with=connection,
    )
    rows = connection.execute(
        sa.select(table).limit(min(max(int(limit), 1), _TABLE_ROW_MAX))
    ).fetchall()
    return selected, [_row_mapping(row) for row in rows]


_TABLE_DATE_FIELDS = (
    "production_date",
    "operational_date",
    "transaction_date",
    "feeding_date",
    "quality_date",
    "observed_at",
    "treated_at",
    "effective_date",
    "event_date",
    "recorded_at",
    "created_at",
    "updated_at",
    "opened_at",
    "raised_at",
    "last_observed_at",
    "purchase_date",
    "payment_date",
    "period_start",
    "measurement_date",
    "weaned_at",
    "timestamp",
    "digest_date",
    "scheduled_at",
)


def _table_date_column(table: sa.Table) -> sa.Column[Any] | None:
    for field in _TABLE_DATE_FIELDS:
        if field in table.c:
            return table.c[field]
    return None


def _table_boundary(column: sa.Column[Any], value: date) -> Any:
    try:
        python_type = column.type.python_type
    except (AttributeError, NotImplementedError):
        python_type = None
    if python_type is date:
        return value
    if python_type is datetime:
        return datetime.combine(value, datetime.min.time())
    return value.isoformat()


def _table_summary(
    connection,
    table_name: str,
    window: DateWindow,
    limit: int,
) -> dict[str, Any]:
    """Return a bounded, date-aware read of one current application table."""
    catalog = _database_catalog(connection)
    selected = next(
        (
            item
            for item in catalog
            if item["table"].lower() == table_name.strip().lower()
        ),
        None,
    )
    if selected is None:
        raise ValueError(f"Unknown DairyOS database table: {table_name}")

    schema = "public" if connection.dialect.name == "postgresql" else None
    table = sa.Table(
        selected["table"],
        sa.MetaData(),
        schema=schema,
        autoload_with=connection,
    )
    date_column = _table_date_column(table)
    if window.is_empty:
        condition = sa.false()
    elif (
        date_column is not None
        and window.effective_start is not None
        and window.effective_end is not None
    ):
        condition = sa.and_(
            date_column >= _table_boundary(date_column, window.effective_start),
            date_column
            < _table_boundary(date_column, window.effective_end + timedelta(days=1)),
        )
    else:
        condition = None

    count_statement = sa.select(sa.func.count()).select_from(table)
    if condition is not None:
        count_statement = count_statement.where(condition)
    record_count = int(connection.execute(count_statement).scalar_one())

    row_statement = sa.select(table)
    if condition is not None:
        row_statement = row_statement.where(condition)
    if date_column is not None:
        row_statement = row_statement.order_by(date_column.asc())
    row_statement = row_statement.limit(min(max(int(limit), 1), _TABLE_ROW_MAX))
    rows = connection.execute(row_statement).fetchall()
    return {
        "metric": "operational_table",
        "table": selected,
        "record_count": record_count,
        "rows": [_row_mapping(row) for row in rows],
        "period_filter_column": date_column.name if date_column is not None else None,
        "period_filter_applied": condition is not None,
        "basis": "current persisted DairyOS table read under a transaction-scoped read-only guard",
        "source_tables": [selected["table"]],
    }


def _multi_table_summary(
    connection,
    table_names: tuple[str, ...],
    window: DateWindow,
    limit: int,
) -> dict[str, Any]:
    summaries = [
        _table_summary(connection, table_name, window, limit)
        for table_name in table_names
    ]
    return {
        "metric": "operational_tables",
        "record_count": sum(item["record_count"] for item in summaries),
        "tables": summaries,
        "source_tables": list(table_names),
        "basis": "bounded reads from the selected current DairyOS tables",
    }


def _event_input_summary(
    factory: RepositoryFactory,
    input_type: str,
    window: DateWindow,
    limit: int,
) -> dict[str, Any]:
    records = []
    for row in _event_rows(factory):
        if row.event_type != "OperationalInputReceived":
            continue
        payload = row.payload if isinstance(row.payload, dict) else {}
        if str(payload.get("input_type") or "").lower() != input_type.lower():
            continue
        business = (
            payload.get("payload")
            if isinstance(payload.get("payload"), dict)
            else payload
        )
        if (
            str(business.get("status") or payload.get("status") or "COMPLETED").upper()
            == "VOID"
        ):
            continue
        event_date = next(
            (
                _as_date(business.get(field))
                for field in (
                    "administered_date",
                    "measurement_date",
                    "weaned_at",
                    "effective_date",
                    "operational_date",
                    "recorded_at",
                )
                if _as_date(business.get(field)) is not None
            ),
            _as_date(row.timestamp),
        )
        if not _period_filter(window, event_date):
            continue
        records.append(
            {
                "event_id": row.event_id,
                "event_date": event_date.isoformat() if event_date else None,
                "payload": _json_safe(payload),
            }
        )
    return {
        "metric": "operational_input_events",
        "input_type": input_type,
        "record_count": len(records),
        "records": records[: min(max(int(limit), 1), _MAX_LIMIT)],
        "basis": "durable OperationalInputReceived events; VOID inputs excluded",
        "source_tables": ["event_journal"],
    }


def _milk_disposition_summary(
    factory: RepositoryFactory, window: DateWindow, limit: int
) -> dict[str, Any]:
    rows = factory.milk_dispositions().get_all() or []
    selected = []
    quantity = 0.0
    amount_due = 0.0
    amount_received = 0.0
    types: Counter[str] = Counter()
    for row in rows:
        if str(getattr(row, "status", "RECORDED") or "RECORDED").upper() == "VOID":
            continue
        row_date = _record_date(row, "production_date", "created_at")
        if not _period_filter(window, row_date):
            continue
        disposition_type = str(
            getattr(row, "disposition_type", "UNKNOWN") or "UNKNOWN"
        ).upper()
        types[disposition_type] += 1
        quantity += float(getattr(row, "quantity_litres", 0) or 0)
        amount_due += float(getattr(row, "amount_due", 0) or 0)
        amount_received += float(getattr(row, "amount_received", 0) or 0)
        selected.append(
            _sanitised_model_row(
                row,
                (
                    "id",
                    "production_date",
                    "disposition_type",
                    "quantity_litres",
                    "sale_id",
                    "counterparty",
                    "selling_price_per_litre",
                    "amount_due",
                    "amount_received",
                    "recorded_by",
                    "status",
                    "created_at",
                ),
            )
        )
    return {
        "metric": "milk_dispositions",
        "record_count": len(selected),
        "quantity_litres": round(quantity, 4),
        "amount_due": round(amount_due, 2),
        "amount_received": round(amount_received, 2),
        "disposition_type_counts": dict(sorted(types.items())),
        "records": selected[: min(max(int(limit), 1), _MAX_LIMIT)],
        "basis": "persisted milk disposition authority; VOID rows excluded",
        "source_tables": ["milk_dispositions"],
    }


def _read_database_schema(
    table_name: str | None = None, limit: int = 50
) -> dict[str, Any]:
    def read(factory: RepositoryFactory) -> dict[str, Any]:
        connection = factory.session.connection()
        catalog = _database_catalog(connection)
        result: dict[str, Any] = {
            "data_status": "LIVE_PERSISTED_DATA",
            "assistant_name": "AI Assistant",
            "metric": "database_schema",
            "database_scope": "current DairyOS application database; credentials and secrets are omitted",
            "read_only": True,
            "database_read": True,
            "tables": catalog,
            "table_count": len(catalog),
        }
        if table_name:
            selected, rows = _table_rows(connection, table_name, limit)
            result["selected_table"] = selected
            result["rows"] = rows
        return result

    return _with_read_only(read)


def _read_operational_data(
    question: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    month: str | int | None = None,
    year: str | int | None = None,
    table_name: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    def read(factory: RepositoryFactory) -> dict[str, Any]:
        today = OperationalDateAuthority(repository_factory=factory).current_date()
        window = _resolve_window(
            question,
            operational_date=today,
            start_date=start_date,
            end_date=end_date,
            month=month,
            year=year,
        )
        result: dict[str, Any] = {
            "data_status": "LIVE_PERSISTED_DATA",
            "assistant_name": "AI Assistant",
            "question": question,
            "period": window.as_dict(),
            "read_only": True,
            "database_read": True,
        }
        if window.is_empty:
            result.update(
                {
                    "data_status": "NO_DATA_IN_REQUESTED_PERIOD",
                    "evidence": {
                        "metric": "operational_period_empty",
                        "record_count": 0,
                        "message": "The requested period contains no completed operational date.",
                        "source_tables": [],
                        "read_only": True,
                    },
                }
            )
            return result
        if table_name:
            summary = _table_summary(
                factory.session.connection(), table_name, window, limit
            )
            result.update(
                {
                    "metric": "database_table",
                    "table": summary["table"],
                    "rows": summary["rows"],
                    "record_count": summary["record_count"],
                    "evidence": summary,
                }
            )
            return result

        lowered = str(question or "").lower()
        if any(
            term in lowered
            for term in ("calf", "calves", "calving", "delivered", "birth")
        ) and any(
            term in lowered
            for term in ("mortality", "mortalities", "died", "death", "deceased")
        ):
            result["evidence"] = {
                "metric": "operational_multi_domain",
                "domains": ["reproduction_and_calf_lifecycle", "mortality"],
                "evidence": [
                    _reproductive_summary(factory, window),
                    _mortality_summary(factory, window),
                ],
                "read_only": True,
                "database_read": True,
                "source_tables": ["breeding_records", "animal", "event_journal"],
            }
        elif any(
            term in lowered
            for term in ("milk", "litre", "liter", "yield", "production")
        ) and any(
            term in lowered
            for term in ("mortality", "mortalities", "died", "death", "deceased")
        ):
            result["evidence"] = {
                "metric": "operational_multi_domain",
                "domains": ["milk_production", "mortality"],
                "evidence": [
                    _milk_summary(factory, window),
                    _mortality_summary(factory, window),
                ],
                "read_only": True,
                "database_read": True,
                "source_tables": ["milk_production", "event_journal", "animal"],
            }
        elif any(
            term in lowered
            for term in ("animal sold", "livestock sold", "animal disposition")
        ):
            result["evidence"] = _event_input_summary(
                factory, "animal_disposition", window, limit
            )
        elif any(
            term in lowered
            for term in ("disposition", "sold", "sale", "wastage", "waste")
        ) and any(
            term in lowered
            for term in ("milk", "litre", "liter", "disposition", "wastage", "waste")
        ):
            result["evidence"] = _milk_disposition_summary(factory, window, limit)
        elif any(
            term in lowered for term in ("milk quality", "fat", "snf", "quality sample")
        ):
            result["evidence"] = _table_summary(
                factory.session.connection(), "milk_quality_samples", window, limit
            )
        elif any(term in lowered for term in ("vaccin",)):
            result["evidence"] = _event_input_summary(
                factory, "vaccination", window, limit
            )
        elif any(
            term in lowered
            for term in (
                "youngstock",
                "young stock",
                "weaning",
                "weight gain",
                "growth",
            )
        ):
            result["evidence"] = _event_input_summary(
                factory,
                "youngstock_weaning" if "weaning" in lowered else "youngstock_growth",
                window,
                limit,
            )
        elif any(
            term in lowered
            for term in ("milk", "litre", "liter", "yield", "production")
        ):
            result["evidence"] = _milk_summary(factory, window)
        elif any(
            term in lowered
            for term in ("calf", "calves", "calving", "delivered", "birth")
        ):
            result["evidence"] = _reproductive_summary(factory, window)
        elif any(
            term in lowered
            for term in ("mortality", "mortalities", "died", "death", "deceased")
        ):
            result["evidence"] = _mortality_summary(factory, window)
        elif any(
            term in lowered
            for term in ("health", "symptom", "treatment", "disease", "diagnos")
        ):
            result["evidence"] = _health_insight(factory, question, window)
        elif any(
            term in lowered
            for term in ("inventory", "feed inventory", "stock level", "reorder")
        ):
            result["evidence"] = _multi_table_summary(
                factory.session.connection(),
                ("inventory_transactions", "feed_inventory_items"),
                window,
                limit,
            )
        elif any(
            term in lowered
            for term in ("finance", "financial", "expense", "income", "cash", "opex")
        ):
            result["evidence"] = _finance_summary(factory, window)
        elif any(
            term in lowered for term in ("feed", "feeding", "ration", "tmr", "forage")
        ):
            result["evidence"] = _feed_summary(factory, window)
        elif any(
            term in lowered for term in ("animal", "herd", "cow", "cattle", "livestock")
        ):
            result["evidence"] = _animal_summary(factory, window)
        elif any(term in lowered for term in ("inventory", "stock level", "reorder")):
            result["evidence"] = _table_summary(
                factory.session.connection(), "inventory_transactions", window, limit
            )
        elif any(
            term in lowered
            for term in ("equipment", "maintenance", "service event", "repair")
        ):
            result["evidence"] = _multi_table_summary(
                factory.session.connection(),
                ("equipment", "equipment_service_events"),
                window,
                limit,
            )
        elif any(term in lowered for term in ("payroll", "workforce", "employee")):
            result["evidence"] = _table_summary(
                factory.session.connection(), "payroll_record", window, limit
            )
        elif any(term in lowered for term in ("semen", "bull", "semen lot")):
            result["evidence"] = _multi_table_summary(
                factory.session.connection(),
                ("semen_lots", "semen_stock_movements"),
                window,
                limit,
            )
        elif any(
            term in lowered
            for term in (
                "finding",
                "alert history",
                "watchlist history",
                "operational finding",
            )
        ):
            result["evidence"] = _multi_table_summary(
                factory.session.connection(),
                ("operational_findings", "operational_finding_lifecycle_events"),
                window,
                limit,
            )
        elif any(
            term in lowered
            for term in ("breeding", "pregnancy", "insemination", "calving")
        ):
            result["evidence"] = _reproductive_summary(factory, window)
        else:
            result["evidence"] = _domain_snapshot(factory)
        snapshot = _domain_snapshot(factory)
        result["catalog"] = snapshot["domain_counts"]
        result["table_counts"] = snapshot["table_counts"]
        return result

    return _with_read_only(read)


def _read_cop_metrics(
    question: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    month: str | int | None = None,
    year: str | int | None = None,
) -> dict[str, Any]:
    def read(factory: RepositoryFactory) -> dict[str, Any]:
        today = OperationalDateAuthority(repository_factory=factory).current_date()
        window = _resolve_window(
            question,
            operational_date=today,
            start_date=start_date,
            end_date=end_date,
            month=month,
            year=year,
            completed_only=True,
            default_to_month=True,
        )
        if window.effective_start is None or window.effective_end is None:
            return {
                "data_status": "NO_COMPLETED_PERIOD",
                "status": "NO_COMPLETED_PERIOD",
                "period": window.as_dict(),
                "period_cop_per_litre": None,
                "average_daily_cop_per_litre": None,
                "maximum_daily_cop_per_litre": None,
                "read_only": True,
                "database_read": True,
                "source_tables": [
                    "milk_production",
                    "feed_ration",
                    "financial_transactions",
                ],
            }

        container = SimpleNamespace(repository_factory=factory)
        aggregate = get_integrated_coml(
            period_start=window.effective_start,
            period_end=window.effective_end,
            allow_current_period=False,
            container=container,
        )
        daily = []
        missing_authority_days: list[str] = []
        no_milk_days: list[str] = []
        day = window.effective_start
        while day <= window.effective_end:
            item = get_integrated_coml(
                period_start=day,
                period_end=day,
                allow_current_period=False,
                container=container,
            )
            costs = item.get("costs", {})
            litres = float(item.get("production", {}).get("totalLiters") or 0.0)
            cop = costs.get("total_coml_per_liter")
            feed_source = costs.get("feed_source") or {}
            missing = list(feed_source.get("missing_authority_days") or [])
            if missing:
                missing_authority_days.extend(missing)
            if litres <= 0:
                no_milk_days.append(day.isoformat())
            daily.append(
                {
                    "date": day.isoformat(),
                    "milk_litres": round(litres, 4),
                    "feed_cost_per_litre": costs.get("feed_cost_per_liter"),
                    "opex_cost_per_litre": costs.get("opex_cost_per_liter"),
                    "cop_per_litre": cop,
                    "status": (
                        "MISSING_COST_AUTHORITY"
                        if missing
                        else "NO_MILK"
                        if litres <= 0
                        else "CALCULATED"
                    ),
                    "missing_authority_days": missing,
                }
            )
            day += timedelta(days=1)

        valid_daily = [
            item
            for item in daily
            if item["status"] == "CALCULATED" and item["cop_per_litre"] is not None
        ]
        daily_values = [float(item["cop_per_litre"]) for item in valid_daily]
        unique_missing = sorted(set(missing_authority_days))
        if unique_missing:
            status = "INCOMPLETE_COST_AUTHORITY"
        elif aggregate.get("total_coml_per_liter") is None:
            status = "NO_MILK_DATA"
        else:
            status = "OK"
        return {
            "data_status": status,
            "status": status,
            "period": window.as_dict(),
            "period_cop_per_litre": aggregate.get("total_coml_per_liter"),
            "period_feed_cost_per_litre": aggregate.get("feed_cost_per_liter"),
            "period_opex_cost_per_litre": aggregate.get("opex_cost_per_liter"),
            "period_milk_litres": aggregate.get("production", {}).get("totalLiters"),
            "average_daily_cop_per_litre": (
                round(sum(daily_values) / len(daily_values), 4)
                if daily_values
                else None
            ),
            "maximum_daily_cop_per_litre": round(max(daily_values), 4)
            if daily_values
            else None,
            "minimum_daily_cop_per_litre": round(min(daily_values), 4)
            if daily_values
            else None,
            "valid_daily_days": len(valid_daily),
            "missing_authority_days": unique_missing,
            "no_milk_days": no_milk_days,
            "daily": daily,
            "calculation_basis": (
                "period COP is the governed weighted ratio of TMR whole-herd feed cost plus attributed Finance OPEX "
                "to authoritative milk litres; average and maximum are arithmetic statistics over complete daily COP rows"
            ),
            "source_tables": [
                "milk_production",
                "feed_ration",
                "financial_transactions",
                "app_settings",
                "coml_records",
            ],
            "read_only": True,
            "database_read": True,
        }

    return _with_read_only(read)


def _file_log_paths() -> list[Path]:
    candidates = [logs_dir(create=False)]
    configured = os.environ.get("DAIRYOS_BACKEND_LOG", "").strip()
    if configured:
        candidates.append(Path(configured).expanduser())
    configured_dir = os.environ.get("DAIRYOS_RUNTIME_LOG_DIR", "").strip()
    if configured_dir:
        candidates.append(Path(configured_dir).expanduser())
    result: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_dir():
            paths = sorted(
                (
                    item
                    for item in resolved.iterdir()
                    if item.is_file()
                    and item.suffix.lower() in {".log", ".txt", ".jsonl"}
                ),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )[:8]
        elif resolved.is_file():
            paths = [resolved]
        else:
            paths = []
        for path in paths:
            key = str(path).lower()
            if key not in seen:
                seen.add(key)
                result.append(path)
    return result[:12]


def _tail_file(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > _FILE_LOG_MAX_BYTES:
                handle.seek(-_FILE_LOG_MAX_BYTES, os.SEEK_END)
            content = handle.read(_FILE_LOG_MAX_BYTES).decode("utf-8", errors="replace")
    except OSError as exc:
        return {"path": str(path), "available": False, "error": type(exc).__name__}
    lines = content.splitlines()[-80:]
    redacted = []
    for line in lines:
        safe = re.sub(
            r"(?i)(password|secret|token|api[_-]?key|credential)(\s*[:=]\s*)[^\s,;]+",
            r"\1\2[REDACTED]",
            line,
        )
        redacted.append(safe[:_FILE_LOG_LINE_MAX])
    return {
        "path": str(path),
        "available": True,
        "bytes_read": len(content.encode("utf-8")),
        "lines": redacted,
    }


def _read_operational_logs(
    question: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    def read(factory: RepositoryFactory) -> dict[str, Any]:
        today = OperationalDateAuthority(repository_factory=factory).current_date()
        window = _resolve_window(
            question,
            operational_date=today,
            start_date=start_date,
            end_date=end_date,
        )
        selected_limit = min(max(int(limit), 1), _MAX_LIMIT)
        journal = []
        for row in (
            factory.session.query(EventJournalModel)
            .order_by(EventJournalModel.id.desc())
            .limit(selected_limit * 2)
            .all()
        ):
            if window.requested_start is not None and not window.contains(
                _as_date(row.timestamp)
            ):
                continue
            journal.append(
                {
                    "id": row.id,
                    "event_id": row.event_id,
                    "event_type": row.event_type,
                    "timestamp": _json_safe(row.timestamp),
                    "payload": _json_safe(row.payload),
                }
            )
            if len(journal) >= selected_limit:
                break
        operational = []
        for row in (
            factory.session.query(OperationalEventModel)
            .order_by(OperationalEventModel.id.desc())
            .limit(selected_limit * 2)
            .all()
        ):
            if window.requested_start is not None and not window.contains(
                _as_date(row.created_at)
            ):
                continue
            operational.append(
                {
                    "id": row.id,
                    "event_type": row.event_type,
                    "source": row.source,
                    "description": _json_safe(row.description),
                    "created_at": _json_safe(row.created_at),
                }
            )
            if len(operational) >= selected_limit:
                break
        outbox = [
            {
                "id": row.id,
                "request_id": row.request_id,
                "journal_id": row.journal_id,
                "status": row.status,
                "attempts": row.attempts,
                "last_error": _json_safe(row.last_error, context_key="last_error"),
                "created_at": _json_safe(row.created_at),
                "delivered_at": _json_safe(row.delivered_at),
            }
            for row in (
                factory.session.query(OperationalProjectionOutbox)
                .order_by(OperationalProjectionOutbox.id.desc())
                .limit(selected_limit)
                .all()
            )
        ]
        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "assistant_name": "AI Assistant",
            "period": window.as_dict(),
            "database_logs": {
                "event_journal": journal,
                "operational_events": operational,
                "projection_outbox": outbox,
            },
            "file_logs": [_tail_file(path) for path in _file_log_paths()],
            "read_only": True,
            "database_read": True,
            "source_tables": [
                "event_journal",
                "operational_events",
                "operational_projection_outbox",
            ],
        }

    return _with_read_only(read)


def read_operational_data(**kwargs: Any) -> dict[str, Any]:
    return _read_operational_data(**kwargs)


def read_cop_metrics(**kwargs: Any) -> dict[str, Any]:
    return _read_cop_metrics(**kwargs)


def read_health_insight(**kwargs: Any) -> dict[str, Any]:
    question = str(kwargs.get("question") or "")
    animal_id = kwargs.get("animal_id")

    def read(factory: RepositoryFactory) -> dict[str, Any]:
        today = OperationalDateAuthority(repository_factory=factory).current_date()
        window = _resolve_window(
            question,
            operational_date=today,
            start_date=kwargs.get("start_date"),
            end_date=kwargs.get("end_date"),
            month=kwargs.get("month"),
            year=kwargs.get("year"),
        )
        result = _health_insight(factory, question, window, animal_id=animal_id)
        result["period"] = window.as_dict()
        result["question"] = question
        result["animal_id"] = animal_id
        result["data_status"] = "LIVE_PERSISTED_DATA"
        return result

    return _with_read_only(read)


def read_operational_logs(**kwargs: Any) -> dict[str, Any]:
    return _read_operational_logs(**kwargs)


def read_database_schema(**kwargs: Any) -> dict[str, Any]:
    return _read_database_schema(**kwargs)


def operational_capability_catalog() -> dict[str, Any]:
    return {
        "assistant_name": "AI Assistant",
        "read_only": True,
        "database_read": True,
        "capabilities": [
            "current operational data across the DairyOS application database",
            "canonical milk production and period summaries",
            "feed, Finance OPEX and governed COP/L calculations",
            "breeding, calving, calf lifecycle and mortality evidence",
            "persisted health observations and treatment history",
            "persisted health cases, vaccination and other operational input history",
            "milk quality, disposition/sales, inventory, equipment, payroll and breeding data",
            "database schema, all current table counts and bounded table rows",
            "persistent event journal, operational events, projection outbox and local log files",
        ],
        "safety": "All operational reads use a transaction-scoped database read-only guard; credentials and secrets are redacted.",
    }
