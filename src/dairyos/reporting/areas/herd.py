"""Herd reporting.

Authority: the Animal register, classified by ``AnimalClassificationService``
(the Animal Passport category authority). Exits and mortality come from the
governed ``animal_disposition`` entries of the operational event journal.

Herd category is current state. DairyOS keeps no category history, so these
reports describe the herd as it stands now and never reconstruct a past herd
composition.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import date
from typing import Any

from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.farm.herd.services.animal_classification_service import (
    AnimalClassificationError,
    AnimalClassificationService,
)
from dairyos.reporting.context import ReportContext, age_label, age_months, clean_text, money, to_date, upper
from dairyos.reporting.definitions import Column, Filter, Metric, ReportDefinition, ReportResult, Section
from dairyos.reporting.engine import column_set

AREA = "herd"
PERMISSION = "animals.view"
AUTHORITY = "Animal register classified by the Animal Passport category authority"

CATEGORY_ORDER = ("Milking", "Dry", "Heifer", "Female Calf", "Male Calf", "Bull")
CATEGORY_PLURALS = {
    "Milking": "Milking Cows",
    "Dry": "Dry Cows",
    "Heifer": "Heifers",
    "Female Calf": "Female Calves",
    "Male Calf": "Male Calves",
    "Bull": "Bulls",
}
EXIT_LABELS = {"SOLD": "Sold", "DECEASED": "Deceased", "CULLED": "Culled"}
DIRECTIVE_LABELS = {"NONE": None}


def classify(animal: Any) -> tuple[str | None, bool]:
    """Return ``(category, exited)`` from the Passport category authority."""
    try:
        result = AnimalClassificationService.classify(
            getattr(animal, "lifecycle_status", None), getattr(animal, "sex", None)
        )
    except AnimalClassificationError:
        return None, False
    category = result.category.value
    if category == "Exited":
        return None, True
    return (category if category in CATEGORY_ORDER else None), False


def is_current(animal: Any) -> bool:
    category, exited = classify(animal)
    if exited or category is None:
        return False
    return bool(getattr(animal, "active", True)) and upper(getattr(animal, "status", "ACTIVE")) not in {
        "SOLD", "DECEASED", "CULLED", "INACTIVE", "VOID"}


def _status_label(animal: Any) -> str:
    lifecycle = upper(getattr(animal, "lifecycle_status", None))
    if lifecycle in EXIT_LABELS:
        return EXIT_LABELS[lifecycle]
    status = upper(getattr(animal, "status", "ACTIVE")) or "ACTIVE"
    if status in EXIT_LABELS:
        return EXIT_LABELS[status]
    if not bool(getattr(animal, "active", True)) or status == "INACTIVE":
        return "Inactive"
    return "Active"


def animal_row(animal: Any, as_of: date) -> dict[str, Any]:
    category, _ = classify(animal)
    born = to_date(getattr(animal, "date_of_birth", None))
    directive = upper(getattr(animal, "non_milking_directive", None))
    return {
        "animal_id": clean_text(animal.animal_id),
        "ear_tag": clean_text(getattr(animal, "ear_tag", None)),
        "rfid": clean_text(getattr(animal, "rfid", None)),
        "legacy_animal_id": clean_text(getattr(animal, "legacy_animal_id", None)),
        "category": category,
        "sex": (clean_text(getattr(animal, "sex", None)) or "").title() or None,
        "breed": clean_text(getattr(animal, "breed", None)),
        "date_of_birth": born,
        "age": age_label(born, as_of),
        "age_months": age_months(born, as_of),
        "dam_id": clean_text(getattr(animal, "dam_id", None)),
        "sire_id": clean_text(getattr(animal, "sire_id", None)),
        "production_group": clean_text(getattr(animal, "production_group", None)),
        "location": clean_text(getattr(animal, "location", None)),
        "milking_frequency": clean_text(getattr(animal, "milking_frequency", None))
        if bool(getattr(animal, "is_currently_milking", False)) else None,
        "date_of_acquisition": to_date(getattr(animal, "date_of_acquisition", None)),
        "origin": "Purchased" if getattr(animal, "date_of_acquisition", None) else (
            "Born on farm" if getattr(animal, "dam_id", None) else None),
        "status": _status_label(animal),
        "milking_restriction": None if directive in {"", "NONE"} else directive.replace("_", " ").title(),
        "milking_restriction_reason": clean_text(getattr(animal, "non_milking_reason", None))
        if directive not in {"", "NONE"} else None,
        "milking_restriction_until": to_date(getattr(animal, "non_milking_until", None))
        if directive not in {"", "NONE"} else None,
        "record_created": to_date(getattr(animal, "created_at", None)),
        "record_updated": to_date(getattr(animal, "updated_at", None)),
    }


IDENT = "Identification"
DETAILS = "Animal Details"
FAMILY = "Family"
MANAGE = "Management"
RESTRICT = "Milking Restriction"
ADMIN = "Record Administration"


def _register_columns(*default_keys: str) -> tuple[Column, ...]:
    catalogue = (
        Column("animal_id", "Animal ID", "text", IDENT),
        Column("ear_tag", "Ear Tag", "text", IDENT),
        Column("rfid", "RFID", "text", IDENT),
        Column("legacy_animal_id", "Previous Animal ID", "text", IDENT),
        Column("category", "Category", "text", DETAILS),
        Column("sex", "Sex", "text", DETAILS),
        Column("breed", "Breed", "text", DETAILS),
        Column("date_of_birth", "Date of Birth", "date", DETAILS),
        Column("age", "Age", "text", DETAILS),
        Column("age_months", "Age (Months)", "integer", DETAILS),
        Column("dam_id", "Dam ID", "text", FAMILY),
        Column("sire_id", "Sire ID", "text", FAMILY),
        Column("production_group", "Production Group", "text", MANAGE),
        Column("location", "Location", "text", MANAGE),
        Column("milking_frequency", "Milking Frequency", "text", MANAGE),
        Column("origin", "Origin", "text", MANAGE),
        Column("date_of_acquisition", "Date of Acquisition", "date", MANAGE),
        Column("status", "Status", "status", MANAGE),
        Column("milking_restriction", "Milking Restriction", "text", RESTRICT),
        Column("milking_restriction_reason", "Restriction Reason", "text", RESTRICT),
        Column("milking_restriction_until", "Restricted Until", "date", RESTRICT),
        Column("record_created", "Record Created", "date", ADMIN),
        Column("record_updated", "Record Last Updated", "date", ADMIN),
    )
    out = []
    for column in catalogue:
        tier = "default" if column.key in default_keys else ("advanced" if column.group == ADMIN else "optional")
        out.append(Column(column.key, column.label, column.type, column.group, tier))
    ordered = [c for key in default_keys for c in out if c.key == key]
    ordered += [c for c in out if c.key not in default_keys]
    return column_set(*ordered)


REGISTER_COLUMNS = _register_columns(
    "animal_id", "ear_tag", "category", "sex", "breed", "date_of_birth", "age",
    "production_group", "location", "status")

CATEGORY_DEFAULTS = {
    "Milking": ("animal_id", "ear_tag", "breed", "age", "production_group", "location", "milking_frequency"),
    "Dry": ("animal_id", "ear_tag", "breed", "age", "production_group", "location", "milking_restriction"),
    "Heifer": ("animal_id", "ear_tag", "breed", "date_of_birth", "age", "location", "dam_id"),
    "Female Calf": ("animal_id", "ear_tag", "breed", "date_of_birth", "age", "dam_id", "location"),
    "Male Calf": ("animal_id", "ear_tag", "breed", "date_of_birth", "age", "dam_id", "location"),
    "Bull": ("animal_id", "ear_tag", "breed", "date_of_birth", "age", "location"),
}

BREED_FILTER = Filter("breed", "Breed", options_source="breeds")
GROUP_FILTER = Filter("production_group", "Production Group", options_source="production_groups")
LOCATION_FILTER = Filter("location", "Location", options_source="locations")
CATEGORY_FILTER = Filter("category", "Category", options=tuple((c, CATEGORY_PLURALS[c]) for c in CATEGORY_ORDER))


def _matches(row: dict[str, Any], ctx: ReportContext) -> bool:
    for key in ("breed", "production_group", "location", "category"):
        wanted = ctx.filter(key)
        if wanted and (row.get(key) or "").lower() != wanted.lower():
            return False
    return True


def build_register(ctx: ReportContext) -> ReportResult:
    preset_category = ctx.preset.get("category")
    include_exited = ctx.flag("include_exited") and not preset_category
    rows = []
    unclassified = 0
    for animal in ctx.animals():
        category, exited = classify(animal)
        if exited and not include_exited:
            continue
        if not exited and category is None:
            unclassified += 1
            continue
        if not exited and not is_current(animal) and not include_exited:
            continue
        if preset_category and category != preset_category:
            continue
        row = animal_row(animal, ctx.today)
        if _matches(row, ctx):
            rows.append(row)

    columns = _register_columns(*CATEGORY_DEFAULTS[preset_category]) if preset_category else REGISTER_COLUMNS
    title = CATEGORY_PLURALS.get(preset_category, "Herd Register")
    notes = []
    if unclassified:
        notes.append(f"{unclassified} animal record(s) could not be classified by the Passport authority and are omitted.")
    summary = [Metric("animals", title if preset_category else "Animals Listed", len(rows), "integer")]
    if not preset_category:
        for category in CATEGORY_ORDER:
            summary.append(Metric(category, CATEGORY_PLURALS[category],
                                  sum(1 for r in rows if r["category"] == category and r["status"] == "Active"), "integer"))
    return ReportResult(
        sections=[Section("register", title, columns, rows, primary=True)],
        summary=summary, notes=notes,
    )


CATEGORY_COLUMNS = column_set(
    Column("category", "Herd Category"),
    Column("animals", "Animals", "integer", total=True),
    Column("share", "% of Herd", "percent"),
)
BREED_COLUMNS = column_set(
    Column("breed", "Breed"),
    *[Column(c, CATEGORY_PLURALS[c], "integer", total=True) for c in CATEGORY_ORDER],
    Column("total", "Total", "integer", total=True),
)


def current_herd_counts(ctx: ReportContext) -> dict[str, int]:
    counts = {c: 0 for c in CATEGORY_ORDER}
    for animal in ctx.animals():
        if is_current(animal):
            counts[classify(animal)[0]] += 1
    return counts


def build_by_category(ctx: ReportContext) -> ReportResult:
    from dairyos.api.dashboard import _herd_composition, _is_governed_active_animal

    current = [a for a in ctx.animals() if is_current(a)]
    counts = {c: 0 for c in CATEGORY_ORDER}
    breeds: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    for animal in current:
        category = classify(animal)[0]
        counts[category] += 1
        breed = clean_text(getattr(animal, "breed", None)) or "Breed not recorded"
        line = breeds.setdefault(breed, {"breed": breed, **{c: 0 for c in CATEGORY_ORDER}, "total": 0})
        line[category] += 1
        line["total"] += 1
    total = len(current)
    rows = [{"category": CATEGORY_PLURALS[c], "animals": counts[c],
             "share": round(counts[c] * 100 / total, 1) if total else None,
             "_drill": {"report_id": f"herd-{c.lower().replace(' ', '-')}", "label": CATEGORY_PLURALS[c], "filters": {}}}
            for c in CATEGORY_ORDER]
    breed_rows = sorted(breeds.values(), key=lambda r: (-r["total"], r["breed"]))

    dashboard = {item["name"]: item["value"] for item in _herd_composition(
        [a for a in ctx.factory.animal().active_animals() if _is_governed_active_animal(a)])}
    notes = []
    differing = [c for c in CATEGORY_ORDER if dashboard.get(c, 0) != counts[c]]
    if differing:
        notes.append("Dashboard herd counts differ from the Passport category authority for: "
                     + ", ".join(CATEGORY_PLURALS[c] for c in differing)
                     + ". Review animals whose milking flag and lifecycle status disagree.")
    from dairyos.reporting.definitions import ReconciliationCheck
    return ReportResult(
        sections=[
            Section("categories", "Herd by Category", CATEGORY_COLUMNS, rows,
                    {"_label": "Total Herd", "animals": total, "share": 100.0 if total else None}, primary=True),
            Section("breeds", "Herd by Breed and Category", BREED_COLUMNS, breed_rows,
                    {"_label": "Total Herd", **counts, "total": total}),
        ],
        summary=[Metric("herd", "Total Herd", total, "integer")]
        + [Metric(c, CATEGORY_PLURALS[c], counts[c], "integer") for c in CATEGORY_ORDER],
        notes=notes,
        reconciliation=[ReconciliationCheck("Herd total agrees with Dashboard", sum(dashboard.values()), total, "integer")],
    )


# ---------------------------------------------------------------------------
# Exits, mortality and herd movement
# ---------------------------------------------------------------------------

def disposition_events(ctx: ReportContext) -> list[dict[str, Any]]:
    """Governed exit records, latest record per animal and disposition."""
    def load():
        entries = (
            ctx.session.query(EventJournalModel)
            .filter(EventJournalModel.event_type == "OperationalInputReceived")
            .filter(EventJournalModel.payload["input_type"].as_string() == "animal_disposition")
            .order_by(EventJournalModel.id)
            .all()
        )
        events = []
        for entry in entries:
            payload = dict(entry.payload or {})
            effective = to_date(payload.get("effective_date")) or to_date(entry.timestamp)
            events.append({
                "animal_id": clean_text(payload.get("animal_id")),
                "exit_date": effective,
                "exit_type": EXIT_LABELS.get(upper(payload.get("disposition")), upper(payload.get("disposition")).title()),
                "reason": clean_text(payload.get("reason")),
                "cause": clean_text(payload.get("cause")),
                "counterparty": clean_text(payload.get("buyer_or_counterparty")),
                "amount": money(payload.get("amount")) if payload.get("amount") not in (None, "") else None,
                "reference": clean_text(payload.get("reference")),
                "veterinarian": clean_text(payload.get("veterinarian")),
                "notes": clean_text(payload.get("notes")),
                "recorded_by": clean_text(payload.get("operator")),
            })
        return events
    return ctx.cached("dispositions", load)


EXIT_COLUMNS = column_set(
    Column("exit_date", "Exit Date", "date"),
    Column("animal_id", "Animal ID"),
    Column("ear_tag", "Ear Tag", "text", IDENT, "optional"),
    Column("category_at_record", "Sex", "text", DETAILS, "optional"),
    Column("breed", "Breed"),
    Column("age_at_exit", "Age at Exit"),
    Column("exit_type", "Exit Type", "status"),
    Column("cause", "Cause of Death"),
    Column("reason", "Reason"),
    Column("counterparty", "Buyer", "text", "Sale", "optional"),
    Column("amount", "Sale Amount (PKR)", "money", "Sale", "optional", total=True),
    Column("veterinarian", "Veterinarian", "text", "Details", "optional"),
    Column("reference", "Reference", "text", "Details", "optional"),
    Column("notes", "Notes", "text", "Details", "optional"),
    Column("recorded_by", "Recorded By", "text", "Details", "optional"),
)


def _exit_rows(ctx: ReportContext) -> list[dict[str, Any]]:
    animals = ctx.animal_index()
    rows = []
    for event in disposition_events(ctx):
        if not ctx.period.contains(event["exit_date"]):
            continue
        animal = animals.get(event["animal_id"] or "")
        born = to_date(getattr(animal, "date_of_birth", None)) if animal else None
        rows.append({
            **event,
            "ear_tag": clean_text(getattr(animal, "ear_tag", None)) if animal else None,
            "category_at_record": (clean_text(getattr(animal, "sex", None)) or "").title() or None,
            "breed": clean_text(getattr(animal, "breed", None)) if animal else None,
            "age_at_exit": age_label(born, event["exit_date"]) if event["exit_date"] else None,
        })
    return rows


def build_exits(ctx: ReportContext) -> ReportResult:
    wanted = ctx.filter("exit_type")
    rows = [r for r in _exit_rows(ctx) if not wanted or upper(r["exit_type"]) == wanted]
    deaths = sum(1 for r in rows if r["exit_type"] == "Deceased")
    sold = sum(1 for r in rows if r["exit_type"] == "Sold")
    herd = sum(current_herd_counts(ctx).values())
    return ReportResult(
        sections=[Section("exits", "Exits and Mortality", EXIT_COLUMNS, rows,
                          {"_label": "Total", "amount": sum((r["amount"] for r in rows if r["amount"] is not None), money(0))},
                          primary=True)],
        summary=[
            Metric("exits", "Total Exits", len(rows), "integer"),
            Metric("deaths", "Deaths", deaths, "integer"),
            Metric("sold", "Sold", sold, "integer"),
            Metric("mortality_rate", "Deaths per 100 Animals", round(deaths * 100 / (herd + deaths), 2) if herd + deaths else None,
                   "number", "Deaths in period divided by current herd plus those deaths"),
        ],
        notes=["The sale amount shown is the value recorded with the exit. Finance revenue for animal sales is "
               "reported under Finance, Animal Sales."],
    )


MOVEMENT_COLUMNS = column_set(
    Column("date", "Date", "date"),
    Column("movement", "Movement", "status"),
    Column("animal_id", "Animal ID"),
    Column("sex", "Sex"),
    Column("breed", "Breed"),
    Column("detail", "Detail"),
)
MOVEMENT_SUMMARY_COLUMNS = column_set(
    Column("movement", "Movement"),
    Column("animals", "Animals", "integer"),
)


def build_movement(ctx: ReportContext) -> ReportResult:
    rows = []
    for animal in ctx.animals():
        born = to_date(getattr(animal, "date_of_birth", None))
        acquired = to_date(getattr(animal, "date_of_acquisition", None))
        base = {"animal_id": clean_text(animal.animal_id),
                "sex": (clean_text(getattr(animal, "sex", None)) or "").title() or None,
                "breed": clean_text(getattr(animal, "breed", None))}
        if acquired is None and ctx.period.contains(born):
            dam = clean_text(getattr(animal, "dam_id", None))
            rows.append({**base, "date": born, "movement": "Birth", "detail": f"Dam {dam}" if dam else None})
        if ctx.period.contains(acquired):
            rows.append({**base, "date": acquired, "movement": "Acquisition", "detail": None})
    for event in _exit_rows(ctx):
        rows.append({"animal_id": event["animal_id"], "sex": event["category_at_record"], "breed": event["breed"],
                     "date": event["exit_date"], "movement": event["exit_type"],
                     "detail": event["cause"] or event["reason"] or event["counterparty"]})
    rows.sort(key=lambda r: (r["date"] or date.min, r["animal_id"] or ""))
    births = sum(1 for r in rows if r["movement"] == "Birth")
    acquisitions = sum(1 for r in rows if r["movement"] == "Acquisition")
    exits = len(rows) - births - acquisitions
    summary_rows = [
        {"movement": "Births on farm", "animals": births},
        {"movement": "Acquisitions", "animals": acquisitions},
        {"movement": "Exits (sold, deceased)", "animals": -exits},
        {"movement": "Net change in herd", "animals": births + acquisitions - exits, "_emphasis": "total"},
    ]
    return ReportResult(
        sections=[Section("summary", "Movement Summary", MOVEMENT_SUMMARY_COLUMNS, summary_rows),
                  Section("movements", "Herd Movements", MOVEMENT_COLUMNS, rows, primary=True)],
        summary=[Metric("births", "Births", births, "integer"), Metric("acquisitions", "Acquisitions", acquisitions, "integer"),
                 Metric("exits", "Exits", exits, "integer"), Metric("net", "Net Change", births + acquisitions - exits, "integer"),
                 Metric("herd", "Current Herd", sum(current_herd_counts(ctx).values()), "integer")],
        notes=["A birth is an animal born in the period with no acquisition date. An acquisition is an animal whose "
               "date of acquisition falls in the period."],
    )


IDENT_COLUMNS = column_set(
    Column("animal_id", "Animal ID"),
    Column("ear_tag", "Ear Tag"),
    Column("rfid", "RFID"),
    Column("legacy_animal_id", "Previous Animal ID", "text", IDENT, "optional"),
    Column("category", "Category"),
    Column("breed", "Breed"),
    Column("location", "Location"),
    Column("identification_gap", "Identification Gap"),
)


def build_identification(ctx: ReportContext) -> ReportResult:
    only_gaps = ctx.flag("only_gaps")
    rows = []
    for animal in ctx.animals():
        if not is_current(animal):
            continue
        row = animal_row(animal, ctx.today)
        missing = [label for key, label in (("ear_tag", "Ear Tag"), ("rfid", "RFID")) if not row[key]]
        row["identification_gap"] = ("Missing " + " and ".join(missing)) if missing else None
        if only_gaps and not missing:
            continue
        if _matches(row, ctx):
            rows.append(row)
    return ReportResult(
        sections=[Section("identification", "Animal Identification", IDENT_COLUMNS, rows, primary=True)],
        summary=[Metric("animals", "Animals Listed", len(rows), "integer"),
                 Metric("no_tag", "Without Ear Tag", sum(1 for r in rows if not r["ear_tag"]), "integer"),
                 Metric("no_rfid", "Without RFID", sum(1 for r in rows if not r["rfid"]), "integer")],
    )


# ---------------------------------------------------------------------------
PASSPORT_COLUMNS = column_set(Column("date", "Date", "date"), Column("domain", "Area", "status"), Column("event", "Event"))
PASSPORT_LINE_COLUMNS = column_set(Column("line", "Passport Item"), Column("value", "Value"))
_TIMELINE_HIDDEN = {"id", "record_id", "animal_id", "timestamp", "created_at", "updated_at", "recorded_at",
                    "operator", "input_type", "photo_data", "session_ledger", "source_event_id", "semen_lot_id",
                    "health_case_id", "event_id"}


def _timeline_text(record: Any) -> str | None:
    if not isinstance(record, dict):
        return clean_text(record)
    parts = []
    for key in sorted(record):
        value = record[key]
        if key in _TIMELINE_HIDDEN or value in (None, "", [], {}) or isinstance(value, (dict, list, tuple, set)):
            continue
        if isinstance(value, bool):
            value = "Yes" if value else "No"
        label = key.replace("_", " ").title().replace(" Id", " ID")
        parts.append(f"{label}: {value}")
    return "; ".join(parts) or None


def build_passport(ctx: ReportContext) -> ReportResult:
    from dairyos.application.database_aware_animal_passport import DatabaseAwareLifetimeAnimalPassportService
    from dairyos.reporting.context import ReportParameterError

    animal_id = ctx.filter("animal_id")
    passport = DatabaseAwareLifetimeAnimalPassportService(ctx.factory).build(animal_id, as_of_date=ctx.period.as_of)
    if passport is None:
        raise ReportParameterError("Animal ID was not found in the herd register.")
    animal = ctx.animal_index().get(animal_id)
    identity = animal_row(animal, ctx.period.as_of) if animal is not None else {}
    biology = dict(passport.get("biological_summary") or {})
    lineage = dict(passport.get("lineage") or {})

    def text(value: Any) -> str | None:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value).replace("_", " ").title() if isinstance(value, str) and value.isupper() else str(value)

    lines = [
        ("Animal ID", animal_id), ("Ear Tag", identity.get("ear_tag")), ("RFID", identity.get("rfid")),
        ("Category", identity.get("category") or identity.get("status")), ("Sex", identity.get("sex")),
        ("Breed", identity.get("breed")),
        ("Date of Birth", identity["date_of_birth"].strftime("%d-%b-%Y") if identity.get("date_of_birth") else None),
        ("Age", identity.get("age")), ("Dam ID", identity.get("dam_id")), ("Sire ID", identity.get("sire_id")),
        ("Production Group", identity.get("production_group")), ("Location", identity.get("location")),
        ("Status", identity.get("status")),
        ("Lifetime Milk (L)", biology.get("lifetime_milk_liters")), ("Lactations", biology.get("lactation_count")),
        ("Lifetime Calvings", biology.get("lifetime_calvings")), ("Days in Milk", biology.get("days_in_milk")),
        ("Reproductive Status", biology.get("current_reproductive_status")),
        ("Pregnancy Status", biology.get("current_pregnancy_status")),
        ("Open Health Cases", biology.get("open_health_cases")),
        ("Under Milk Withdrawal", biology.get("active_milk_withdrawal")),
        ("Known Ancestors", len(list(lineage.get("ancestors") or []))),
        ("Known Descendants", len(list(lineage.get("descendants") or []))),
    ]
    line_rows = [{"line": label, "value": text(value)} for label, value in lines if text(value) is not None]
    timeline = []
    for event in passport.get("timeline") or []:
        if isinstance(event, dict):
            timeline.append({"date": to_date(event.get("timestamp")),
                             "domain": (clean_text(event.get("domain")) or "").replace("_", " ").title() or None,
                             "event": _timeline_text(event.get("record"))})
    return ReportResult(
        sections=[Section("passport", f"Animal Passport: {animal_id}", PASSPORT_LINE_COLUMNS, line_rows),
                  Section("timeline", "Lifetime Timeline", PASSPORT_COLUMNS, timeline, primary=True,
                          empty_message="No lifetime event is recorded for this animal.")],
        summary=[Metric("milk", "Lifetime Milk", biology.get("lifetime_milk_liters"), "litres"),
                 Metric("lactations", "Lactations", biology.get("lactation_count"), "integer"),
                 Metric("calvings", "Lifetime Calvings", biology.get("lifetime_calvings"), "integer"),
                 Metric("events", "Timeline Events", len(timeline), "integer")],
    )


def _definition(report_id, title, purpose, builder, **kwargs) -> ReportDefinition:
    kwargs.setdefault("authority", AUTHORITY)
    return ReportDefinition(id=report_id, area=AREA, title=title, purpose=purpose,
                            permission=PERMISSION, builder=builder, **kwargs)


_CATEGORY_PURPOSE = {
    "Milking": "Cows currently in the milking herd, with group, location and milking frequency.",
    "Dry": "Dry cows, including any cow held out of milking under a veterinary restriction.",
    "Heifer": "Heifers and close-up heifers, with age and dam.",
    "Female Calf": "Female calves, with date of birth, age and dam.",
    "Male Calf": "Male calves, with date of birth, age and dam.",
    "Bull": "Bulls kept on the farm, with breed, age and location.",
}

REPORTS: tuple[ReportDefinition, ...] = (
    _definition("herd-register", "Herd Register",
                "The complete current herd with identification, category, breed, age, group and location.",
                build_register, columns=REGISTER_COLUMNS, default_sort=("animal_id", "asc"),
                filters=(CATEGORY_FILTER, BREED_FILTER, GROUP_FILTER, LOCATION_FILTER,
                         Filter("include_exited", "Include sold and deceased animals", "toggle", default=False))),
    *[
        _definition(f"herd-{category.lower().replace(' ', '-')}", CATEGORY_PLURALS[category],
                    _CATEGORY_PURPOSE[category], build_register, preset={"category": category},
                    columns=_register_columns(*CATEGORY_DEFAULTS[category]), default_sort=("animal_id", "asc"),
                    filters=(BREED_FILTER, LOCATION_FILTER) + ((GROUP_FILTER,) if category in {"Milking", "Dry"} else ()))
        for category in CATEGORY_ORDER
    ],
    _definition("herd-by-category", "Herd by Category",
                "Head count of each herd category and breed, reconciled to the Dashboard herd total.",
                build_by_category, columns=CATEGORY_COLUMNS),
    _definition("herd-movement", "Herd Movement",
                "Births, acquisitions and exits in the period, and the net change in herd size.",
                build_movement, period="range", columns=MOVEMENT_COLUMNS, basis="DERIVED",
                authority="Animal register dates and governed animal disposition records"),
    _definition("herd-exits-mortality", "Exits & Mortality",
                "Animals sold or deceased in the period, with cause, reason and buyer.",
                build_exits, period="range", columns=EXIT_COLUMNS, default_sort=("exit_date", "asc"),
                filters=(Filter("exit_type", "Exit Type", options=(("SOLD", "Sold"), ("DECEASED", "Deceased"))),),
                authority="Governed animal disposition records (operational event journal)"),
    _definition("herd-animal-passport", "Individual Animal Passport",
                "One animal's identity, lifetime production, reproduction and health position, and its lifetime timeline.",
                build_passport, period="as_of", columns=PASSPORT_COLUMNS, default_sort=("date", "asc"), basis="CALCULATED",
                filters=(Filter("animal_id", "Animal ID", "animal", required=True),),
                authority="Lifetime Animal Passport read model"),
    _definition("herd-identification", "Animal Identification",
                "Animal ID, ear tag and RFID for the current herd, highlighting identification gaps.",
                build_identification, columns=IDENT_COLUMNS, default_sort=("animal_id", "asc"),
                filters=(CATEGORY_FILTER, LOCATION_FILTER,
                         Filter("only_gaps", "Only animals with missing identification", "toggle", default=False))),
)
