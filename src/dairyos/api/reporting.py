"""Governed read-only Reporting API for DairyOS.

Reporting is a projection layer only. It reads the same repositories used by
operator workflows, preserves audit rows, and never invents missing values.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator, model_validator

from dairyos.api.dependencies import get_container
from dairyos.api.reporting_animal_passport import animal_passport_dataset
from dairyos.api.reporting_export import csv_bytes, pdf_bytes, xlsx_bytes
from dairyos.api.reporting_milk import milk_reporting_dataset
from dairyos.api.reporting_milk_quality import milk_quality_reporting_dataset
from dairyos.api.reporting_tmr import tmr_reporting_dataset
from dairyos.farm.herd.services.animal_classification_service import (
    AnimalClassificationError,
    AnimalClassificationService,
)
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
from dairyos.finance.classification.transaction_classifier import (
    is_active as finance_is_active,
    is_expense as finance_is_expense,
    is_income as finance_is_income,
)

router = APIRouter(prefix="/farm/reporting", tags=["Reporting"])

DomainKey = Literal[
    "ANIMALS", "MILK", "MILK_QUALITY", "FEED", "FINANCE", "BREEDING",
    "HEALTH", "VACCINATION", "COML", "WHOLE_FARM",
]
PeriodMode = Literal[
    "TODAY", "YESTERDAY", "OPERATIONAL_DATE", "CURRENT_HERD", "AS_OF_DATE",
    "DATE_RANGE", "MONTH", "CUSTOM_PERIOD", "CURRENT_YEAR", "SNAPSHOT_DATE",
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
    historical_capability: Literal["CURRENT_ONLY", "HISTORICAL", "SNAPSHOT"]


def _report(report_id: str, domain: DomainKey, name: str, authority: str, period_modes: tuple[PeriodMode, ...], filters: tuple[str, ...], permissions: tuple[str, ...], historical: Literal["CURRENT_ONLY", "HISTORICAL", "SNAPSHOT"] = "HISTORICAL", scope: str = "Uses governed DairyOS persistence authority.") -> ReportDefinition:
    return ReportDefinition(id=report_id, domain=domain, name=name, authority=authority, period_modes=period_modes, filters=filters, scope_note=scope, required_permissions=permissions, historical_capability=historical)


REPORTS: tuple[ReportDefinition, ...] = (
    _report("animal-register", "ANIMALS", "Animal Register", "Animal master records, lifecycle status, disposition history, and governed category mapping.", ("CURRENT_HERD",), ("category", "status", "breed_code", "production_phase", "herd_composition"), ("animals.view",), "CURRENT_ONLY", "Supports the current herd across all six canonical DairyOS categories."),
    _report("animal-population", "ANIMALS", "Animal Population by Category", "Animal category authority with active/inactive disposition semantics.", ("CURRENT_HERD",), ("status",), ("animals.view",), "CURRENT_ONLY", "Counts the current herd using canonical singular categories and plural herd totals."),
    _report("animal-lifecycle", "ANIMALS", "Animal Entry / Lifecycle Report", "Animal registration, acquisition, lifecycle, disposition, and operational event records.", ("DATE_RANGE", "CUSTOM_PERIOD"), ("category", "event_type"), ("animals.view",)),
    _report("animal-passport", "ANIMALS", "Individual Animal Passport", "Lifetime Animal Passport read model and animal-scoped operational histories.", ("AS_OF_DATE", "CURRENT_HERD"), ("animal_id",), ("animals.view",)),
    _report("daily-milk", "MILK", "Daily Milk Production", "Milk production rows, milking session records, corrections, and disposition authority.", ("TODAY", "YESTERDAY", "OPERATIONAL_DATE", "DATE_RANGE"), ("session", "category", "animal_id", "milking_cohort"), ("milk.view",), scope="Keeps MORNING, AFTERNOON, EVENING, and all-session views distinct."),
    _report("milk-animal", "MILK", "Milk Production by Animal", "Per-animal milk production and milking-frequency history.", ("DATE_RANGE", "MONTH", "CUSTOM_PERIOD"), ("animal_id", "milking_cohort"), ("milk.view",), scope="Prevents misleading comparison of twice- and thrice-milked animals."),
    _report("milk-disposition", "MILK", "Milk Disposition / Reconciliation", "Milk production and sold/domestic/calf/wastage/withdrawal disposition authority.", ("DATE_RANGE", "MONTH"), ("disposition_type", "status"), ("milk.view",)),
    _report("milk-quality-log", "MILK_QUALITY", "Milk Quality Log", "Milk quality samples with recorded status, operator, timestamps, and revision history.", ("DATE_RANGE", "OPERATIONAL_DATE", "MONTH"), ("sample_type", "status", "milk_quality_threshold", "scc_alert", "antibiotic_flag", "temp_breach", "adulteration_suspect"), ("milk.view",)),
    _report("quality-summary", "MILK_QUALITY", "Milk Quality Summary", "Recorded milk quality samples and governed summary calculations.", ("DATE_RANGE", "MONTH"), ("sample_type",), ("milk.view",)),
    _report("current-tmr", "FEED", "Current TMR", "Governed TMR ration and feed records with Finance-backed pricing where available.", ("CURRENT_HERD", "OPERATIONAL_DATE"), ("category", "ingredient"), ("feed.view",)),
    _report("historical-tmr", "FEED", "Historical TMR / Feed Cost", "Historical feed ration and feed-record authority.", ("AS_OF_DATE", "DATE_RANGE"), ("category", "ingredient"), ("feed.view",)),
    _report("finance-ledger", "FINANCE", "Transaction Ledger", "Finance ledger, canonical classifier, settlement status, VOID rules, and COP attribution.", ("DATE_RANGE", "MONTH", "CUSTOM_PERIOD"), ("transaction_type", "status", "category", "counterparty"), ("finance.view",), scope="VOID rows remain available for audit while excluded from active totals."),
    _report("financial-summary", "FINANCE", "Income and Expense Summary", "Governed Finance calculations and canonical transaction classifier.", ("DATE_RANGE", "MONTH", "CURRENT_YEAR"), ("category", "payment_state"), ("finance.view",)),
    _report("breeding-cycle", "BREEDING", "Reproductive Cycle History", "Breeding lifecycle records, cycle attribution, PD results, pregnancy loss, and calving events.", ("DATE_RANGE", "AS_OF_DATE"), ("animal_id", "technician", "event_type"), ("breeding.view",)),
    _report("breeding-performance", "BREEDING", "Pregnancy and AI Performance", "Cycle-aware breeding records and semen usage links.", ("DATE_RANGE", "CUSTOM_PERIOD"), ("technician", "semen_type", "semen_lot"), ("breeding.view",), scope="Does not infer pregnancy success when cycle attribution is absent."),
    _report("health-cases", "HEALTH", "Health Cases and Treatments", "Health cases, observations, treatments, withdrawal references, and animal IDs.", ("DATE_RANGE", "AS_OF_DATE"), ("animal_id", "case_status", "severity"), ("health.view",)),
    _report("withdrawal", "HEALTH", "Withdrawal Periods", "Treatment records and persisted milk-withdrawal authority.", ("OPERATIONAL_DATE", "DATE_RANGE"), ("animal_id", "status"), ("health.view",)),
    _report("vaccination-schedule", "VACCINATION", "Vaccination Schedule and Due Status", "Vaccination records, administered state, schedule rows, due and overdue dates.", ("OPERATIONAL_DATE", "DATE_RANGE", "CUSTOM_PERIOD"), ("animal_id", "vaccine", "schedule_status"), ("health.view",)),
    _report("coml-period", "COML", "Period COML / COP", "Locked COML records, historical feed authority, milk denominator, and Finance OPEX attribution.", ("MONTH", "CUSTOM_PERIOD"), ("lock_status", "cost_component"), ("coml.view",)),
    _report("whole-farm-snapshot", "WHOLE_FARM", "Complete Farm Snapshot", "Cross-domain authoritative projections as of the selected operational date.", ("SNAPSHOT_DATE",), ("major_sections",), ("animals.view", "milk.view", "feed.view", "finance.view", "breeding.view", "health.view", "coml.view", "analytics.view"), "SNAPSHOT"),
)
REPORT_BY_ID = {report.id: report for report in REPORTS}


class ReportingRequest(BaseModel):
    report_id: str = Field(min_length=1)
    domain: DomainKey
    period_mode: PeriodMode
    operational_date: date | None = None
    as_of_date: date | None = None
    snapshot_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    filters: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    selected_columns: list[str] | None = None

    @field_validator("report_id")
    @classmethod
    def normalize_report_id(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_report_contract(self):
        definition = REPORT_BY_ID.get(self.report_id)
        if definition is None:
            raise ValueError(f"Unknown report_id: {self.report_id}")
        if self.domain != definition.domain:
            raise ValueError("domain does not match the selected report")
        if self.period_mode not in definition.period_modes:
            raise ValueError("period_mode is not supported by the selected report")
        if self.start_date is not None and self.end_date is not None and self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        if self.period_mode in {"DATE_RANGE", "CUSTOM_PERIOD"} and (self.start_date is None or self.end_date is None):
            raise ValueError("start_date and end_date are required for the selected period_mode")
        if self.period_mode == "AS_OF_DATE" and self.as_of_date is None:
            raise ValueError("as_of_date is required for AS_OF_DATE")
        if self.period_mode == "OPERATIONAL_DATE" and self.operational_date is None:
            raise ValueError("operational_date is required for OPERATIONAL_DATE")
        if self.period_mode == "SNAPSHOT_DATE" and self.snapshot_date is None:
            raise ValueError("snapshot_date is required for SNAPSHOT_DATE")
        unsupported = sorted(set(self.filters) - set(definition.filters))
        if unsupported:
            raise ValueError("Unsupported filter(s) for report: " + ", ".join(unsupported))
        if self.selected_columns is not None:
            self.selected_columns = [str(column).strip() for column in self.selected_columns if str(column).strip()]
            if not self.selected_columns:
                raise ValueError("At least one Reporting column must be selected")
            if len(self.selected_columns) != len(set(self.selected_columns)):
                raise ValueError("Selected Reporting columns must be unique")
        return self


def reporting_permission_for_request(report_id: str | None) -> str | None:
    if not report_id:
        return "settings.view"
    definition = REPORT_BY_ID.get(str(report_id).strip().lower())
    if definition is None or len(definition.required_permissions) != 1:
        return "settings.view"
    return definition.required_permissions[0]


def _resolved_period(request: ReportingRequest, *, operational_today: date) -> dict[str, str | None]:
    if request.period_mode == "TODAY": start = end = operational_today
    elif request.period_mode == "YESTERDAY": start = end = operational_today - timedelta(days=1)
    elif request.period_mode == "OPERATIONAL_DATE": start = end = request.operational_date
    elif request.period_mode in {"DATE_RANGE", "CUSTOM_PERIOD"}: start, end = request.start_date, request.end_date
    elif request.period_mode == "AS_OF_DATE": start, end = None, request.as_of_date
    elif request.period_mode == "SNAPSHOT_DATE": start, end = None, request.snapshot_date
    elif request.period_mode == "CURRENT_HERD": start, end = None, operational_today
    elif request.period_mode == "MONTH":
        selected = request.as_of_date or request.operational_date or operational_today
        start = selected.replace(day=1)
        next_month = date(selected.year + 1, 1, 1) if selected.month == 12 else date(selected.year, selected.month + 1, 1)
        end = next_month - timedelta(days=1)
    elif request.period_mode == "CURRENT_YEAR": start, end = date(operational_today.year, 1, 1), date(operational_today.year, 12, 31)
    else: raise HTTPException(status_code=422, detail="Unsupported Reporting period mode.")
    as_of = end or operational_today
    return {"start_date": start.isoformat() if start else None, "end_date": end.isoformat() if end else None, "as_of_date": as_of.isoformat()}


TERMINAL_ANIMAL_LIFECYCLE_STATUSES = {"SOLD", "CULLED", "DECEASED"}
ANIMAL_CATEGORY_ORDER = ("Milking", "Dry", "Heifer", "Female Calf", "Male Calf", "Bull")
ANIMAL_CATEGORY_TOTAL_LABELS = {"Milking": "Milking Cows", "Dry": "Dry Cows", "Heifer": "Heifers", "Female Calf": "Female Calves", "Male Calf": "Male Calves", "Bull": "Bulls"}
ANIMAL_CATEGORY_FILTER_ALIASES = {"MILKING": "Milking", "MILKING COW": "Milking", "MILKING COWS": "Milking", "DRY": "Dry", "DRY COW": "Dry", "DRY COWS": "Dry", "HEIFER": "Heifer", "HEIFERS": "Heifer", "FEMALE CALF": "Female Calf", "FEMALE CALVES": "Female Calf", "MALE CALF": "Male Calf", "MALE CALVES": "Male Calf", "BULL": "Bull", "BULLS": "Bull"}


def _text_or_none(value: Any) -> str | None:
    if value is None: return None
    text = str(value).strip()
    return text or None


def _plain_date(value: Any) -> date | None:
    if isinstance(value, datetime): return value.date()
    if isinstance(value, date): return value
    if isinstance(value, str):
        try: return date.fromisoformat(value[:10])
        except ValueError: return None
    return None


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)): return value
    if isinstance(value, Decimal): return float(value)
    if isinstance(value, Enum): return value.value
    if isinstance(value, (date, datetime)): return value.isoformat()
    return str(value)


def _row(record: Any) -> dict[str, Any]:
    if isinstance(record, dict): return {str(key): _json_value(value) for key, value in record.items() if not str(key).startswith("_")}
    values = vars(record) if hasattr(record, "__dict__") else {}
    return {str(key): _json_value(value) for key, value in values.items() if not str(key).startswith("_")}


def _record_date(record: Any) -> date | None:
    for field in ("production_date", "transaction_date", "effective_date", "operational_date", "event_date", "date", "timestamp", "recorded_at", "sample_date", "month_start", "treated_at", "administered_date", "due_date", "next_due_date", "created_at", "updated_at"):
        selected = _plain_date(getattr(record, field, None))
        if selected is not None: return selected
    return None


def _period_dates(payload: ReportingRequest, operational_today: date) -> tuple[date | None, date | None]:
    period = _resolved_period(payload, operational_today=operational_today)
    return _plain_date(period["start_date"]), _plain_date(period["end_date"])


def _in_period(record: Any, start: date | None, end: date | None) -> bool:
    selected = _record_date(record)
    if selected is None: return start is None and end is None
    if start is not None and selected < start: return False
    if end is not None and selected > end: return False
    return True


def _matches(record: Any, aliases: dict[str, tuple[str, ...]], filters: dict[str, Any]) -> bool:
    for filter_name, fields in aliases.items():
        wanted = filters.get(filter_name)
        if wanted is None or str(wanted).strip().upper() == "ALL": continue
        actual = None
        for field in fields:
            candidate = getattr(record, field, None)
            if candidate is not None:
                actual = candidate
                break
        if str(actual or "").strip().upper() != str(wanted).strip().upper(): return False
    return True


def _repo(container: Any, name: str) -> Any:
    factory = getattr(container, "repository_factory", None)
    getter = getattr(factory, name, None) if factory is not None else None
    if callable(getter): return getter()
    return getattr(container, name, None)


def _repo_records(container: Any, name: str) -> list[Any]:
    repository = _repo(container, name)
    getter = getattr(repository, "get_all", None)
    if not callable(getter):
        raise HTTPException(status_code=503, detail={"code": "REPORTING_AUTHORITY_UNAVAILABLE", "repository": name, "message": f"Authoritative Reporting repository '{name}' cannot list records."})
    return list(getter() or [])


def _dataset(rows: list[dict[str, Any]], *, summary: dict[str, Any] | None = None, status: str = "AUTHORITATIVE_DATASET", warnings: list[str] | None = None) -> dict[str, Any]:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns: columns.append(key)
    return {"dataset_status": status, "authority_status": "AUTHORITY_AVAILABLE", "columns": columns, "rows": rows, "summary": summary or {}, "warnings": warnings or []}


def _project_dataset(dataset: dict[str, Any], selected_columns: list[str] | None) -> dict[str, Any]:
    if selected_columns is None:
        return dataset
    available = list(dataset.get("columns") or [])
    unsupported = [column for column in selected_columns if column not in available]
    if unsupported:
        raise HTTPException(status_code=422, detail="Unsupported Reporting column(s): " + ", ".join(unsupported))
    projected = dict(dataset)
    projected["columns"] = list(selected_columns)
    projected["rows"] = [{column: row.get(column) for column in selected_columns} for row in dataset.get("rows", [])]
    return projected


def _classify_current_animal(animal: Any) -> str | None:
    lifecycle = _text_or_none(getattr(animal, "lifecycle_status", None))
    if lifecycle and lifecycle.upper() in TERMINAL_ANIMAL_LIFECYCLE_STATUSES: return None
    try: classification = AnimalClassificationService.classify(lifecycle, getattr(animal, "sex", None))
    except AnimalClassificationError as exc:
        raise HTTPException(status_code=409, detail={"code": "ANIMAL_REPORTING_AUTHORITY_INTEGRITY_ERROR", "animal_id": _text_or_none(getattr(animal, "animal_id", None)) or "<unknown>", "message": str(exc)}) from exc
    category = classification.category.value
    return category if category in ANIMAL_CATEGORY_ORDER else None


def _current_animal_rows(payload: ReportingRequest, *, container: Any) -> list[dict[str, Any]]:
    repository = getattr(container, "animal_repository", None) or _repo(container, "animal")
    getter = getattr(repository, "get_all", None)
    if not callable(getter): raise HTTPException(status_code=503, detail="Authoritative Animal repository cannot list animals.")
    category_filter = payload.filters.get("category")
    canonical_filter = None
    if category_filter is not None:
        canonical_filter = ANIMAL_CATEGORY_FILTER_ALIASES.get(str(category_filter).strip().upper())
        if canonical_filter is None: raise HTTPException(status_code=422, detail="Unsupported Animal Reporting category filter.")
    rows: list[dict[str, Any]] = []
    for animal in list(getter() or []):
        category = _classify_current_animal(animal)
        if category is None or (canonical_filter is not None and category != canonical_filter): continue
        wanted_status = payload.filters.get("status")
        if wanted_status is not None and str(getattr(animal, "status", "")).upper() != str(wanted_status).upper(): continue
        for filter_name, field_name in (("breed_code", "breed_code"), ("production_phase", "production_phase_dim")):
            wanted = payload.filters.get(filter_name)
            if wanted is not None and str(getattr(animal, field_name, "")).upper() != str(wanted).upper(): continue
        herd = str(payload.filters.get("herd_composition") or "").upper()
        herd_categories = {"LACTATING_HERD": {"Milking"}, "DRY_ONLY": {"Dry"}, "HEIFER_YOUNG_STOCK": {"Heifer", "Female Calf", "Male Calf"}}
        if herd in herd_categories and category not in herd_categories[herd]: continue
        data = _row(animal); data["category"] = category; rows.append(data)
    rows.sort(key=lambda item: str(item.get("animal_id") or ""))
    return rows


def _animal_dataset(payload: ReportingRequest, container: Any) -> dict[str, Any]:
    rows = _current_animal_rows(payload, container=container)
    counts = {category: 0 for category in ANIMAL_CATEGORY_ORDER}
    for row in rows: counts[row["category"]] += 1
    herd_totals = {ANIMAL_CATEGORY_TOTAL_LABELS[category]: counts[category] for category in ANIMAL_CATEGORY_ORDER}
    output = [{"category": category, "herd_total_label": ANIMAL_CATEGORY_TOTAL_LABELS[category], "count": counts[category]} for category in ANIMAL_CATEGORY_ORDER] if payload.report_id == "animal-population" else rows
    return _dataset(output, summary={"total_current_animals": len(rows), "category_counts": counts, "herd_totals": herd_totals}, status="AUTHORITATIVE_CURRENT_DATASET", warnings=[] if rows else ["No current Animal Register records match the selected filters."])


def _generic_repo_dataset(payload: ReportingRequest, container: Any, operational_today: date, repo_name: str, aliases: dict[str, tuple[str, ...]]) -> dict[str, Any]:
    start, end = _period_dates(payload, operational_today)
    records = [record for record in _repo_records(container, repo_name) if _in_period(record, start, end) and _matches(record, aliases, payload.filters)]
    return _dataset([_row(record) for record in records], summary={"records": len(records)})


def _milk_dataset(payload: ReportingRequest, container: Any, operational_today: date) -> dict[str, Any]:
    start, end = _period_dates(payload, operational_today); records = _repo_records(container, "milk"); animal_filter = payload.filters.get("animal_id"); session = str(payload.filters.get("session") or "ALL").strip().upper(); session_fields = {"MORNING": "morning_yield", "AFTERNOON": "afternoon_yield", "EVENING": "evening_yield"}; rows=[]; active_total=0.0
    for record in records:
        if not _in_period(record, start, end): continue
        if animal_filter is not None and str(getattr(record, "animal_id", "")) != str(animal_filter): continue
        data = _row(record)
        if session in session_fields:
            field=session_fields[session]; data["selected_session"]=session; data["selected_session_yield"]=_json_value(getattr(record, field, None))
        status=str(getattr(record,"status","RECORDED") or "RECORDED").upper()
        if status != "VOID":
            value=getattr(record,session_fields[session],None) if session in session_fields else getattr(record,"total_yield",None)
            if value is not None: active_total += float(value)
        rows.append(data)
    return _dataset(rows, summary={"active_milk_liters":active_total,"records":len(rows),"session":session})


def _finance_dataset(payload: ReportingRequest, container: Any, operational_today: date) -> dict[str, Any]:
    start,end=_period_dates(payload,operational_today); aliases={"transaction_type":("transaction_type","type"),"status":("status",),"category":("category","master_category","sub_category"),"counterparty":("counterparty",),"payment_state":("payment_state","settlement_status")}; records=[record for record in _repo_records(container,"finance") if _in_period(record,start,end) and _matches(record,aliases,payload.filters)]; income=sum(float(getattr(record,"amount",0) or 0) for record in records if finance_is_income(record)); expense_records=[record for record in records if finance_is_expense(record)]; operating_expense=sum(float(getattr(record,"amount",0) or 0) for record in expense_records if str(getattr(record,"master_category","") or "").strip().upper()=="OPEX" and str(getattr(record,"cop_classification","") or "").strip().upper()!="NON_OPEX"); non_operating_expense=sum(float(getattr(record,"amount",0) or 0) for record in expense_records if str(getattr(record,"master_category","") or "").strip().upper()=="NON_OPEX" or str(getattr(record,"cop_classification","") or "").strip().upper()=="NON_OPEX"); active=sum(1 for record in records if finance_is_active(record)); summary={"operating_income":income,"operating_expenses":operating_expense,"non_operating_expenses":non_operating_expense,"operating_net":income-operating_expense,"active_records":active,"audit_records":len(records)}; rows=[{"metric":key,"amount":value} for key,value in summary.items() if key in {"operating_income","operating_expenses","operating_net"}] if payload.report_id=="financial-summary" else [_row(record) for record in records]; return _dataset(rows,summary=summary)


def _snapshot_child(report_id: str, domain: DomainKey, mode: PeriodMode, selected: date) -> ReportingRequest:
    kwargs: dict[str,Any]={}
    if mode=="OPERATIONAL_DATE": kwargs["operational_date"]=selected
    elif mode=="DATE_RANGE": kwargs["start_date"]=selected; kwargs["end_date"]=selected
    elif mode=="AS_OF_DATE": kwargs["as_of_date"]=selected
    return ReportingRequest(report_id=report_id,domain=domain,period_mode=mode,**kwargs)


def _canonical_dataset(payload: ReportingRequest, *, container: Any, operational_today: date) -> dict[str, Any] | None:
    if payload.report_id in {"animal-register","animal-population"}: return _animal_dataset(payload,container)
    if payload.report_id in {"daily-milk","milk-animal","milk-disposition"}: return milk_reporting_dataset(payload,container,operational_today)
    if payload.report_id in {"milk-quality-log","quality-summary"}: return milk_quality_reporting_dataset(payload,container,operational_today)
    if payload.report_id in {"current-tmr","historical-tmr"}: return tmr_reporting_dataset(payload,container,operational_today)
    if payload.report_id in {"finance-ledger","financial-summary"}: return _finance_dataset(payload,container,operational_today)
    if payload.report_id in {"breeding-cycle","breeding-performance"}: return _generic_repo_dataset(payload,container,operational_today,"breeding",{"animal_id":("animal_id",),"technician":("technician",),"event_type":("event_type",),"semen_type":("semen_type",),"semen_lot":("semen_lot_id",)})
    if payload.report_id=="health-cases": return _generic_repo_dataset(payload,container,operational_today,"health_cases",{"animal_id":("animal_id",),"case_status":("status",),"severity":("severity",)})
    if payload.report_id=="withdrawal": return _generic_repo_dataset(payload,container,operational_today,"treatment",{"animal_id":("animal_id",),"status":("status",)})
    if payload.report_id=="vaccination-schedule": return _generic_repo_dataset(payload,container,operational_today,"vaccinations",{"animal_id":("animal_id",),"vaccine":("vaccine","vaccine_name"),"schedule_status":("status","schedule_status")})
    if payload.report_id=="coml-period": return _generic_repo_dataset(payload,container,operational_today,"coml",{"lock_status":("status",),"cost_component":("cost_component",)})
    if payload.report_id=="animal-lifecycle": return _generic_repo_dataset(payload,container,operational_today,"operational_events",{"event_type":("event_type","type"),"category":("category",)})
    if payload.report_id=="animal-passport": return animal_passport_dataset(payload,container,operational_today)
    if payload.report_id=="whole-farm-snapshot":
        selected=payload.snapshot_date
        if selected is None: raise HTTPException(status_code=422,detail="snapshot_date is required for Complete Farm Snapshot.")
        section_specs=(("animal-population","ANIMALS","CURRENT_HERD"),("daily-milk","MILK","OPERATIONAL_DATE"),("milk-quality-log","MILK_QUALITY","OPERATIONAL_DATE"),("current-tmr","FEED","OPERATIONAL_DATE"),("finance-ledger","FINANCE","DATE_RANGE"),("breeding-cycle","BREEDING","AS_OF_DATE"),("health-cases","HEALTH","AS_OF_DATE"),("vaccination-schedule","VACCINATION","OPERATIONAL_DATE"),("coml-period","COML","MONTH"))
        sections=[]
        for report_id,domain,mode in section_specs:
            child=_snapshot_child(report_id,domain,mode,selected); result=_canonical_dataset(child,container=container,operational_today=selected)
            if result is None: raise HTTPException(status_code=503,detail={"code":"REPORTING_SNAPSHOT_SECTION_UNAVAILABLE","report_id":report_id})
            sections.append({"report_id":report_id,"record_count":len(result["rows"]),"summary":result["summary"]})
        return _dataset(sections,summary={"snapshot_date":selected.isoformat(),"sections":len(sections)})
    return None


def _reporting_payload(payload: ReportingRequest, container: Any) -> tuple[ReportDefinition, dict[str, Any], date, datetime]:
    definition=REPORT_BY_ID[payload.report_id]; authority=OperationalDateAuthority(); operational_today=authority.current_date(); generated_at=authority.current_datetime(); dataset=_canonical_dataset(payload,container=container,operational_today=operational_today)
    if dataset is None: dataset={"dataset_status":"DATASET_NOT_IMPLEMENTED","authority_status":"DATASET_NOT_IMPLEMENTED","columns":[],"rows":[],"summary":{},"warnings":["Canonical dataset generation is not implemented for this report yet. No farm values have been fabricated."]}
    dataset=_project_dataset(dataset,payload.selected_columns)
    return definition,dataset,operational_today,generated_at


@router.get("/catalog")
def reporting_catalog():
    return {"data_status":"REPORTING_CATALOG","read_only":True,"reports":[report.model_dump() for report in REPORTS]}


@router.post("/preview")
def reporting_preview(payload: ReportingRequest, container=Depends(get_container)):
    definition,dataset,operational_today,generated_at=_reporting_payload(payload,container); period=_resolved_period(payload,operational_today=operational_today)
    return {"data_status":"REPORTING_DATASET","dataset_status":dataset["dataset_status"],"read_only":True,"report_id":definition.id,"domain":definition.domain,"title":definition.name,"authority":definition.authority,"authority_status":dataset["authority_status"],"historical_capability":definition.historical_capability,"required_permissions":list(definition.required_permissions),"period_mode":payload.period_mode,"period":period,"filters":payload.filters,"generated_at":generated_at.isoformat(),"record_count":len(dataset["rows"]),"columns":dataset["columns"],"rows":dataset["rows"],"summary":dataset["summary"],"warnings":dataset["warnings"]}


@router.post("/export")
def reporting_export(payload: ReportingRequest, format: Literal["PDF", "XLSX", "CSV"], container=Depends(get_container)):
    definition,dataset,_,_=_reporting_payload(payload,container)
    columns=list(dataset["columns"]); rows=list(dataset["rows"]); summary=dict(dataset["summary"])
    if format=="CSV": content=csv_bytes(columns,rows); media_type="text/csv; charset=utf-8"; extension="csv"
    elif format=="XLSX": content=xlsx_bytes(definition.name,columns,rows,summary); media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"; extension="xlsx"
    else: content=pdf_bytes(definition.name,columns,rows,summary); media_type="application/pdf"; extension="pdf"
    safe_name="-".join(part for part in definition.name.replace("/"," ").split() if part)
    headers={"Content-Disposition":f'attachment; filename="DairyOS-{safe_name}.{extension}"',"X-DairyOS-Report-Id":definition.id,"X-DairyOS-Record-Count":str(len(rows)),"X-DairyOS-Dataset-Status":str(dataset["dataset_status"]),"X-DairyOS-Column-Count":str(len(columns))}
    return Response(content=content,media_type=media_type,headers=headers)
