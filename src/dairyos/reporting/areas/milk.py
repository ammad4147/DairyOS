"""Milk reporting.

Authority: the milk production session ledger (``MilkProduction`` rows with
``session_ledger`` set), excluding VOID and NOT_MILKED rows, exactly as the
Milk tab, the Dashboard and the Cost of Milk denominator read it. Milk
utilisation comes from ``MilkReconciliationService`` and the persisted milk
dispositions. Produced milk is never assumed to have been sold.
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from datetime import date, datetime, time, timedelta
from typing import Any

from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.models.milk_production import MilkProduction
from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)
from dairyos.reporting.areas.herd import BREED_FILTER, GROUP_FILTER
from dairyos.reporting.context import (
    ReportContext,
    ReportParameterError,
    clean_text,
    money,
    ratio,
    to_date,
    upper,
)
from dairyos.reporting.definitions import (
    Column,
    Filter,
    Metric,
    ReconciliationCheck,
    ReportDefinition,
    ReportResult,
    Section,
)
from dairyos.reporting.engine import column_set
from dairyos.reporting.periods import month_sequence

AREA = "milk"
PERMISSION = "milk.view"
AUTHORITY = "Milk production session ledger (VOID and NOT_MILKED excluded)"
EXCLUDED_STATUSES = {"VOID", "NOT_MILKED"}
SESSIONS = (("morning", "morning_yield"), ("afternoon", "afternoon_yield"), ("evening", "evening_yield"))
MAX_DAILY_AUTHORITY_DAYS = 366

ANIMAL_FILTER = Filter("animal_id", "Animal ID", "animal")
REQUIRED_ANIMAL = Filter("animal_id", "Animal ID", "animal", required=True)


def production_rows(ctx: ReportContext, start: date, end: date, *, animal_id: str | None = None,
                    include_excluded: bool = False) -> list[MilkProduction]:
    query = ctx.session.query(MilkProduction).filter(
        MilkProduction.production_date >= datetime.combine(start, time.min),
        MilkProduction.production_date < datetime.combine(end + timedelta(days=1), time.min),
    )
    if animal_id:
        query = query.filter(MilkProduction.animal_id == animal_id)
    rows = query.order_by(MilkProduction.production_date, MilkProduction.animal_id, MilkProduction.id).all()
    if include_excluded:
        return rows
    return [r for r in rows if is_active_production(r)]


def is_active_production(record: Any) -> bool:
    return bool(getattr(record, "session_ledger", False)) and upper(
        getattr(record, "status", None) or "RECORDED") not in EXCLUDED_STATUSES


def total_litres(record: Any) -> float:
    value = getattr(record, "total_yield", None)
    if value is None:
        value = sum(float(getattr(record, f) or 0) for _, f in SESSIONS if getattr(record, f, None) is not None)
    return float(value or 0.0)


def _animal_attribute_filter(ctx: ReportContext):
    breed, group = ctx.filter("breed"), ctx.filter("production_group")
    if not breed and not group:
        return None
    allowed = set()
    for animal in ctx.animals():
        if breed and (clean_text(getattr(animal, "breed", None)) or "").lower() != breed.lower():
            continue
        if group and (clean_text(getattr(animal, "production_group", None)) or "").lower() != group.lower():
            continue
        allowed.add(str(animal.animal_id))
    return allowed


# ---------------------------------------------------------------------------
DAILY_COLUMNS = column_set(
    Column("date", "Date", "date"),
    Column("animals_milked", "Animals Milked", "integer"),
    Column("morning", "Morning (L)", "litres", total=True),
    Column("afternoon", "Afternoon (L)", "litres", total=True),
    Column("evening", "Evening (L)", "litres", total=True),
    Column("total", "Total Milk (L)", "litres", total=True),
    Column("avg_per_animal", "Average per Animal (L)", "litres"),
    Column("change_pct", "Change on Previous Day (%)", "percent", "Trend", "optional"),
)


def _daily(ctx: ReportContext, start: date, end: date, animal_id: str | None = None) -> list[dict[str, Any]]:
    days: dict[date, dict[str, Any]] = {}
    allowed = _animal_attribute_filter(ctx) if ctx.definition.id == "milk-daily-production" else None
    for record in production_rows(ctx, start, end, animal_id=animal_id):
        if allowed is not None and str(record.animal_id) not in allowed:
            continue
        day = to_date(record.production_date)
        bucket = days.setdefault(day, {"date": day, "animals": set(), "morning": 0.0, "afternoon": 0.0,
                                       "evening": 0.0, "total": 0.0})
        bucket["animals"].add(str(record.animal_id))
        for key, field in SESSIONS:
            bucket[key] += float(getattr(record, field) or 0)
        bucket["total"] += total_litres(record)
    rows, previous = [], None
    for day in sorted(days):
        bucket = days[day]
        row = {"date": day, "animals_milked": len(bucket["animals"]),
               **{k: round(bucket[k], 2) for k in ("morning", "afternoon", "evening", "total")}}
        row["avg_per_animal"] = ratio(row["total"], row["animals_milked"])
        row["change_pct"] = ratio((row["total"] - previous) * 100, previous, 1) if previous else None
        previous = row["total"]
        rows.append(row)
    return rows


def build_daily(ctx: ReportContext) -> ReportResult:
    from dairyos.api.tmr import milk_litres_for_period

    start, end = ctx.period.start, ctx.period.end
    rows = _daily(ctx, start, end)
    total = round(sum(r["total"] for r in rows), 2)
    totals = {"_label": "Total", **{k: round(sum(r[k] for r in rows), 2) for k in ("morning", "afternoon", "evening")},
              "total": total}
    checks = []
    if not ctx.filter("breed") and not ctx.filter("production_group"):
        checks.append(ReconciliationCheck("Total milk agrees with the Cost of Milk denominator",
                                          round(milk_litres_for_period(ctx.factory, start, end), 2), total, "litres"))
    return ReportResult(
        sections=[Section("daily", "Daily Milk Production", DAILY_COLUMNS, rows, totals, primary=True)],
        summary=[
            Metric("total", "Total Milk", total, "litres"),
            Metric("days", "Days with Production", len(rows), "integer"),
            Metric("avg_day", "Average per Production Day", ratio(total, len(rows)), "litres"),
            Metric("best", "Highest Day", max((r["total"] for r in rows), default=None), "litres"),
        ],
        reconciliation=checks,
        notes=["Breed and Production Group filters use each animal's current breed and group."]
        if checks == [] else [],
    )


# ---------------------------------------------------------------------------
BY_ANIMAL_COLUMNS = column_set(
    Column("animal_id", "Animal ID", "text", "Identification"),
    Column("ear_tag", "Ear Tag", "text", "Identification", "optional"),
    Column("breed", "Breed", "text", "Animal Details"),
    Column("production_group", "Production Group", "text", "Animal Details"),
    Column("days_recorded", "Days Recorded", "integer", "Production"),
    Column("morning", "Morning (L)", "litres", "Sessions", "optional", total=True),
    Column("afternoon", "Afternoon (L)", "litres", "Sessions", "optional", total=True),
    Column("evening", "Evening (L)", "litres", "Sessions", "optional", total=True),
    Column("total", "Total Milk (L)", "litres", "Production", total=True),
    Column("avg_per_day", "Average per Day (L)", "litres", "Production"),
    Column("best_day", "Best Day (L)", "litres", "Production"),
    Column("share", "% of Period Milk", "percent", "Production"),
)


def build_by_animal(ctx: ReportContext) -> ReportResult:
    allowed = _animal_attribute_filter(ctx)
    animals = ctx.animal_index()
    buckets: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for record in production_rows(ctx, ctx.period.start, ctx.period.end, animal_id=ctx.filter("animal_id")):
        animal_id = str(record.animal_id)
        if allowed is not None and animal_id not in allowed:
            continue
        bucket = buckets.setdefault(animal_id, {"days": set(), "morning": 0.0, "afternoon": 0.0, "evening": 0.0,
                                                "total": 0.0, "by_day": defaultdict(float)})
        day = to_date(record.production_date)
        bucket["days"].add(day)
        for key, field in SESSIONS:
            bucket[key] += float(getattr(record, field) or 0)
        litres = total_litres(record)
        bucket["total"] += litres
        bucket["by_day"][day] += litres
    grand = sum(b["total"] for b in buckets.values())
    rows = []
    for animal_id, bucket in buckets.items():
        animal = animals.get(animal_id)
        rows.append({
            "animal_id": animal_id,
            "ear_tag": clean_text(getattr(animal, "ear_tag", None)) if animal else None,
            "breed": clean_text(getattr(animal, "breed", None)) if animal else None,
            "production_group": clean_text(getattr(animal, "production_group", None)) if animal else None,
            "days_recorded": len(bucket["days"]),
            **{k: round(bucket[k], 2) for k in ("morning", "afternoon", "evening", "total")},
            "avg_per_day": ratio(bucket["total"], len(bucket["days"])),
            "best_day": round(max(bucket["by_day"].values()), 2) if bucket["by_day"] else None,
            "share": ratio(bucket["total"] * 100, grand, 1),
            "_drill": {"report_id": "milk-animal-history", "label": animal_id, "filters": {"animal_id": animal_id},
                       "period": {"mode": "CUSTOM", "start_date": ctx.period.start.isoformat(),
                                  "end_date": ctx.period.end.isoformat()}},
        })
    totals = {"_label": "Total", **{k: round(sum(r[k] for r in rows), 2) for k in ("morning", "afternoon", "evening", "total")}}
    return ReportResult(
        sections=[Section("animals", "Milk Production by Animal", BY_ANIMAL_COLUMNS, rows, totals, primary=True)],
        summary=[Metric("animals", "Animals with Production", len(rows), "integer"),
                 Metric("total", "Total Milk", round(grand, 2), "litres"),
                 Metric("avg", "Average per Animal per Day",
                        ratio(grand, sum(r["days_recorded"] for r in rows)), "litres")],
        notes=["Average per Day divides by the days on which the animal has a production record, so animals "
               "milked twice and three times daily are each measured on their own recorded days."],
    )


# ---------------------------------------------------------------------------
HISTORY_COLUMNS = column_set(
    Column("date", "Date", "date"),
    Column("morning", "Morning (L)", "litres", total=True),
    Column("afternoon", "Afternoon (L)", "litres", total=True),
    Column("evening", "Evening (L)", "litres", total=True),
    Column("total", "Total Milk (L)", "litres", total=True),
    Column("status", "Status", "status"),
    Column("counts", "Counted in Totals"),
    Column("notes", "Notes", "text", "Details", "optional"),
)


def build_animal_history(ctx: ReportContext) -> ReportResult:
    animal_id = ctx.filter("animal_id")
    if animal_id not in ctx.animal_index():
        raise ReportParameterError("Animal ID was not found in the herd register.")
    rows = []
    for record in production_rows(ctx, ctx.period.start, ctx.period.end, animal_id=animal_id, include_excluded=True):
        if not bool(getattr(record, "session_ledger", False)):
            continue
        active = is_active_production(record)
        rows.append({
            "date": to_date(record.production_date),
            **{key: getattr(record, field) for key, field in SESSIONS},
            "total": round(total_litres(record), 2) if active else None,
            "status": upper(record.status) or "RECORDED",
            "counts": "Yes" if active else "No",
            "notes": clean_text(record.notes),
            "_active": active,
        })
    active_rows = [r for r in rows if r["_active"]]
    totals = {"_label": "Total (counted records)",
              **{k: round(sum(float(r[k] or 0) for r in active_rows), 2) for k in ("morning", "afternoon", "evening")},
              "total": round(sum(r["total"] or 0 for r in active_rows), 2)}
    return ReportResult(
        sections=[Section("history", f"Milk History: {animal_id}", HISTORY_COLUMNS, rows, totals, primary=True)],
        summary=[Metric("total", "Total Milk", totals["total"], "litres"),
                 Metric("days", "Days Recorded", len(active_rows), "integer"),
                 Metric("avg", "Average per Day", ratio(totals["total"], len(active_rows)), "litres")],
    )


# ---------------------------------------------------------------------------
MONTHLY_COLUMNS = column_set(
    Column("month", "Month"),
    Column("production_days", "Days with Production", "integer", total=True),
    Column("total", "Total Milk (L)", "litres", total=True),
    Column("avg_per_day", "Average per Day (L)", "litres"),
    Column("avg_animals", "Average Animals Milked", "number"),
    Column("avg_per_animal_day", "Average per Animal per Day (L)", "litres"),
)


def build_monthly(ctx: ReportContext) -> ReportResult:
    daily = _daily(ctx, ctx.period.start, ctx.period.end)
    rows = []
    for first, last in month_sequence(ctx.period.start, ctx.period.end):
        days = [d for d in daily if first <= d["date"] <= last]
        total = round(sum(d["total"] for d in days), 2)
        animal_days = sum(d["animals_milked"] for d in days)
        rows.append({"month": first.strftime("%B %Y"), "production_days": len(days), "total": total,
                     "avg_per_day": ratio(total, len(days)), "avg_animals": ratio(animal_days, len(days), 1),
                     "avg_per_animal_day": ratio(total, animal_days)})
    grand = round(sum(r["total"] for r in rows), 2)
    return ReportResult(
        sections=[Section("months", "Monthly Milk Summary", MONTHLY_COLUMNS, rows,
                          {"_label": "Total", "production_days": sum(r["production_days"] for r in rows), "total": grand},
                          primary=True)],
        summary=[Metric("total", "Total Milk", grand, "litres")],
    )


# ---------------------------------------------------------------------------
UTILISATION_COLUMNS = column_set(
    Column("date", "Date", "date"),
    Column("produced", "Produced (L)", "litres", total=True),
    Column("sold", "Sold (L)", "litres", total=True),
    Column("calf_feed", "Calf Feeding (L)", "litres", total=True),
    Column("domestic", "Domestic Use (L)", "litres", total=True),
    Column("wastage", "Wastage (L)", "litres", total=True),
    Column("withdrawal", "Withdrawal Discard (L)", "litres", total=True),
    Column("other", "Other (L)", "litres", total=True),
    Column("accounted", "Accounted (L)", "litres", total=True),
    Column("unaccounted", "Unaccounted (L)", "litres", total=True),
    Column("status", "Reconciliation", "status"),
    Column("sale_value", "Sale Value (PKR)", "money", "Sales", "optional", total=True),
)
_DISPOSITION_KEYS = {"SOLD": "sold", "CALF_FEED": "calf_feed", "DOMESTIC_USE": "domestic",
                     "WASTAGE": "wastage", "WITHDRAWAL": "withdrawal", "OTHER": "other"}


def build_utilisation(ctx: ReportContext) -> ReportResult:
    start, end = ctx.period.start, min(ctx.period.end, ctx.today)
    if ctx.period.days > MAX_DAILY_AUTHORITY_DAYS:
        raise ReportParameterError("Milk Utilisation reconciles each day individually. Select a period of one year or less.")
    service = MilkReconciliationService(disposition_repository=ctx.factory.milk_dispositions(),
                                        production_repository=ctx.factory.milk())
    dispositions: dict[date, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    sale_value: dict[date, Any] = defaultdict(lambda: money(0))
    if start <= end:
        for item in ctx.session.query(MilkDisposition).filter(
            MilkDisposition.production_date >= start, MilkDisposition.production_date <= end).all():
            if upper(item.status) == "VOID":
                continue
            key = _DISPOSITION_KEYS.get(upper(item.disposition_type), "other")
            dispositions[item.production_date][key] += float(item.quantity_litres or 0)
            if key == "sold":
                sale_value[item.production_date] += money(item.amount_due)
    rows = []
    day = start
    while day <= end:
        result = service.reconcile(day, raise_finding=False)
        produced = float(result.get("produced_litres") or 0)
        if produced or dispositions.get(day):
            split = dispositions.get(day, {})
            rows.append({"date": day, "produced": round(produced, 2),
                         **{k: round(split.get(k, 0.0), 2) for k in _DISPOSITION_KEYS.values()},
                         "accounted": round(float(result.get("accounted_litres") or 0), 2),
                         "unaccounted": round(float(result.get("unaccounted_litres") or 0), 2),
                         "status": str(result.get("status") or "").replace("_", " ").title() or None,
                         "sale_value": sale_value.get(day, money(0))})
        day += timedelta(days=1)
    keys = ("produced", *_DISPOSITION_KEYS.values(), "accounted", "unaccounted")
    totals: dict[str, Any] = {"_label": "Total", **{k: round(sum(r[k] for r in rows), 2) for k in keys},
                              "sale_value": sum((r["sale_value"] for r in rows), money(0))}
    produced_total = totals["produced"]
    return ReportResult(
        sections=[Section("utilisation", "Milk Utilisation", UTILISATION_COLUMNS, rows, totals, primary=True)],
        summary=[Metric("produced", "Produced", produced_total, "litres"),
                 Metric("sold", "Sold", totals["sold"], "litres", f"{ratio(totals['sold'] * 100, produced_total, 1) or 0}% of produced"),
                 Metric("calf", "Calf Feeding", totals["calf_feed"], "litres"),
                 Metric("domestic", "Domestic Use", totals["domestic"], "litres"),
                 Metric("waste", "Wastage and Withdrawal", round(totals["wastage"] + totals["withdrawal"], 2), "litres"),
                 Metric("unaccounted", "Unaccounted", totals["unaccounted"], "litres")],
        notes=["Produced, Accounted and Unaccounted come from the daily Milk reconciliation authority. "
               "Destination litres come from the recorded milk dispositions, VOID excluded."],
    )


# ---------------------------------------------------------------------------
WATCHLIST_COLUMNS = column_set(
    Column("animal_id", "Animal ID"),
    Column("breed", "Breed", "text", "Animal Details", "optional"),
    Column("production_group", "Production Group", "text", "Animal Details", "optional"),
    Column("previous_date", "Previous Day", "date"),
    Column("previous_litres", "Previous (L)", "litres"),
    Column("current_date", "Latest Day", "date"),
    Column("current_litres", "Latest (L)", "litres"),
    Column("drop_percentage", "Drop (%)", "percent"),
    Column("severity", "Severity", "status"),
)


def build_yield_drop(ctx: ReportContext) -> ReportResult:
    from dairyos.api.milk_production_analytics import _yield_drop_watchlist
    from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
        MilkProductionTrendIntelligenceService,
    )

    service = MilkProductionTrendIntelligenceService(repository_factory=ctx.factory)
    eligible = service._eligible_animals(ctx.factory)
    watchlist = _yield_drop_watchlist(
        service=service, records=ctx.factory.milk().get_all(), animals=eligible,
        histories=service._animal_histories(ctx.factory, eligible), target_date=ctx.period.as_of, lookback_days=30,
    )
    animals = ctx.animal_index()
    rows = []
    for item in watchlist:
        animal = animals.get(str(item["animal_id"]))
        rows.append({
            "animal_id": item["animal_id"],
            "breed": clean_text(getattr(animal, "breed", None)) if animal else None,
            "production_group": clean_text(getattr(animal, "production_group", None)) if animal else None,
            "previous_date": to_date(item["previous_date"]), "previous_litres": item["previous_litres"],
            "current_date": to_date(item["current_date"]), "current_litres": item["current_litres"],
            "drop_percentage": item["drop_percentage"], "severity": item["severity"],
        })
    return ReportResult(
        sections=[Section("watchlist", "Yield Drop Watchlist", WATCHLIST_COLUMNS, rows, primary=True)],
        summary=[Metric("animals", "Animals on Watchlist", len(rows), "integer"),
                 Metric("critical", "Critical (30% or more)", sum(1 for r in rows if r["severity"] == "CRITICAL"), "integer")],
        notes=["Same rule as the Dashboard watchlist: a fall of 15% or more between an animal's two most recent "
               "complete milking days within the last 30 days. 30% or more is Critical."],
    )


# ---------------------------------------------------------------------------
LACTATION_COLUMNS = column_set(
    Column("animal_id", "Animal ID"),
    Column("breed", "Breed"),
    Column("production_group", "Production Group", "text", "Animal Details", "optional"),
    Column("lactation_number", "Lactation No.", "integer"),
    Column("last_calving_date", "Last Calving", "date"),
    Column("days_in_milk", "Days in Milk", "days"),
    Column("days_recorded", "Days Recorded", "integer"),
    Column("total", "Period Milk (L)", "litres", total=True),
    Column("avg_per_day", "Average per Day (L)", "litres"),
    Column("pregnancy_status", "Pregnancy Status", "status"),
    Column("expected_dry_off_date", "Expected Dry-Off", "date", "Reproduction", "optional"),
)


def build_lactation(ctx: ReportContext) -> ReportResult:
    from dairyos.reporting.areas.breeding import reproductive_states

    states = reproductive_states(ctx, ctx.period.as_of)
    production: dict[str, dict[str, Any]] = {}
    for record in production_rows(ctx, ctx.period.start, ctx.period.end):
        bucket = production.setdefault(str(record.animal_id), {"days": set(), "total": 0.0})
        bucket["days"].add(to_date(record.production_date))
        bucket["total"] += total_litres(record)
    animals = ctx.animal_index()
    rows = []
    for animal_id, bucket in production.items():
        animal, state = animals.get(animal_id), states.get(animal_id)
        rows.append({
            "animal_id": animal_id,
            "breed": clean_text(getattr(animal, "breed", None)) if animal else None,
            "production_group": clean_text(getattr(animal, "production_group", None)) if animal else None,
            "lactation_number": (state.lactation_number or None) if state else None,
            "last_calving_date": state.last_calving_date if state else None,
            "days_in_milk": state.days_in_milk if state else None,
            "days_recorded": len(bucket["days"]),
            "total": round(bucket["total"], 2),
            "avg_per_day": ratio(bucket["total"], len(bucket["days"])),
            "pregnancy_status": state.pregnancy_status.replace("_", " ").title() if state else None,
            "expected_dry_off_date": state.expected_dry_off_date if state else None,
        })
    return ReportResult(
        sections=[Section("lactation", "Lactation and Production Performance", LACTATION_COLUMNS, rows,
                          {"_label": "Total", "total": round(sum(r["total"] for r in rows), 2)}, primary=True)],
        summary=[Metric("animals", "Animals", len(rows), "integer"),
                 Metric("avg_dim", "Average Days in Milk",
                        ratio(sum(r["days_in_milk"] or 0 for r in rows), sum(1 for r in rows if r["days_in_milk"] is not None), 0),
                        "days")],
        notes=["Lactation number and Days in Milk are calculated by the reproductive-state authority from recorded "
               "calvings. They are blank when no calving is recorded for the animal."],
    )


# ---------------------------------------------------------------------------
QUALITY_COLUMNS = column_set(
    Column("date", "Sample Date", "date"),
    Column("sample_type", "Sample Type"),
    Column("fat_pct", "Fat (%)", "number"),
    Column("snf_pct", "SNF (%)", "number"),
    Column("total_solids_pct", "Fat + SNF (%)", "number", "Details", "optional"),
    Column("recorded_by", "Recorded By"),
    Column("revisions", "Times Amended", "integer", "Details", "optional"),
    Column("notes", "Notes", "text", "Details", "optional"),
)


def build_quality(ctx: ReportContext) -> ReportResult:
    wanted = ctx.filter("sample_type")
    rows = []
    for sample in ctx.factory.milk_quality().get_range(ctx.period.start, ctx.period.end) or []:
        if wanted and upper(sample.sample_type) != wanted:
            continue
        rows.append({
            "date": to_date(sample.quality_date),
            "sample_type": (clean_text(sample.sample_type) or "").replace("_", " ").title() or None,
            "fat_pct": sample.fat_pct, "snf_pct": sample.snf_pct,
            "total_solids_pct": round(float(sample.fat_pct or 0) + float(sample.snf_pct or 0), 3),
            "recorded_by": clean_text(sample.recorded_by),
            "revisions": len(sample.revision_history or []),
            "notes": clean_text(sample.notes),
        })
    count = len(rows)
    return ReportResult(
        sections=[Section("quality", "Milk Quality Log", QUALITY_COLUMNS, rows, primary=True)],
        summary=[Metric("samples", "Samples", count, "integer"),
                 Metric("fat", "Average Fat", ratio(sum(r["fat_pct"] for r in rows), count, 3), "percent"),
                 Metric("snf", "Average SNF", ratio(sum(r["snf_pct"] for r in rows), count, 3), "percent"),
                 Metric("latest", "Latest Sample", max((r["date"] for r in rows), default=None), "date")],
        notes=["Only recorded samples are listed. DairyOS records fat and SNF; somatic cell count and residue tests "
               "are not recorded and are therefore not reported."],
    )


def _definition(report_id, title, purpose, builder, **kwargs) -> ReportDefinition:
    kwargs.setdefault("authority", AUTHORITY)
    kwargs.setdefault("period", "range")
    return ReportDefinition(id=report_id, area=AREA, title=title, purpose=purpose,
                            permission=PERMISSION, builder=builder, **kwargs)


REPORTS: tuple[ReportDefinition, ...] = (
    _definition("milk-daily-production", "Daily Milk Production",
                "Milk produced each day with the Morning, Afternoon and Evening sessions, animals milked and day-on-day trend.",
                build_daily, columns=DAILY_COLUMNS, default_sort=("date", "asc"), filters=(BREED_FILTER, GROUP_FILTER)),
    _definition("milk-by-animal", "Milk Production by Animal",
                "Each animal's production for the period: total, average per day, best day and share of the herd's milk.",
                build_by_animal, columns=BY_ANIMAL_COLUMNS, default_sort=("total", "desc"),
                filters=(ANIMAL_FILTER, BREED_FILTER, GROUP_FILTER)),
    _definition("milk-animal-history", "Individual Animal Milk History",
                "Day-by-day session yields for one animal, including records excluded from totals.",
                build_animal_history, columns=HISTORY_COLUMNS, default_sort=("date", "asc"),
                filters=(REQUIRED_ANIMAL,), default_period="LAST_30_DAYS"),
    _definition("milk-monthly-summary", "Monthly Milk Summary",
                "Production by calendar month with daily averages and animals milked.",
                build_monthly, columns=MONTHLY_COLUMNS, default_period="YEAR_TO_DATE", basis="DERIVED"),
    _definition("milk-utilisation", "Milk Utilisation",
                "Where produced milk went each day: sold, calf feeding, domestic use, wastage, withdrawal discard and unaccounted.",
                build_utilisation, columns=UTILISATION_COLUMNS, default_sort=("date", "asc"), basis="CALCULATED",
                authority="Milk reconciliation authority and persisted milk dispositions"),
    _definition("milk-quality-log", "Milk Quality Log",
                "Recorded milk quality samples with fat and SNF, and the period averages.",
                build_quality, columns=QUALITY_COLUMNS, default_sort=("date", "asc"),
                authority="Milk quality sample records",
                filters=(Filter("sample_type", "Sample Type", options=(("BULK_TANK", "Bulk Tank"), ("INDIVIDUAL", "Individual"))),)),
    _definition("milk-yield-drop-watchlist", "Yield Drop Watchlist",
                "Animals whose latest complete milking day fell 15% or more against their previous complete day.",
                build_yield_drop, period="as_of", columns=WATCHLIST_COLUMNS, default_sort=("drop_percentage", "desc"),
                basis="CALCULATED", authority="Dashboard yield-drop derivation over governed complete animal-days",
                empty_message="No animal currently shows a yield drop of 15% or more."),
    _definition("milk-lactation-performance", "Lactation & Production Performance",
                "Production in the period alongside lactation number, days in milk and pregnancy status.",
                build_lactation, columns=LACTATION_COLUMNS, default_sort=("avg_per_day", "desc"), basis="CALCULATED",
                authority="Milk production session ledger and the reproductive-state authority",
                filters=()),
)
