"""Breeding reporting.

Authorities, consumed and never re-implemented:

* ``breeding_biology._resolve_state`` (``ReproductiveStateService`` with the
  farm reproductive policy): pregnancy status, the 35-day pregnancy-diagnosis
  due date, the 283-day expected calving date, voluntary waiting period,
  days in milk and lactation number.
* ``BreedingCycleProjectionService``: partition of the immutable breeding
  event ledger into insemination cycles and service attempts.
* ``BreedingAnalyticsService``: conception, loss and calving rates by
  technician, sire and semen lot.
* ``SemenLot`` / ``SemenStockMovement``: semen stock and usage.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import func

from dairyos.data.models.semen_inventory import SemenLot, SemenStockMovement
from dairyos.farm.reproduction.services.breeding_cycle_analytics_service import (
    BreedingAnalyticsService,
    BreedingCycleProjectionService,
)
from dairyos.farm.reproduction.services.reproductive_state_service import (
    DEFAULT_REPRODUCTIVE_POLICY,
    ReproductiveStateError,
)
from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    is_calving,
    is_confirmed_pregnancy,
    is_insemination,
    is_negative_pregnancy_check,
    normalize_event_type,
)
from dairyos.reporting.areas.herd import BREED_FILTER, classify, is_current
from dairyos.reporting.context import ReportContext, ReportParameterError, clean_text, money, to_date
from dairyos.reporting.definitions import Column, Filter, Metric, ReportDefinition, ReportResult, Section
from dairyos.reporting.engine import column_set

AREA = "breeding"
PERMISSION = "breeding.view"
POLICY = DEFAULT_REPRODUCTIVE_POLICY
LOSS_EVENTS = {"pregnancy_lost": "Pregnancy Lost", "abortion": "Abortion", "stillbirth": "Stillbirth"}
MATURE_FEMALE_CATEGORIES = {"Milking", "Dry", "Heifer"}
REPEAT_BREEDER_SERVICES = 3

ANIMAL_FILTER = Filter("animal_id", "Animal ID", "animal")
REQUIRED_ANIMAL = Filter("animal_id", "Animal ID", "animal", required=True)


def breeding_records(ctx: ReportContext) -> list[Any]:
    return ctx.cached("breeding_records", lambda: list(ctx.factory.breeding().get_all() or []))


def records_by_animal(ctx: ReportContext) -> dict[str, list[Any]]:
    def load():
        grouped: dict[str, list[Any]] = {}
        for record in breeding_records(ctx):
            grouped.setdefault(str(record.animal_id), []).append(record)
        return grouped
    return ctx.cached("breeding_by_animal", load)


def reproductive_states(ctx: ReportContext, as_of: date) -> dict[str, Any]:
    """Authoritative reproductive state of every animal with breeding history."""
    def load():
        from dairyos.api.breeding_biology import _resolve_state

        states = {}
        for animal_id, records in records_by_animal(ctx).items():
            try:
                states[animal_id] = _resolve_state(animal_id, records, as_of_date=as_of)
            except (ReproductiveStateError, ValueError):
                states[animal_id] = None
        return states
    return ctx.cached(f"repro_states:{as_of.isoformat()}", load)


def cycles(ctx: ReportContext) -> list[dict[str, Any]]:
    return ctx.cached("breeding_cycles", lambda: BreedingCycleProjectionService.project(breeding_records(ctx)))


def _breeding_females(ctx: ReportContext) -> list[Any]:
    return [a for a in ctx.animals() if is_current(a) and classify(a)[0] in MATURE_FEMALE_CATEGORIES]


def _label(value: Any) -> str | None:
    text = clean_text(value)
    return text.replace("_", " ").title() if text else None


def _event_label(record: Any) -> str:
    kind = normalize_event_type(getattr(record, "event_type", ""))
    if is_insemination(record):
        return "Insemination"
    if is_confirmed_pregnancy(record):
        return "Pregnancy Confirmed"
    if is_negative_pregnancy_check(record):
        return "Pregnancy Diagnosis: Not Pregnant"
    if is_calving(record):
        return "Calving"
    return LOSS_EVENTS.get(kind) or _label(kind) or "Breeding Event"


def _service_attempts(ctx: ReportContext) -> dict[str, int]:
    """Service attempts of each animal's current (or latest) cycle run."""
    attempts: dict[str, int] = {}
    for cycle in cycles(ctx):
        attempts[cycle["animal_id"]] = cycle["service_attempt_number"]
    return attempts


