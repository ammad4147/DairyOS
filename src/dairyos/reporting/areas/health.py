"""Health and vaccination reporting.

Health and Vaccination are separate DairyOS authorities and are reported
separately:

* Health: ``HealthCase`` and ``TreatmentRecord``. The persisted treatment
  record is the durable milk-withdrawal authority: milk is under withdrawal
  from ``treated_at`` until ``milk_withdrawal_until``.
* Vaccination: ``VaccinationRecord``. A vaccination is due when it is not
  VOID, has a scheduled date and has not been administered, the same rule the
  Vaccination tab applies.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import Any

from dairyos.data.models.health_case import HealthCase
from dairyos.data.models.treatment_record import TreatmentRecord
from dairyos.data.models.vaccination_record import VaccinationRecord
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.reporting.context import (
    ReportContext,
    ReportParameterError,
    clean_text,
    to_date,
    upper,
)
from dairyos.reporting.definitions import (
    Column,
    Filter,
    Metric,
    ReportDefinition,
    ReportResult,
    Section,
)
from dairyos.reporting.engine import column_set

AREA = "health"
PERMISSION = "health.view"
ANIMAL_FILTER = Filter("animal_id", "Animal ID", "animal")
REQUIRED_ANIMAL = Filter("animal_id", "Animal ID", "animal", required=True)
SEVERITY_FILTER = Filter("severity", "Severity", options_source="health_severities")


def _label(value: Any) -> str | None:
    text = clean_text(value)
    return text.replace("_", " ").title() if text else None


def _bounds(ctx: ReportContext) -> tuple[datetime, datetime]:
    return (datetime.combine(ctx.period.start, time.min),
            datetime.combine(ctx.period.end + timedelta(days=1), time.min))


# ---------------------------------------------------------------------------
CASE_COLUMNS = column_set(
    Column("case_id", "Case No."),
    Column("animal_id", "Animal ID"),
    Column("opened_date", "Opened", "date"),
    Column("severity", "Severity", "status"),
    Column("diagnosis", "Diagnosis"),
    Column("status", "Status", "status"),
    Column("days_open", "Days Open", "days"),
    Column("treatments", "Treatments", "integer"),
    Column("follow_up_due", "Follow-Up Due", "date"),
    Column("withdrawal_until", "Milk Withdrawal Until", "date"),
    Column("resolved_date", "Resolved", "date", "Resolution", "optional"),
    Column("resolution", "Resolution", "text", "Resolution", "optional"),
    Column("opened_by", "Opened By", "text", "Details", "optional"),
    Column("resolved_by", "Resolved By", "text", "Details", "optional"),
    Column("notes", "Notes", "text", "Details", "optional"),
)


def _case_row(ctx: ReportContext, case: HealthCase, treatment_counts: dict[int, int]) -> dict[str, Any]:
    opened = to_date(case.opened_at)
    resolved = to_date(case.resolved_at)
    closing = resolved or ctx.today
    return {
        "case_id": clean_text(case.case_id), "animal_id": str(case.animal_id), "opened_date": opened,
        "severity": _label(case.severity), "diagnosis": clean_text(case.diagnosis),
        "status": _label(case.status) or "Open",
        "days_open": (closing - opened).days if opened else None,
        "treatments": treatment_counts.get(case.id, 0),
        "follow_up_due": to_date(case.follow_up_due_at), "withdrawal_until": to_date(case.withdrawal_until),
        "resolved_date": resolved, "resolution": clean_text(case.resolution),
        "opened_by": clean_text(case.opened_by), "resolved_by": clean_text(case.resolved_by),
        "notes": clean_text(case.notes),
    }


def _treatment_counts(ctx: ReportContext) -> dict[int, int]:
    from sqlalchemy import func

    return {case_id: count for case_id, count in ctx.session.query(
        TreatmentRecord.health_case_id, func.count(TreatmentRecord.id)
    ).filter(TreatmentRecord.health_case_id.isnot(None)).group_by(TreatmentRecord.health_case_id).all()}


def build_active_cases(ctx: ReportContext) -> ReportResult:
    counts = _treatment_counts(ctx)
    severity = ctx.filter("severity")
    rows = []
    for case in ctx.session.query(HealthCase).filter(HealthCase.status != "RESOLVED").order_by(HealthCase.opened_at).all():
        if upper(case.status) == "VOID":
            continue
        if severity and upper(case.severity) != upper(severity):
            continue
        rows.append(_case_row(ctx, case, counts))
    overdue = sum(1 for r in rows if r["follow_up_due"] and r["follow_up_due"] < ctx.today)
    return ReportResult(
        sections=[Section("cases", "Active Health Cases", CASE_COLUMNS, rows, primary=True)],
        summary=[Metric("open", "Open Cases", len(rows), "integer"),
                 Metric("animals", "Animals Affected", len({r["animal_id"] for r in rows}), "integer"),
                 Metric("followup", "Follow-Up Overdue", overdue, "integer")],
    )


def build_cases_by_period(ctx: ReportContext) -> ReportResult:
    start, end = _bounds(ctx)
    counts = _treatment_counts(ctx)
    severity, animal_id = ctx.filter("severity"), ctx.filter("animal_id")
    query = ctx.session.query(HealthCase).filter(HealthCase.opened_at >= start, HealthCase.opened_at < end)
    if animal_id:
        query = query.filter(HealthCase.animal_id == animal_id)
    rows = [_case_row(ctx, c, counts) for c in query.order_by(HealthCase.opened_at).all()
            if not severity or upper(c.severity) == upper(severity)]
    by_diagnosis: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["diagnosis"] or "Diagnosis not recorded"
        line = by_diagnosis.setdefault(key, {"diagnosis": key, "cases": 0, "resolved": 0, "open": 0})
        line["cases"] += 1
        line["resolved" if row["status"] == "Resolved" else "open"] += 1
    diagnosis_columns = column_set(Column("diagnosis", "Diagnosis"), Column("cases", "Cases", "integer", total=True),
                                   Column("resolved", "Resolved", "integer", total=True),
                                   Column("open", "Still Open", "integer", total=True))
    diagnosis_rows = sorted(by_diagnosis.values(), key=lambda r: (-r["cases"], r["diagnosis"]))
    return ReportResult(
        sections=[Section("diagnoses", "Cases by Diagnosis", diagnosis_columns, diagnosis_rows,
                          {"_label": "Total", "cases": len(rows), "resolved": sum(r["resolved"] for r in diagnosis_rows),
                           "open": sum(r["open"] for r in diagnosis_rows)}),
                  Section("cases", "Health Cases Opened in Period", CASE_COLUMNS, rows, primary=True)],
        summary=[Metric("cases", "Cases Opened", len(rows), "integer"),
                 Metric("resolved", "Resolved", sum(1 for r in rows if r["status"] == "Resolved"), "integer"),
                 Metric("animals", "Animals Affected", len({r["animal_id"] for r in rows}), "integer")],
    )


# ---------------------------------------------------------------------------
TREATMENT_COLUMNS = column_set(
    Column("treated_date", "Treated", "date"),
    Column("animal_id", "Animal ID"),
    Column("diagnosis", "Diagnosis"),
    Column("medicine", "Medicine"),
    Column("dose", "Dose"),
    Column("treated_by", "Treated By"),
    Column("withdrawal_days", "Withdrawal (Days)", "days"),
    Column("withdrawal_until", "Milk Withdrawal Until", "date"),
    Column("withdrawal_position", "Withdrawal", "status"),
    Column("case_id", "Health Case", "text", "Details", "optional"),
    Column("withdrawal_basis", "Withdrawal Basis", "text", "Details", "optional"),
    Column("notes", "Notes", "text", "Details", "optional"),
)


def _case_codes(ctx: ReportContext) -> dict[int, str]:
    return ctx.cached("case_codes", lambda: {c.id: c.case_id for c in ctx.session.query(HealthCase.id, HealthCase.case_id).all()})


def _treatment_row(ctx: ReportContext, record: TreatmentRecord, at: datetime) -> dict[str, Any]:
    until = record.milk_withdrawal_until
    if until is None or not record.milk_withdrawal_days:
        position = "No withdrawal"
    elif record.treated_at and record.treated_at <= at < until:
        position = "Active"
    else:
        position = "Completed" if until <= at else "Not started"
    source = clean_text(record.withdrawal_source)
    return {
        "treated_date": to_date(record.treated_at), "animal_id": str(record.animal_id),
        "diagnosis": clean_text(record.diagnosis), "medicine": clean_text(record.medicine),
        "dose": clean_text(record.dose), "treated_by": clean_text(record.treated_by),
        "withdrawal_days": record.milk_withdrawal_days, "withdrawal_until": to_date(until),
        "withdrawal_position": position,
        "case_id": _case_codes(ctx).get(record.health_case_id) if record.health_case_id else None,
        "withdrawal_basis": None if not source else "Drug reference table" if source == "reference_table" else _label(source),
        "notes": clean_text(record.notes),
        "_until": until,
    }


def _now(ctx: ReportContext) -> datetime:
    """The farm clock as the naive UTC instant DairyOS persists treatment
    times in. Derived from the operational-date authority, never from a
    second clock."""

    moment = ctx.generated_at
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(UTC).replace(tzinfo=None)


def build_treatments(ctx: ReportContext) -> ReportResult:
    start, end = _bounds(ctx)
    animal_id = ctx.filter("animal_id")
    query = ctx.session.query(TreatmentRecord).filter(TreatmentRecord.treated_at >= start, TreatmentRecord.treated_at < end)
    if animal_id:
        query = query.filter(TreatmentRecord.animal_id == animal_id)
    medicine = ctx.filter("medicine")
    rows = [_treatment_row(ctx, r, _now(ctx)) for r in query.order_by(TreatmentRecord.treated_at).all()
            if not medicine or medicine.lower() in str(r.medicine or "").lower()]
    return ReportResult(
        sections=[Section("treatments", "Treatment History", TREATMENT_COLUMNS, rows, primary=True)],
        summary=[Metric("treatments", "Treatments", len(rows), "integer"),
                 Metric("animals", "Animals Treated", len({r["animal_id"] for r in rows}), "integer"),
                 Metric("withdrawal", "With Milk Withdrawal", sum(1 for r in rows if r["withdrawal_position"] != "No withdrawal"), "integer")],
    )


WITHDRAWAL_COLUMNS = column_set(
    Column("animal_id", "Animal ID"), Column("medicine", "Medicine"), Column("diagnosis", "Diagnosis"),
    Column("treated_date", "Treated", "date"), Column("withdrawal_days", "Withdrawal (Days)", "days"),
    Column("withdrawal_until", "Withhold Milk Until", "date"), Column("days_remaining", "Days Remaining", "days"),
    Column("treated_by", "Treated By", "text", "Details", "optional"),
    Column("withdrawal_basis", "Withdrawal Basis", "text", "Details", "optional"),
)


def build_withdrawal_status(ctx: ReportContext) -> ReportResult:
    now = _now(ctx)
    rows = []
    for record in ctx.session.query(TreatmentRecord).filter(TreatmentRecord.milk_withdrawal_until > now).all():
        row = _treatment_row(ctx, record, now)
        if row["withdrawal_position"] != "Active":
            continue
        row["days_remaining"] = max(0, (row["withdrawal_until"] - ctx.today).days) if row["withdrawal_until"] else None
        rows.append(row)
    return ReportResult(
        sections=[Section("withdrawal", "Animals Under Milk Withdrawal", WITHDRAWAL_COLUMNS, rows, primary=True)],
        summary=[Metric("animals", "Animals Under Withdrawal", len({r["animal_id"] for r in rows}), "integer"),
                 Metric("treatments", "Active Withdrawals", len(rows), "integer")],
        notes=["Milk from these animals must be withheld. The persisted treatment record is the withdrawal authority."],
    )


def build_withdrawal_history(ctx: ReportContext) -> ReportResult:
    start, end = _bounds(ctx)
    now = _now(ctx)
    rows = []
    for record in ctx.session.query(TreatmentRecord).filter(
        TreatmentRecord.milk_withdrawal_until.isnot(None),
        TreatmentRecord.treated_at < end, TreatmentRecord.milk_withdrawal_until >= start,
    ).order_by(TreatmentRecord.treated_at).all():
        if not record.milk_withdrawal_days:
            continue
        rows.append(_treatment_row(ctx, record, now))
    return ReportResult(
        sections=[Section("withdrawals", "Withdrawal History", TREATMENT_COLUMNS, rows, primary=True)],
        summary=[Metric("withdrawals", "Withdrawal Periods", len(rows), "integer"),
                 Metric("days", "Withdrawal Days Imposed", sum(int(r["withdrawal_days"] or 0) for r in rows), "days")],
        notes=["Listed: every withdrawal period that overlaps the selected dates."],
    )


# ---------------------------------------------------------------------------
VACCINATION_COLUMNS = column_set(
    Column("animal_id", "Animal ID"), Column("vaccine", "Vaccine"), Column("dose", "Dose"),
    Column("scheduled_date", "Scheduled / Next Due", "date"), Column("administered_date", "Administered", "date"),
    Column("position", "Position", "status"), Column("days", "Days Overdue / To Go", "days"),
    Column("veterinarian", "Veterinarian", "text", "Details", "optional"),
    Column("batch_number", "Vaccine Batch", "text", "Details", "optional"),
    Column("recorded_by", "Recorded By", "text", "Details", "optional"),
    Column("notes", "Notes", "text", "Details", "optional"),
)


def _vaccination_row(ctx: ReportContext, record: VaccinationRecord) -> dict[str, Any]:
    scheduled, given = record.next_due_date, record.administered_date
    if upper(record.status) == "VOID" or upper(record.schedule_status) == "VOID":
        position, days = "VOID", None
    elif given is not None:
        position, days = "Administered", None
    elif scheduled is None:
        position, days = "Not scheduled", None
    else:
        gap = (scheduled - ctx.period.as_of).days
        position = "Overdue" if gap < 0 else "Due today" if gap == 0 else "Upcoming"
        days = abs(gap)
    return {"animal_id": str(record.animal_id), "vaccine": clean_text(record.vaccine), "dose": clean_text(record.dose),
            "scheduled_date": scheduled, "administered_date": given, "position": position, "days": days,
            "veterinarian": clean_text(record.veterinarian), "batch_number": clean_text(record.batch_number),
            "recorded_by": clean_text(record.operator), "notes": clean_text(record.notes)}


def build_vaccination_due(ctx: ReportContext) -> ReportResult:
    horizon = int(ctx.filter("within_days") or 30)
    limit = ctx.period.as_of + timedelta(days=horizon)
    vaccine, animals = ctx.filter("vaccine"), ctx.animal_index()
    rows = []
    for record in ctx.session.query(VaccinationRecord).filter(
        VaccinationRecord.administered_date.is_(None), VaccinationRecord.next_due_date.isnot(None),
        VaccinationRecord.next_due_date <= limit,
    ).order_by(VaccinationRecord.next_due_date).all():
        row = _vaccination_row(ctx, record)
        if row["position"] == "VOID":
            continue
        if vaccine and vaccine.lower() not in (row["vaccine"] or "").lower():
            continue
        animal = animals.get(row["animal_id"])
        if animal is not None and not bool(getattr(animal, "active", True)):
            continue
        rows.append(row)
    return ReportResult(
        sections=[Section("due", "Vaccination Due", VACCINATION_COLUMNS, rows, primary=True)],
        summary=[Metric("overdue", "Overdue", sum(1 for r in rows if r["position"] == "Overdue"), "integer"),
                 Metric("today", "Due Today", sum(1 for r in rows if r["position"] == "Due today"), "integer"),
                 Metric("upcoming", f"Due within {horizon} Days", sum(1 for r in rows if r["position"] == "Upcoming"), "integer")],
        notes=["Same rule as the Vaccination tab: not VOID, scheduled, and not yet administered. Exited animals are omitted."],
    )


def build_vaccination_history(ctx: ReportContext) -> ReportResult:
    vaccine, animal_id = ctx.filter("vaccine"), ctx.filter("animal_id")
    query = ctx.session.query(VaccinationRecord).filter(
        VaccinationRecord.administered_date >= ctx.period.start, VaccinationRecord.administered_date <= ctx.period.end)
    if animal_id:
        query = query.filter(VaccinationRecord.animal_id == animal_id)
    rows = []
    for record in query.order_by(VaccinationRecord.administered_date).all():
        row = _vaccination_row(ctx, record)
        if row["position"] == "VOID" or (vaccine and vaccine.lower() not in (row["vaccine"] or "").lower()):
            continue
        rows.append(row)
    by_vaccine: dict[str, int] = {}
    for row in rows:
        by_vaccine[row["vaccine"] or "Vaccine not recorded"] = by_vaccine.get(row["vaccine"] or "Vaccine not recorded", 0) + 1
    vaccine_columns = column_set(Column("vaccine", "Vaccine"), Column("doses", "Doses Administered", "integer", total=True))
    return ReportResult(
        sections=[Section("vaccines", "Doses by Vaccine", vaccine_columns,
                          [{"vaccine": k, "doses": v} for k, v in sorted(by_vaccine.items(), key=lambda kv: -kv[1])],
                          {"_label": "Total", "doses": len(rows)}),
                  Section("history", "Vaccination History", VACCINATION_COLUMNS, rows, primary=True)],
        summary=[Metric("doses", "Doses Administered", len(rows), "integer"),
                 Metric("animals", "Animals Vaccinated", len({r["animal_id"] for r in rows}), "integer")],
    )


def build_animal_history(ctx: ReportContext) -> ReportResult:
    animal_id = ctx.filter("animal_id")
    if animal_id not in ctx.animal_index():
        raise ReportParameterError("Animal ID was not found in the herd register.")
    counts, now = _treatment_counts(ctx), _now(ctx)
    cases = [_case_row(ctx, c, counts) for c in ctx.session.query(HealthCase).filter(
        HealthCase.animal_id == animal_id).order_by(HealthCase.opened_at).all()]
    treatments = [_treatment_row(ctx, r, now) for r in ctx.session.query(TreatmentRecord).filter(
        TreatmentRecord.animal_id == animal_id).order_by(TreatmentRecord.treated_at).all()]
    vaccinations = [row for row in (_vaccination_row(ctx, r) for r in ctx.session.query(VaccinationRecord).filter(
        VaccinationRecord.animal_id == animal_id).order_by(VaccinationRecord.id).all()) if row["position"] != "VOID"]
    return ReportResult(
        sections=[Section("cases", "Health Cases", CASE_COLUMNS, cases, empty_message="No health case is recorded for this animal."),
                  Section("treatments", f"Treatments: {animal_id}", TREATMENT_COLUMNS, treatments, primary=True),
                  Section("vaccinations", "Vaccinations", VACCINATION_COLUMNS, vaccinations,
                          empty_message="No vaccination is recorded for this animal.")],
        summary=[Metric("cases", "Health Cases", len(cases), "integer"), Metric("treatments", "Treatments", len(treatments), "integer"),
                 Metric("vaccinations", "Vaccinations", len(vaccinations), "integer"),
                 Metric("withdrawal", "Under Withdrawal Now",
                        "Yes" if any(t["withdrawal_position"] == "Active" for t in treatments) else "No")],
        notes=["This history agrees with the Health section of the Animal Passport, which reads the same records."],
    )


CLINICAL_INVENTORY_COLUMNS = column_set(
    Column("date", "Date", "date"), Column("item", "Item"),
    Column("movement", "Movement", "status"), Column("quantity_in", "In", "number", total=True),
    Column("quantity_out", "Out", "number", total=True), Column("unit", "Unit"),
    Column("source", "Source"), Column("recorded_by", "Recorded By", "text", "Details", "optional"),
    Column("notes", "Notes", "text", "Details", "optional"),
)


def build_clinical_inventory(ctx: ReportContext) -> ReportResult:
    start, end = _bounds(ctx)
    item_filter = ctx.filter("item")
    source_types = {"CLINICAL_RECEIPT", "TREATMENT_CONSUMPTION", "VACCINATION_CONSUMPTION"}
    rows = []
    for record in ctx.session.query(InventoryTransaction).filter(
        InventoryTransaction.recorded_at >= start,
        InventoryTransaction.recorded_at < end,
    ).order_by(InventoryTransaction.recorded_at, InventoryTransaction.id).all():
        if upper(record.source_type) not in source_types:
            continue
        if item_filter and item_filter.lower() not in str(record.item or "").lower():
            continue
        signed = float(record.signed_quantity or 0)
        source = {
            "CLINICAL_RECEIPT": "Clinical inventory receipt",
            "TREATMENT_CONSUMPTION": "Treatment consumption",
            "VACCINATION_CONSUMPTION": "Vaccination consumption",
        }[upper(record.source_type)]
        rows.append({
            "date": to_date(record.recorded_at), "item": clean_text(record.item),
            "movement": _label(record.movement_type),
            "quantity_in": round(signed, 3) if signed > 0 else None,
            "quantity_out": round(-signed, 3) if signed < 0 else None,
            "unit": clean_text(record.unit), "source": source,
            "recorded_by": clean_text(record.recorded_by), "notes": clean_text(record.notes),
        })
    return ReportResult(
        sections=[Section("clinical_inventory", "Clinical Inventory Movements", CLINICAL_INVENTORY_COLUMNS, rows,
                          {"_label": "Total", "quantity_in": round(sum(r["quantity_in"] or 0 for r in rows), 3),
                           "quantity_out": round(sum(r["quantity_out"] or 0 for r in rows), 3)}, primary=True)],
        summary=[Metric("movements", "Movements", len(rows), "integer"),
                 Metric("items", "Items", len({r["item"] for r in rows}), "integer")],
        notes=["Clinical inventory is operator-recorded. Treatment and vaccination events consume stock only when explicitly linked; no dose is inferred from free text.",
               "Quantities are displayed by movement; filter to one item before interpreting totals when units differ."],
    )


def _definition(report_id, title, purpose, builder, **kwargs) -> ReportDefinition:
    kwargs.setdefault("authority", "Health cases and treatment records")
    return ReportDefinition(id=report_id, area=AREA, title=title, purpose=purpose,
                            permission=PERMISSION, builder=builder, **kwargs)


VACCINE_FILTER = Filter("vaccine", "Vaccine contains", "text")

REPORTS: tuple[ReportDefinition, ...] = (
    _definition("health-active-cases", "Active Health Cases",
                "Open health cases with severity, days open, treatments given and follow-up due.",
                build_active_cases, columns=CASE_COLUMNS, default_sort=("days_open", "desc"), filters=(SEVERITY_FILTER,),
                empty_message="There is no open health case."),
    _definition("health-cases-period", "Health Cases by Period",
                "Health cases opened in the period, summarised by diagnosis, with outcome.",
                build_cases_by_period, period="range", columns=CASE_COLUMNS, default_sort=("opened_date", "asc"),
                filters=(ANIMAL_FILTER, SEVERITY_FILTER)),
    _definition("health-treatments", "Treatment History",
                "Treatments given in the period with medicine, dose, who treated and the milk withdrawal imposed.",
                build_treatments, period="range", columns=TREATMENT_COLUMNS, default_sort=("treated_date", "asc"),
                filters=(ANIMAL_FILTER, Filter("medicine", "Medicine contains", "text"))),
    _definition("health-withdrawal-status", "Milk Withdrawal Status",
                "Animals whose milk must be withheld right now, and until when.",
                build_withdrawal_status, columns=WITHDRAWAL_COLUMNS, default_sort=("withdrawal_until", "asc"),
                authority="Persisted treatment records (durable milk-withdrawal authority)",
                empty_message="No animal is under milk withdrawal."),
    _definition("health-withdrawal-history", "Withdrawal History",
                "Every milk withdrawal period overlapping the selected dates.",
                build_withdrawal_history, period="range", columns=TREATMENT_COLUMNS, default_sort=("treated_date", "asc"),
                authority="Persisted treatment records (durable milk-withdrawal authority)"),
    _definition("health-vaccination-due", "Vaccination Due",
                "Scheduled vaccinations that are overdue, due today or due within the chosen horizon.",
                build_vaccination_due, period="as_of", columns=VACCINATION_COLUMNS, default_sort=("scheduled_date", "asc"),
                authority="Vaccination records and schedule",
                filters=(Filter("within_days", "Look ahead", options=(("7", "7 days"), ("14", "14 days"), ("30", "30 days"),
                                                                       ("60", "60 days"), ("90", "90 days")), default="30"),
                         VACCINE_FILTER),
                empty_message="No vaccination is due in the selected horizon."),
    _definition("health-vaccination-history", "Vaccination History",
                "Vaccinations administered in the period, by vaccine and animal.",
                build_vaccination_history, period="range", columns=VACCINATION_COLUMNS, default_sort=("administered_date", "asc"),
                authority="Vaccination records and schedule", filters=(ANIMAL_FILTER, VACCINE_FILTER)),
    _definition("health-animal-history", "Health History by Animal",
                "One animal's health cases, treatments, withdrawals and vaccinations.",
                build_animal_history, columns=TREATMENT_COLUMNS, filters=(REQUIRED_ANIMAL,),
                authority="Health cases, treatment records and vaccination records"),
    _definition("health-clinical-inventory", "Clinical Inventory",
                "Receipts and explicitly linked medicine and vaccination consumption recorded by the operator.",
                build_clinical_inventory, period="range", columns=CLINICAL_INVENTORY_COLUMNS,
                default_sort=("date", "asc"), authority="Clinical inventory movement ledger",
                filters=(Filter("item", "Item contains", "text"),)),
)
