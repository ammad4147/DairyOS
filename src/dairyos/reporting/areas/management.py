"""Management reporting: cross-module summaries.

Management reports hold no logic of their own. Every figure is read from the
summary of the area report that owns it, by running that report's builder
with the same date. A management figure therefore cannot disagree with the
detailed report it links to.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

from dairyos.reporting.context import ReportContext
from dairyos.reporting.definitions import (
    Column,
    Metric,
    ReportDefinition,
    ReportResult,
    Section,
)
from dairyos.reporting.engine import column_set
from dairyos.reporting.periods import ResolvedPeriod, format_date

AREA = "management"
PERMISSION = "settings.view"
AUTHORITY = "The area reports of this catalogue, each reading its own DairyOS authority"

LINE_COLUMNS = column_set(
    Column("area", "Area"), Column("line", "Measure"), Column("value", "Value", "number"),
    Column("unit", "Unit"), Column("comment", "Comment"),
)
ATTENTION_COLUMNS = column_set(
    Column("area", "Area"), Column("item", "Attention Item", "status"),
    Column("count", "Count", "integer", total=True), Column("detail", "What to Do"),
)


def _sub(ctx: ReportContext, report_id: str, *, start: date | None = None, end: date | None = None,
         filters: dict[str, Any] | None = None) -> ReportResult | None:
    """Run another report's builder inside this request. A failing area
    never breaks the summary: it is reported as unavailable."""
    from dairyos.reporting.registry import REPORT_BY_ID

    definition = REPORT_BY_ID[report_id]
    if definition.period == "range":
        period = ResolvedPeriod("range", "CUSTOM", start, end, "", ctx.today)
    elif definition.period == "as_of":
        period = ResolvedPeriod("as_of", "AS_OF", None, end or ctx.period.as_of, "", ctx.today)
    else:
        period = ResolvedPeriod("none", None, None, ctx.today, "", ctx.today)
    defaults = {f.key: f.default for f in definition.filters if f.default is not None}
    child = replace(ctx, definition=definition, period=period, filters={**defaults, **(filters or {})})
    child._cache = ctx._cache
    try:
        return definition.builder(child)
    except Exception:  # noqa: BLE001 - one unavailable area must not hide the rest
        ctx.session.rollback()
        return None


def _metric(result: ReportResult | None, key: str) -> Any:
    if result is None:
        return None
    for metric in result.summary:
        if metric.key == key:
            return metric.value
    return None


def _number(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _line(area: str, line: str, value: Any, unit: str, comment: str | None = None,
          drill: str | None = None, period: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {"area": area, "line": line, "value": _number(value), "unit": unit, "comment": comment}
    if value is None and comment is None:
        row["comment"] = "Not available"
    if drill:
        row["_drill"] = {"report_id": drill, "label": line, "filters": {}, **({"period": period} if period else {})}
    return row


def _attention(ctx: ReportContext, as_of: date) -> list[dict[str, Any]]:
    items: list[tuple[str, str, Any, str, str]] = []
    watch = _sub(ctx, "milk-yield-drop-watchlist", end=as_of)
    items.append(("Milk", "Yield drop of 15% or more", _metric(watch, "animals"), "Check these cows for illness, heat or feed change.", "milk-yield-drop-watchlist"))
    withdrawal = _sub(ctx, "health-withdrawal-status")
    items.append(("Health", "Animals under milk withdrawal", _metric(withdrawal, "animals"), "Withhold their milk from sale.", "health-withdrawal-status"))
    cases = _sub(ctx, "health-active-cases")
    items.append(("Health", "Open health cases", _metric(cases, "open"), "Review treatment and follow-up.", "health-active-cases"))
    items.append(("Health", "Health follow-ups overdue", _metric(cases, "followup"), "Carry out the overdue follow-up.", "health-active-cases"))
    vaccination = _sub(ctx, "health-vaccination-due", end=as_of, filters={"within_days": "7"})
    items.append(("Health", "Vaccinations overdue", _metric(vaccination, "overdue"), "Administer or reschedule.", "health-vaccination-due"))
    pd_due = _sub(ctx, "breed-pd-due", end=as_of)
    items.append(("Breeding", "Pregnancy diagnosis due or overdue", _metric(pd_due, "due"), "Arrange pregnancy diagnosis.", "breed-pd-due"))
    due_ai = _sub(ctx, "breed-due-for-ai", end=as_of)
    items.append(("Breeding", "Animals due for AI", _metric(due_ai, "animals"), "Watch for heat and inseminate.", "breed-due-for-ai"))
    calving = _sub(ctx, "breed-pregnancies", end=as_of, filters={"calving_within": "14"})
    items.append(("Breeding", "Calving expected within 14 days", _metric(calving, "pregnant"), "Move to the calving area and observe.", "breed-pregnancies"))
    repeat = _sub(ctx, "breed-repeat-breeders", end=as_of)
    items.append(("Breeding", "Repeat breeders", _metric(repeat, "animals"), "Veterinary reproductive examination.", "breed-repeat-breeders"))
    stock = _sub(ctx, "feed-inventory")
    low = (_metric(stock, "low") or 0) + (_metric(stock, "shortage") or 0) if stock else None
    items.append(("Feed", "Feed items low or in shortage", low, "Reorder before the ration is affected.", "feed-inventory"))
    receivable = _sub(ctx, "fin-receivables", end=as_of)
    items.append(("Finance", "Receivables overdue (PKR)", _metric(receivable, "overdue"), "Follow up with the buyer.", "fin-receivables"))
    payable = _sub(ctx, "fin-payables", end=as_of)
    items.append(("Finance", "Payables overdue (PKR)", _metric(payable, "overdue"), "Schedule supplier payment.", "fin-payables"))

    rows = []
    for area, item, count, detail, report_id in items:
        number = _number(count)
        if count is None:
            rows.append({"area": area, "item": item, "count": None, "detail": "This area could not be read.",
                         "_drill": {"report_id": report_id, "label": item, "filters": {}}})
        elif number and number > 0:
            rows.append({"area": area, "item": item, "count": number, "detail": detail,
                         "_drill": {"report_id": report_id, "label": item, "filters": {}}})
    return rows


def build_attention(ctx: ReportContext) -> ReportResult:
    rows = _attention(ctx, ctx.period.as_of)
    return ReportResult(
        sections=[Section("attention", "Items Needing Attention", ATTENTION_COLUMNS, rows, primary=True)],
        summary=[Metric("items", "Attention Items", len(rows), "integer")],
        notes=["Finance rows show an amount in PKR rather than a count. Select any row to open the supporting report."],
    )


def build_daily_summary(ctx: ReportContext) -> ReportResult:
    day = ctx.period.as_of
    span = {"mode": "CUSTOM", "start_date": day.isoformat(), "end_date": day.isoformat()}
    herd = _sub(ctx, "herd-by-category")
    milk = _sub(ctx, "milk-daily-production", start=day, end=day)
    use = _sub(ctx, "milk-utilisation", start=day, end=day)
    feed = _sub(ctx, "feed-daily-cost", start=day, end=day)
    finance = _sub(ctx, "fin-revenue-expense-reconciliation", start=day, end=day)
    exits = _sub(ctx, "herd-exits-mortality", start=day, end=day)
    receivable = _sub(ctx, "fin-receivables", end=day)
    payable = _sub(ctx, "fin-payables", end=day)

    sessions = milk.sections[0].totals if milk else {}
    lines = [
        _line("Herd", "Total herd", _metric(herd, "herd"), "animals", "Current herd", "herd-by-category"),
        _line("Herd", "Milking cows", _metric(herd, "Milking"), "animals", "Current herd", "herd-milking"),
        _line("Herd", "Dry cows", _metric(herd, "Dry"), "animals", "Current herd", "herd-dry"),
        _line("Herd", "Deaths recorded", _metric(exits, "deaths"), "animals", None, "herd-exits-mortality", span),
        _line("Milk", "Milk produced", _metric(milk, "total"), "litres", None, "milk-daily-production", span),
        _line("Milk", "Morning session", sessions.get("morning"), "litres"),
        _line("Milk", "Afternoon session", sessions.get("afternoon"), "litres"),
        _line("Milk", "Evening session", sessions.get("evening"), "litres"),
        _line("Milk", "Milk sold", _metric(use, "sold"), "litres", None, "milk-utilisation", span),
        _line("Milk", "Calf feeding", _metric(use, "calf"), "litres"),
        _line("Milk", "Domestic use", _metric(use, "domestic"), "litres"),
        _line("Milk", "Wastage and withdrawal discard", _metric(use, "waste"), "litres"),
        _line("Milk", "Unaccounted milk", _metric(use, "unaccounted"), "litres"),
        _line("Feed", "Herd feed cost", _metric(feed, "cost"), "PKR", None, "feed-daily-cost", span),
        _line("Feed", "Feed cost per litre", _metric(feed, "per_litre"), "PKR / litre"),
        _line("Finance", "Revenue recorded", _metric(finance, "total_revenue"), "PKR", None, "fin-revenue-expense-reconciliation", span),
        _line("Finance", "Expenses recorded", _metric(finance, "total_expenses"), "PKR"),
        _line("Finance", "Receivables outstanding", _metric(receivable, "outstanding"), "PKR", f"As of {format_date(day)}", "fin-receivables"),
        _line("Finance", "Payables outstanding", _metric(payable, "outstanding"), "PKR", f"As of {format_date(day)}", "fin-payables"),
    ]
    attention = _attention(ctx, day)
    return ReportResult(
        sections=[Section("figures", f"Farm Figures for {format_date(day)}", LINE_COLUMNS, lines, primary=True),
                  Section("attention", "Items Needing Attention", ATTENTION_COLUMNS, attention,
                          empty_message="Nothing needs attention.")],
        summary=[Metric("milk", "Milk Produced", _metric(milk, "total"), "litres"),
                 Metric("herd", "Total Herd", _metric(herd, "herd"), "integer"),
                 Metric("revenue", "Revenue", _metric(finance, "total_revenue"), "money"),
                 Metric("expenses", "Expenses", _metric(finance, "total_expenses"), "money"),
                 Metric("attention", "Attention Items", len(attention), "integer")],
        notes=["Herd figures are the current herd. All other figures are for the selected date."],
    )


def build_period_summary(ctx: ReportContext) -> ReportResult:
    start, end = ctx.period.start, ctx.period.end
    span = {"mode": "CUSTOM", "start_date": start.isoformat(), "end_date": end.isoformat()}
    milk = _sub(ctx, "milk-daily-production", start=start, end=end)
    use = _sub(ctx, "milk-utilisation", start=start, end=end) if ctx.period.days <= 366 else None
    movement = _sub(ctx, "herd-movement", start=start, end=end)
    exits = _sub(ctx, "herd-exits-mortality", start=start, end=end)
    service = _sub(ctx, "breed-technician-performance", start=start, end=end)
    calvings = _sub(ctx, "breed-calvings", start=start, end=end)
    cases = _sub(ctx, "health-cases-period", start=start, end=end)
    treatments = _sub(ctx, "health-treatments", start=start, end=end)
    finance = _sub(ctx, "fin-revenue-expense-reconciliation", start=start, end=end)
    cost = _sub(ctx, "cost-period", start=start, end=end)
    herd = _sub(ctx, "herd-by-category")

    lines = [
        _line("Herd", "Current herd", _metric(herd, "herd"), "animals", "Current herd", "herd-by-category"),
        _line("Herd", "Births", _metric(movement, "births"), "animals", None, "herd-movement", span),
        _line("Herd", "Acquisitions", _metric(movement, "acquisitions"), "animals"),
        _line("Herd", "Exits", _metric(movement, "exits"), "animals"),
        _line("Herd", "Deaths", _metric(exits, "deaths"), "animals", None, "herd-exits-mortality", span),
        _line("Milk", "Milk produced", _metric(milk, "total"), "litres", None, "milk-daily-production", span),
        _line("Milk", "Average per production day", _metric(milk, "avg_day"), "litres"),
        _line("Milk", "Milk sold", _metric(use, "sold"), "litres", None, "milk-utilisation", span),
        _line("Milk", "Unaccounted milk", _metric(use, "unaccounted"), "litres"),
        _line("Breeding", "Inseminations", _metric(service, "ai"), "services", None, "breed-inseminations", span),
        _line("Breeding", "Conception rate", _metric(service, "rate"), "%", "Inseminations with a known outcome"),
        _line("Breeding", "Calvings", _metric(calvings, "calvings"), "calvings", None, "breed-calvings", span),
        _line("Health", "Health cases opened", _metric(cases, "cases"), "cases", None, "health-cases-period", span),
        _line("Health", "Treatments given", _metric(treatments, "treatments"), "treatments", None, "health-treatments", span),
        _line("Finance", "Revenue", _metric(finance, "total_revenue"), "PKR", None, "fin-revenue-expense-reconciliation", span),
        _line("Finance", "Expenses", _metric(finance, "total_expenses"), "PKR"),
        _line("Finance", "Revenue less expenses", _metric(finance, "position"), "PKR", "Arithmetic position, not profit"),
        _line("Cost of Milk", "Feed cost per litre", _metric(cost, "feed"), "PKR / litre", None, "cost-period", span),
        _line("Cost of Milk", "OPEX per litre", _metric(cost, "opex"), "PKR / litre"),
        _line("Cost of Milk", "Cost of production per litre", _metric(cost, "cop"), "PKR / litre"),
    ]
    revenue, litres_sold = _number(_metric(finance, "total_revenue")), _number(_metric(use, "sold"))
    return ReportResult(
        sections=[Section("figures", "Farm Performance Summary", LINE_COLUMNS, lines, primary=True)],
        summary=[Metric("milk", "Milk Produced", _metric(milk, "total"), "litres"),
                 Metric("cop", "Cost of Production / L", _metric(cost, "cop"), "rate"),
                 Metric("revenue", "Revenue", _metric(finance, "total_revenue"), "money"),
                 Metric("expenses", "Expenses", _metric(finance, "total_expenses"), "money"),
                 Metric("position", "Revenue less Expenses", _metric(finance, "position"), "money", "Arithmetic position, not profit")],
        notes=["Every figure is the summary figure of the report it links to. Select a row to open the detail."]
        + (["Milk utilisation is omitted for periods longer than one year."] if use is None and revenue is not None and litres_sold is None else []),
    )


def _definition(report_id, title, purpose, builder, **kwargs) -> ReportDefinition:
    return ReportDefinition(id=report_id, area=AREA, title=title, purpose=purpose, permission=PERMISSION,
                            builder=builder, authority=AUTHORITY, basis="CALCULATED", **kwargs)


REPORTS: tuple[ReportDefinition, ...] = (
    _definition("mgmt-daily-summary", "Daily Farm Summary",
                "One page for the day: herd, milk by session, where the milk went, feed cost, money and what needs attention.",
                build_daily_summary, period="as_of", columns=LINE_COLUMNS),
    _definition("mgmt-period-summary", "Farm Performance Summary",
                "Herd, production, breeding, health, finance and cost of milk for a month, a quarter or any period.",
                build_period_summary, period="range", columns=LINE_COLUMNS, default_period="CURRENT_MONTH"),
    _definition("mgmt-attention", "Attention Report",
                "Everything across the farm that needs action today, each linked to its supporting report.",
                build_attention, period="as_of", columns=ATTENTION_COLUMNS,
                empty_message="Nothing needs attention."),
)