# ---------------------------------------------------------------------------
STATUS_COLUMNS = column_set(
    Column("animal_id", "Animal ID", "text", "Identification"),
    Column("ear_tag", "Ear Tag", "text", "Identification", "optional"),
    Column("category", "Category", "text", "Animal Details"),
    Column("breed", "Breed", "text", "Animal Details", "optional"),
    Column("reproductive_status", "Reproductive Status", "status", "Status"),
    Column("lactation_number", "Lactation No.", "integer", "Lactation"),
    Column("last_calving_date", "Last Calving", "date", "Lactation"),
    Column("days_in_milk", "Days in Milk", "days", "Lactation"),
    Column("last_insemination_date", "Last Insemination", "date", "Service"),
    Column("service_attempts", "Services This Cycle", "integer", "Service"),
    Column("pd_due_date", "PD Due", "date", "Service"),
    Column("pregnancy_confirmed_date", "Pregnancy Confirmed", "date", "Pregnancy", "optional"),
    Column("days_pregnant", "Days Pregnant", "days", "Pregnancy"),
    Column("expected_dry_off_date", "Expected Dry-Off", "date", "Pregnancy", "optional"),
    Column("expected_calving_date", "Expected Calving", "date", "Pregnancy"),
    Column("days_open", "Days Open", "days", "Pregnancy", "optional"),
    Column("eligible_to_breed", "Eligible to Breed", "text", "Status", "optional"),
)


def _status_rows(ctx: ReportContext, as_of: date) -> list[dict[str, Any]]:
    states = reproductive_states(ctx, as_of)
    attempts = _service_attempts(ctx)
    active_cycles = BreedingCycleProjectionService.current_by_animal(cycles(ctx))
    rows = []
    for animal in _breeding_females(ctx):
        animal_id = str(animal.animal_id)
        has_history = animal_id in records_by_animal(ctx)
        state = states.get(animal_id)
        if has_history and state is None:
            status = "History needs review"
        elif state is None:
            status = "No breeding history"
        else:
            status = _label(state.reproductive_status)
        rows.append({
            "animal_id": animal_id,
            "ear_tag": clean_text(getattr(animal, "ear_tag", None)),
            "category": classify(animal)[0],
            "breed": clean_text(getattr(animal, "breed", None)),
            "reproductive_status": status,
            "lactation_number": (state.lactation_number or None) if state else None,
            "last_calving_date": state.last_calving_date if state else None,
            "days_in_milk": state.days_in_milk if state else None,
            "last_insemination_date": state.last_insemination_date if state else None,
            "service_attempts": attempts.get(animal_id) if animal_id in active_cycles else None,
            "pd_due_date": state.pd_due_date if state and state.reproductive_status == "BRED" else None,
            "pregnancy_confirmed_date": state.pregnancy_confirmed_date if state else None,
            "days_pregnant": state.days_pregnant if state else None,
            "expected_dry_off_date": state.expected_dry_off_date if state else None,
            "expected_calving_date": state.expected_calving_date if state else None,
            "days_open": state.days_open if state else None,
            "eligible_to_breed": ("Yes" if state.eligible_to_breed else "No") if state else "Yes",
            "_state": state,
        })
    return rows


def _filter_breed(ctx: ReportContext, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    breed = ctx.filter("breed")
    return [r for r in rows if not breed or (r.get("breed") or "").lower() == breed.lower()]


def build_status(ctx: ReportContext) -> ReportResult:
    rows = _filter_breed(ctx, _status_rows(ctx, ctx.period.as_of))
    wanted = ctx.filter("reproductive_status")
    if wanted:
        rows = [r for r in rows if (r["reproductive_status"] or "").upper().replace(" ", "_") == wanted]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["reproductive_status"]] = counts.get(row["reproductive_status"], 0) + 1
    return ReportResult(
        sections=[Section("status", "Breeding Status", STATUS_COLUMNS, rows, primary=True)],
        summary=[Metric("females", "Breeding Females", len(rows), "integer")]
        + [Metric(k, k, v, "integer") for k, v in sorted(counts.items(), key=lambda kv: -kv[1])],
        notes=[f"Policy: pregnancy diagnosis is due {POLICY.pd_due_days} days after insemination, expected calving is "
               f"{POLICY.gestation_days} days after the successful insemination, voluntary waiting period is "
               f"{POLICY.voluntary_waiting_period_days} days."],
    )


def _work_columns(*keys: str, extra: tuple[Column, ...] = ()) -> tuple[Column, ...]:
    by_key = {c.key: c for c in STATUS_COLUMNS}
    picked = [Column(by_key[k].key, by_key[k].label, by_key[k].type, by_key[k].group, "default") for k in keys]
    return column_set(*picked, *extra)


DUE_AI_COLUMNS = _work_columns(
    "animal_id", "ear_tag", "category", "breed", "reproductive_status", "last_calving_date", "days_in_milk",
    "last_insemination_date",
    extra=(Column("days_since_vwp", "Days Past Waiting Period", "days", "Service"),
           Column("previous_services", "Previous Services", "integer", "Service")))


def build_due_for_ai(ctx: ReportContext) -> ReportResult:
    as_of = ctx.period.as_of
    attempts = _service_attempts(ctx)
    rows = []
    for row in _filter_breed(ctx, _status_rows(ctx, as_of)):
        state = row["_state"]
        if row["reproductive_status"] == "History needs review":
            continue
        if state is not None and (not state.eligible_to_breed or state.reproductive_status in {"BRED", "PREGNANT"}):
            continue
        vwp_end = state.voluntary_waiting_period_end if state else None
        row["days_since_vwp"] = (as_of - vwp_end).days if vwp_end else None
        row["previous_services"] = attempts.get(row["animal_id"], 0) if state and state.last_insemination_date else 0
        rows.append(row)
    return ReportResult(
        sections=[Section("due", "Animals Due for AI", DUE_AI_COLUMNS, rows, primary=True)],
        summary=[Metric("animals", "Animals Due for AI", len(rows), "integer"),
                 Metric("heifers", "Of Which Heifers", sum(1 for r in rows if r["category"] == "Heifer"), "integer")],
        notes=["Listed: breeding females that are not pregnant, are not awaiting pregnancy diagnosis and have completed "
               f"the {POLICY.voluntary_waiting_period_days}-day voluntary waiting period after their last calving."],
    )


PD_DUE_COLUMNS = _work_columns(
    "animal_id", "ear_tag", "category", "breed", "last_insemination_date", "service_attempts", "pd_due_date",
    extra=(Column("days_since_ai", "Days Since Insemination", "days", "Service"),
           Column("pd_position", "PD Position", "status", "Service")))


def build_pd_due(ctx: ReportContext) -> ReportResult:
    as_of = ctx.period.as_of
    only_due = ctx.flag("only_due", True)
    rows = []
    for row in _filter_breed(ctx, _status_rows(ctx, as_of)):
        state = row["_state"]
        if state is None or state.reproductive_status != "BRED" or state.pd_due_date is None:
            continue
        overdue = (as_of - state.pd_due_date).days
        row["days_since_ai"] = (as_of - state.last_insemination_date).days
        row["pd_position"] = "Overdue" if overdue > 0 else "Due today" if overdue == 0 else f"Due in {-overdue} d"
        if only_due and overdue < 0:
            continue
        rows.append(row)
    return ReportResult(
        sections=[Section("pd", "Pregnancy Diagnosis Due", PD_DUE_COLUMNS, rows, primary=True)],
        summary=[Metric("due", "Animals Listed", len(rows), "integer"),
                 Metric("overdue", "Overdue", sum(1 for r in rows if r["pd_position"] == "Overdue"), "integer")],
        notes=[f"Pregnancy diagnosis falls due {POLICY.pd_due_days} days after the last insemination."],
    )


PREGNANCY_COLUMNS = _work_columns(
    "animal_id", "ear_tag", "category", "breed", "last_insemination_date", "pregnancy_confirmed_date",
    "days_pregnant", "expected_dry_off_date", "expected_calving_date",
    extra=(Column("days_to_calving", "Days to Calving", "days", "Pregnancy"),
           Column("sire", "Sire", "text", "Service", "optional")))


def build_pregnancies(ctx: ReportContext) -> ReportResult:
    as_of = ctx.period.as_of
    within = ctx.filter("calving_within")
    active = BreedingCycleProjectionService.current_by_animal(cycles(ctx))
    rows = []
    for row in _filter_breed(ctx, _status_rows(ctx, as_of)):
        state = row["_state"]
        if state is None or state.pregnancy_status != "PREGNANT":
            continue
        row["days_to_calving"] = (state.expected_calving_date - as_of).days if state.expected_calving_date else None
        row["sire"] = clean_text((active.get(row["animal_id"]) or {}).get("sire_code"))
        if within and (row["days_to_calving"] is None or row["days_to_calving"] > int(within)):
            continue
        rows.append(row)
    return ReportResult(
        sections=[Section("pregnancies", "Confirmed Pregnancies and Expected Calvings", PREGNANCY_COLUMNS, rows, primary=True)],
        summary=[Metric("pregnant", "Confirmed Pregnant", len(rows), "integer"),
                 Metric("soon", "Calving within 30 Days",
                        sum(1 for r in rows if r["days_to_calving"] is not None and r["days_to_calving"] <= 30), "integer"),
                 Metric("overdue", "Past Expected Calving",
                        sum(1 for r in rows if r["days_to_calving"] is not None and r["days_to_calving"] < 0), "integer")],
        notes=[f"Expected calving is {POLICY.gestation_days} days after the successful insemination. Expected dry-off is "
               f"{POLICY.dry_off_days_before_calving} days before expected calving."],
    )


# ---------------------------------------------------------------------------
EVENT_COLUMNS = column_set(
    Column("event_date", "Date", "date"),
    Column("animal_id", "Animal ID"),
    Column("event", "Event", "status"),
    Column("result", "Result"),
    Column("technician", "Technician / Inseminator"),
    Column("semen_or_bull", "Semen / Sire"),
    Column("semen_lot", "Semen Lot", "text", "Semen", "optional"),
    Column("semen_supplier", "Semen Supplier", "text", "Semen", "optional"),
    Column("semen_batch_number", "Semen Batch", "text", "Semen", "optional"),
    Column("semen_unit_cost", "Semen Cost (PKR)", "money", "Semen", "optional", total=True),
    Column("notes", "Notes", "text", "Details", "optional"),
)


def _lot_codes(ctx: ReportContext) -> dict[int, str]:
    return ctx.cached("lot_codes", lambda: {lot.id: lot.lot_code for lot in ctx.session.query(SemenLot).all()})


def _event_row(ctx: ReportContext, record: Any) -> dict[str, Any]:
    return {
        "event_date": to_date(record.timestamp),
        "animal_id": str(record.animal_id),
        "event": _event_label(record),
        "result": _label(record.result),
        "technician": clean_text(record.technician),
        "semen_or_bull": clean_text(record.semen_or_bull),
        "semen_lot": _lot_codes(ctx).get(record.semen_lot_id) if record.semen_lot_id else None,
        "semen_supplier": clean_text(record.semen_supplier),
        "semen_batch_number": clean_text(record.semen_batch_number),
        "semen_unit_cost": money(record.semen_unit_cost) if record.semen_unit_cost is not None else None,
        "notes": clean_text(record.notes),
    }


def _events(ctx: ReportContext, predicate) -> list[dict[str, Any]]:
    animal_id = ctx.filter("animal_id")
    technician = ctx.filter("technician")
    rows = []
    for record in breeding_records(ctx):
        if not ctx.period.contains(to_date(record.timestamp)) or not predicate(record):
            continue
        if animal_id and str(record.animal_id) != animal_id:
            continue
        if technician and technician.lower() not in str(record.technician or "").lower():
            continue
        rows.append(_event_row(ctx, record))
    return rows


def build_inseminations(ctx: ReportContext) -> ReportResult:
    rows = _events(ctx, is_insemination)
    cost = sum((r["semen_unit_cost"] for r in rows if r["semen_unit_cost"] is not None), money(0))
    return ReportResult(
        sections=[Section("ai", "Insemination History", EVENT_COLUMNS, rows,
                          {"_label": "Total", "semen_unit_cost": cost}, primary=True)],
        summary=[Metric("ai", "Inseminations", len(rows), "integer"),
                 Metric("animals", "Animals Served", len({r["animal_id"] for r in rows}), "integer"),
                 Metric("cost", "Semen Cost", cost, "money")],
    )


def build_calvings(ctx: ReportContext) -> ReportResult:
    rows = _events(ctx, is_calving)
    calves: dict[tuple[str, date | None], list[str]] = {}
    for animal in ctx.animals():
        dam = clean_text(getattr(animal, "dam_id", None))
        if dam:
            calves.setdefault((dam, to_date(animal.date_of_birth)), []).append(
                f"{animal.animal_id} ({(clean_text(animal.sex) or 'sex not recorded').title()})")
    for row in rows:
        row["calves"] = ", ".join(calves.get((row["animal_id"], row["event_date"]), [])) or None
    columns = column_set(
        Column("event_date", "Calving Date", "date"), Column("animal_id", "Dam ID"),
        Column("calves", "Calf Registered"), Column("result", "Outcome"),
        Column("technician", "Attended By", "text", "Details", "optional"),
        Column("notes", "Notes", "text", "Details", "optional"))
    return ReportResult(
        sections=[Section("calvings", "Calving History", columns, rows, primary=True)],
        summary=[Metric("calvings", "Calvings", len(rows), "integer"),
                 Metric("calves", "Calves Registered", sum(len(v) for k, v in calves.items()
                                                           if any(r["animal_id"] == k[0] and r["event_date"] == k[1] for r in rows)), "integer")],
    )


def build_losses(ctx: ReportContext) -> ReportResult:
    rows = _events(ctx, lambda r: normalize_event_type(r.event_type) in LOSS_EVENTS)
    by_cycle = {}
    for cycle in cycles(ctx):
        if cycle.get("outcome") in {"PREGNANCY_LOST", "ABORTION", "STILLBIRTH"}:
            by_cycle[(cycle["animal_id"], cycle["outcome_date"])] = cycle
    for row in rows:
        cycle = by_cycle.get((row["animal_id"], row["event_date"].isoformat() if row["event_date"] else None))
        service = to_date(cycle["insemination_date"]) if cycle else None
        row["insemination_date"] = service
        row["days_carried"] = (row["event_date"] - service).days if service and row["event_date"] else None
    columns = column_set(
        Column("event_date", "Date", "date"), Column("animal_id", "Animal ID"), Column("event", "Loss Type", "status"),
        Column("insemination_date", "Insemination Date", "date"), Column("days_carried", "Days Carried", "days"),
        Column("technician", "Recorded By", "text", "Details", "optional"), Column("notes", "Notes"))
    return ReportResult(
        sections=[Section("losses", "Pregnancy Losses", columns, rows, primary=True)],
        summary=[Metric("losses", "Pregnancy Losses", len(rows), "integer")],
    )


def build_animal_history(ctx: ReportContext) -> ReportResult:
    animal_id = ctx.filter("animal_id")
    if animal_id not in ctx.animal_index():
        raise ReportParameterError("Animal ID was not found in the herd register.")
    records = sorted(records_by_animal(ctx).get(animal_id, []), key=lambda r: (to_date(r.timestamp) or date.min, str(r.record_id)))
    rows = [_event_row(ctx, r) for r in records]
    cycle_rows = [{
        "cycle": c["cycle_number"], "service_attempt": c["service_attempt_number"],
        "insemination_date": to_date(c["insemination_date"]), "sire": clean_text(c.get("sire_code")),
        "inseminator": clean_text(c.get("inseminator")),
        "pregnancy_confirmation_date": to_date(c.get("pregnancy_confirmation_date")),
        "outcome": _label(c.get("outcome")) or _label(c["status"].replace("ACTIVE_", "In progress: ")),
        "outcome_date": to_date(c.get("outcome_date")),
    } for c in cycles(ctx) if c["animal_id"] == animal_id]
    cycle_columns = column_set(
        Column("cycle", "Cycle", "integer"), Column("service_attempt", "Service Attempt", "integer"),
        Column("insemination_date", "Insemination", "date"), Column("sire", "Sire"), Column("inseminator", "Inseminator"),
        Column("pregnancy_confirmation_date", "Pregnancy Confirmed", "date"), Column("outcome", "Outcome", "status"),
        Column("outcome_date", "Outcome Date", "date"))
    state = reproductive_states(ctx, ctx.today).get(animal_id)
    return ReportResult(
        sections=[Section("cycles", "Breeding Cycles", cycle_columns, cycle_rows,
                          empty_message="No insemination cycle is recorded for this animal."),
                  Section("events", f"Reproductive Events: {animal_id}", EVENT_COLUMNS, rows, primary=True)],
        summary=[Metric("status", "Reproductive Status", _label(state.reproductive_status) if state else "No breeding history"),
                 Metric("lactation", "Lactation No.", (state.lactation_number or None) if state else None, "integer"),
                 Metric("cycles", "Insemination Cycles", len(cycle_rows), "integer"),
                 Metric("expected", "Expected Calving", state.expected_calving_date if state else None, "date")],
    )


# ---------------------------------------------------------------------------
REPEAT_COLUMNS = column_set(
    Column("animal_id", "Animal ID"), Column("category", "Category"), Column("breed", "Breed"),
    Column("services", "Services Since Last Calving", "integer"),
    Column("first_service", "First Service", "date"), Column("last_service", "Last Service", "date"),
    Column("last_outcome", "Latest Outcome", "status"), Column("current_status", "Reproductive Status", "status"),
)


def build_repeat_breeders(ctx: ReportContext) -> ReportResult:
    minimum = int(ctx.filter("minimum_services") or REPEAT_BREEDER_SERVICES)
    status_by_animal = {r["animal_id"]: r for r in _status_rows(ctx, ctx.period.as_of)}
    runs: dict[str, list[dict[str, Any]]] = {}
    for cycle in cycles(ctx):
        run = runs.setdefault(cycle["animal_id"], [])
        if cycle["service_attempt_number"] == 1:
            run.clear()
        run.append(cycle)
    rows = []
    for animal_id, run in runs.items():
        status = status_by_animal.get(animal_id)
        if status is None or len(run) < minimum:
            continue
        if status["_state"] is not None and status["_state"].pregnancy_status == "PREGNANT":
            continue
        rows.append({
            "animal_id": animal_id, "category": status["category"], "breed": status["breed"],
            "services": len(run), "first_service": to_date(run[0]["insemination_date"]),
            "last_service": to_date(run[-1]["insemination_date"]),
            "last_outcome": _label(run[-1].get("outcome")) or "Awaiting diagnosis",
            "current_status": status["reproductive_status"],
        })
    return ReportResult(
        sections=[Section("repeat", "Repeat Breeders", REPEAT_COLUMNS, rows, primary=True)],
        summary=[Metric("animals", "Repeat Breeders", len(rows), "integer")],
        notes=[f"Listed: current breeding females that are not pregnant after {minimum} or more inseminations since "
               "their last calving. Service attempts are counted by the breeding-cycle authority."],
    )


PERFORMANCE_COLUMNS = column_set(
    Column("key", "Name"),
    Column("cycles", "Inseminations", "integer", total=True),
    Column("documented_outcomes", "With Known Outcome", "integer", total=True),
    Column("conceptions", "Conceptions", "integer", total=True),
    Column("negative_pd", "Not Pregnant", "integer", total=True),
    Column("pregnancy_losses", "Pregnancy Losses", "integer", total=True),
    Column("calvings", "Calvings", "integer", total=True),
    Column("conception_rate_percent", "Conception Rate (%)", "percent"),
    Column("loss_rate_per_conception_percent", "Loss per Conception (%)", "percent", "Rates", "optional"),
    Column("total_semen_cost", "Semen Cost (PKR)", "money", "Cost", total=True),
    Column("cost_per_conception", "Cost per Conception (PKR)", "money", "Cost"),
)


def build_performance(ctx: ReportContext) -> ReportResult:
    key = ctx.preset["group_by"]
    selected = [c for c in cycles(ctx) if ctx.period.contains(to_date(c["insemination_date"]))]
    if key == "semen_lot_id":
        codes = _lot_codes(ctx)
        selected = [{**c, "semen_lot_id": codes.get(c.get("semen_lot_id"), None) or "No semen lot recorded"} for c in selected]
    rows = BreedingAnalyticsService._group(selected, key)
    for row in rows:
        row["key"] = "Not recorded" if row["key"] == "UNKNOWN" else row["key"]
        row["total_semen_cost"] = money(row["total_semen_cost"])
        row["cost_per_conception"] = money(row["cost_per_conception"]) if row["cost_per_conception"] is not None else None
    totals = {"_label": "Total", **{k: sum(r[k] for r in rows) for k in
                                    ("cycles", "documented_outcomes", "conceptions", "negative_pd", "pregnancy_losses", "calvings")},
              "total_semen_cost": sum((r["total_semen_cost"] for r in rows), money(0))}
    totals["conception_rate_percent"] = BreedingAnalyticsService._rate(totals["conceptions"], totals["documented_outcomes"])
    title = ctx.definition.title
    return ReportResult(
        sections=[Section("performance", title, PERFORMANCE_COLUMNS, rows, totals, primary=True)],
        summary=[Metric("ai", "Inseminations", totals["cycles"], "integer"),
                 Metric("rate", "Conception Rate", totals["conception_rate_percent"], "percent",
                        "Conceptions divided by inseminations with a known outcome")],
        notes=["Inseminations are selected by insemination date. Conception rate uses only inseminations whose "
               "outcome is documented, so recent services awaiting diagnosis do not depress the rate."],
    )


# ---------------------------------------------------------------------------
SEMEN_COLUMNS = column_set(
    Column("lot_code", "Semen Lot"), Column("sire", "Sire"), Column("breed", "Breed"),
    Column("semen_type", "Semen Type"), Column("supplier", "Supplier"),
    Column("purchase_date", "Purchased", "date"), Column("expiry_date", "Expiry", "date"),
    Column("purchased", "Straws Purchased", "integer", total=True),
    Column("used", "Straws Used", "integer", total=True),
    Column("adjusted", "Other Movements", "integer", "Stock", "optional", total=True),
    Column("on_hand", "Straws on Hand", "integer", total=True),
    Column("unit_cost", "Cost / Straw (PKR)", "rate"),
    Column("stock_value", "Stock Value (PKR)", "money", total=True),
    Column("storage_location", "Storage", "text", "Details", "optional"),
    Column("batch_number", "Batch No.", "text", "Details", "optional"),
    Column("expiry_position", "Expiry Position", "status"),
)


def build_semen_inventory(ctx: ReportContext) -> ReportResult:
    movements: dict[int, dict[str, int]] = {}
    for lot_id, kind, quantity in ctx.session.query(
        SemenStockMovement.semen_lot_id, SemenStockMovement.movement_type,
        func.coalesce(func.sum(SemenStockMovement.signed_quantity), 0),
    ).group_by(SemenStockMovement.semen_lot_id, SemenStockMovement.movement_type).all():
        movements.setdefault(lot_id, {})[str(kind).upper()] = int(quantity)
    only_stock = ctx.flag("only_in_stock")
    rows = []
    for lot in ctx.session.query(SemenLot).order_by(SemenLot.lot_code).all():
        split = movements.get(lot.id, {})
        on_hand = sum(split.values())
        used = -split.get("AI_CONSUMPTION", 0)
        purchased = split.get("PURCHASE", 0)
        if only_stock and on_hand <= 0:
            continue
        expiry = lot.expiry_date
        rows.append({
            "lot_code": lot.lot_code, "sire": clean_text(lot.bull_name) or lot.sire_code, "breed": clean_text(lot.breed),
            "semen_type": _label(lot.semen_type), "supplier": clean_text(lot.supplier),
            "purchase_date": lot.purchase_date, "expiry_date": expiry,
            "purchased": purchased, "used": used,
            "adjusted": on_hand - purchased + used, "on_hand": on_hand,
            "unit_cost": float(lot.unit_cost), "stock_value": money(float(lot.unit_cost) * max(on_hand, 0)),
            "storage_location": clean_text(lot.storage_location), "batch_number": clean_text(lot.batch_number),
            "expiry_position": None if expiry is None else "Expired" if expiry < ctx.today
            else "Expires within 90 days" if (expiry - ctx.today).days <= 90 else "In date",
        })
    totals = {"_label": "Total", **{k: sum(r[k] for r in rows) for k in ("purchased", "used", "adjusted", "on_hand")},
              "stock_value": sum((r["stock_value"] for r in rows), money(0))}
    return ReportResult(
        sections=[Section("semen", "Semen Inventory and Usage", SEMEN_COLUMNS, rows, totals, primary=True)],
        summary=[Metric("on_hand", "Straws on Hand", totals["on_hand"], "integer"),
                 Metric("value", "Stock Value", totals["stock_value"], "money"),
                 Metric("expired", "Expired Lots with Stock",
                        sum(1 for r in rows if r["expiry_position"] == "Expired" and r["on_hand"] > 0), "integer")],
        notes=["Straws on Hand is the sum of the semen stock movement ledger for each lot."],
    )


def _definition(report_id, title, purpose, builder, **kwargs) -> ReportDefinition:
    kwargs.setdefault("authority", "Breeding event ledger via the reproductive-state and breeding-cycle authorities")
    return ReportDefinition(id=report_id, area=AREA, title=title, purpose=purpose,
                            permission=PERMISSION, builder=builder, **kwargs)


TECHNICIAN_FILTER = Filter("technician", "Technician contains", "text")

REPORTS: tuple[ReportDefinition, ...] = (
    _definition("breed-status", "Breeding Status",
                "The reproductive position of every breeding female: open, bred, pregnant, with key dates.",
                build_status, period="as_of", columns=STATUS_COLUMNS, default_sort=("animal_id", "asc"), basis="CALCULATED",
                filters=(BREED_FILTER, Filter("reproductive_status", "Reproductive Status", options=(
                    ("OPEN", "Open"), ("BRED", "Bred"), ("PREGNANT", "Pregnant"), ("LACTATING", "Lactating"),
                    ("DRY_OFF", "Dry Off"), ("NO_BREEDING_HISTORY", "No breeding history"))))),
    _definition("breed-due-for-ai", "Animals Due for AI",
                "Open breeding females that have cleared the voluntary waiting period and can be inseminated.",
                build_due_for_ai, period="as_of", columns=DUE_AI_COLUMNS, default_sort=("days_since_vwp", "desc"),
                basis="CALCULATED", filters=(BREED_FILTER,), empty_message="No animal is currently due for AI."),
    _definition("breed-pd-due", "Pregnancy Diagnosis Due",
                "Inseminated animals whose pregnancy diagnosis is due or overdue.",
                build_pd_due, period="as_of", columns=PD_DUE_COLUMNS, default_sort=("pd_due_date", "asc"), basis="CALCULATED",
                filters=(BREED_FILTER, Filter("only_due", "Only due and overdue", "toggle", default=True)),
                empty_message="No pregnancy diagnosis is due."),
    _definition("breed-pregnancies", "Confirmed Pregnancies & Expected Calvings",
                "Confirmed pregnant animals with days pregnant, expected dry-off and expected calving dates.",
                build_pregnancies, period="as_of", columns=PREGNANCY_COLUMNS, default_sort=("expected_calving_date", "asc"),
                basis="CALCULATED",
                filters=(BREED_FILTER, Filter("calving_within", "Calving within", options=(
                    ("14", "14 days"), ("30", "30 days"), ("60", "60 days"), ("90", "90 days"))))),
    _definition("breed-inseminations", "Insemination History",
                "Every insemination in the period with technician, semen, lot and semen cost.",
                build_inseminations, period="range", columns=EVENT_COLUMNS, default_sort=("event_date", "asc"),
                filters=(ANIMAL_FILTER, TECHNICIAN_FILTER)),
    _definition("breed-calvings", "Calving History",
                "Calvings in the period with the calves registered from each.",
                build_calvings, period="range", default_sort=("event_date", "asc"), filters=(ANIMAL_FILTER,)),
    _definition("breed-pregnancy-losses", "Pregnancy Losses",
                "Pregnancy losses, abortions and stillbirths with the insemination they followed.",
                build_losses, period="range", default_sort=("event_date", "asc"), filters=(ANIMAL_FILTER,)),
    _definition("breed-repeat-breeders", "Repeat Breeders",
                "Breeding females still not pregnant after repeated inseminations since their last calving.",
                build_repeat_breeders, period="as_of", columns=REPEAT_COLUMNS, default_sort=("services", "desc"), basis="DERIVED",
                filters=(Filter("minimum_services", "Minimum services", options=(("2", "2"), ("3", "3"), ("4", "4")), default="3"),),
                empty_message="No repeat breeder at the selected threshold."),
    _definition("breed-technician-performance", "AI Technician Performance",
                "Inseminations, conceptions and conception rate by technician.",
                build_performance, period="range", preset={"group_by": "inseminator"}, columns=PERFORMANCE_COLUMNS,
                default_period="YEAR_TO_DATE", basis="CALCULATED"),
    _definition("breed-sire-performance", "Sire Performance",
                "Inseminations, conceptions and conception rate by sire.",
                build_performance, period="range", preset={"group_by": "sire_code"}, columns=PERFORMANCE_COLUMNS,
                default_period="YEAR_TO_DATE", basis="CALCULATED"),
    _definition("breed-semen-lot-performance", "Semen Lot Performance",
                "Inseminations, conceptions, conception rate and cost per conception by semen lot.",
                build_performance, period="range", preset={"group_by": "semen_lot_id"}, columns=PERFORMANCE_COLUMNS,
                default_period="YEAR_TO_DATE", basis="CALCULATED"),
    _definition("breed-semen-inventory", "Semen Inventory & Usage",
                "Straws purchased, used and on hand for every semen lot, with stock value and expiry position.",
                build_semen_inventory, columns=SEMEN_COLUMNS, default_sort=("lot_code", "asc"),
                filters=(Filter("only_in_stock", "Only lots with stock", "toggle", default=False),),
                authority="Semen lot register and semen stock movement ledger"),
    _definition("breed-animal-history", "Reproductive History by Animal",
                "The complete breeding cycles and reproductive events of one animal.",
                build_animal_history, columns=EVENT_COLUMNS, filters=(REQUIRED_ANIMAL,), default_sort=("event_date", "asc")),
)
