"""Cost of Milk reporting.

Authority: the Estimated COP calculation (``/farm/coml/integrated``), which
combines the TMR feed-cost authority, Finance OPEX attribution and the milk
production ledger, and the locked official monthly ``COMLRecord``.

Reporting calls that authority for each period it presents. It never
computes feed cost, OPEX attribution or a per-litre cost of its own.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from dairyos.finance import ledger_semantics as semantics
from dairyos.finance.opex_period_attribution import attribute_opex_for_period
from dairyos.reporting.context import (
    ReportContext,
    ReportParameterError,
    clean_text,
    money,
    ratio,
    to_date,
)
from dairyos.reporting.definitions import (
    Column,
    Metric,
    ReconciliationCheck,
    ReportDefinition,
    ReportResult,
    Section,
)
from dairyos.reporting.engine import column_set
from dairyos.reporting.periods import format_date, month_sequence

AREA = "cost"
PERMISSION = "coml.view"
AUTHORITY = "Estimated COP authority: TMR feed cost, attributed Finance OPEX and the milk production ledger"
MAX_DAILY_DAYS = 92


def integrated(ctx: ReportContext, start: date, end: date) -> dict[str, Any]:
    from dairyos.api.coml import get_integrated_coml

    return ctx.cached(f"cop:{start}:{end}", lambda: get_integrated_coml(
        period_start=start, period_end=end, container=ctx.container))


def _cop_row(label: str, start: date, end: date, result: dict[str, Any]) -> dict[str, Any]:
    costs = result.get("costs", {})
    feed = costs.get("feed_total")
    return {
        "period": label, "from_date": start, "to_date": end,
        "milk": result.get("production", {}).get("totalLiters"),
        "feed_cost": money(feed) if feed is not None else None,
        "opex": money(costs.get("opex_total")),
        "total_cost": money(float(feed) + float(costs.get("opex_total") or 0)) if feed is not None else None,
        "feed_per_litre": costs.get("feed_cost_per_liter"),
        "opex_per_litre": costs.get("opex_cost_per_liter"),
        "cop_per_litre": costs.get("total_coml_per_liter"),
        "cost_basis": "Complete" if result.get("data_status") == "AUTO_AGGREGATED" else "Feed cost authority incomplete",
    }


PERIOD_COLUMNS = column_set(
    Column("period", "Period"), Column("from_date", "From", "date", "Period", "optional"),
    Column("to_date", "To", "date", "Period", "optional"),
    Column("milk", "Milk Produced (L)", "litres", total=True),
    Column("feed_cost", "Feed Cost (PKR)", "money", total=True), Column("opex", "OPEX (PKR)", "money", total=True),
    Column("total_cost", "Total Cost (PKR)", "money", total=True),
    Column("feed_per_litre", "Feed Cost / L (PKR)", "rate"), Column("opex_per_litre", "OPEX / L (PKR)", "rate"),
    Column("cop_per_litre", "COP / L (PKR)", "rate"), Column("cost_basis", "Cost Basis", "status"),
)
COMPONENT_COLUMNS = column_set(
    Column("component", "Cost Component"), Column("amount", "Amount (PKR)", "money", total=True),
    Column("per_litre", "Per Litre (PKR)", "rate"), Column("share", "% of Cost", "percent"),
)


def _totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    milk = round(sum(float(r["milk"] or 0) for r in rows), 2)
    feed = sum((r["feed_cost"] for r in rows if r["feed_cost"] is not None), money(0))
    opex = sum((r["opex"] for r in rows), money(0))
    return {"_label": "Total", "milk": milk, "feed_cost": feed, "opex": opex, "total_cost": feed + opex,
            "feed_per_litre": ratio(feed, milk, 4), "opex_per_litre": ratio(opex, milk, 4),
            "cop_per_litre": ratio(feed + opex, milk, 4)}


def build_period_cost(ctx: ReportContext) -> ReportResult:
    start, end = ctx.period.start, ctx.period.end
    result = integrated(ctx, start, end)
    row = _cop_row(ctx.period.label, start, end, result)
    litres = float(row["milk"] or 0)

    components: dict[str, Any] = {}
    if start <= ctx.today:
        for item in attribute_opex_for_period(ctx.factory, start, min(end, ctx.today)).rows:
            if item.status == "ATTRIBUTED":
                group = semantics.expense_category(item.transaction)[2]
                components[group] = components.get(group, money(0)) + item.attributed
    total_cost = row["total_cost"] or row["opex"]
    component_rows = []
    if row["feed_cost"] is not None:
        component_rows.append({"component": "Feed (TMR authority)", "amount": row["feed_cost"]})
    component_rows += [{"component": f"OPEX: {name}", "amount": amount}
                       for name, amount in sorted(components.items(), key=lambda kv: -kv[1])]
    for line in component_rows:
        line["per_litre"] = ratio(line["amount"], litres, 4)
        line["share"] = ratio(line["amount"] * 100, total_cost, 1) if total_cost else None

    official = result.get("official")
    notes = [clean_text(result.get("message"))] if result.get("message") else []
    costs = result.get("costs", {})
    if costs.get("unattributed_opex_count"):
        notes.append(f"{costs['unattributed_opex_count']} OPEX transaction(s) totalling PKR "
                     f"{float(costs.get('unattributed_opex_total') or 0):,.2f} lack attribution and are not in this cost.")
    if litres <= 0:
        notes.append("No milk is recorded for the period, so per-litre costs are not available.")
    if official:
        notes.append(f"Official locked COML for {official['month_label']}: PKR {official['total_coml_per_liter']:.4f} per litre.")
    return ReportResult(
        sections=[Section("cost", "Cost of Milk for Period", PERIOD_COLUMNS, [row]),
                  Section("components", "Cost Component Breakdown", COMPONENT_COLUMNS, component_rows,
                          {"_label": "Total Cost", "amount": sum((r["amount"] for r in component_rows), money(0)),
                           "per_litre": ratio(total_cost, litres, 4), "share": 100.0 if component_rows else None}, primary=True)],
        summary=[Metric("cop", "Cost of Production / L", row["cop_per_litre"], "rate"),
                 Metric("feed", "Feed Cost / L", row["feed_per_litre"], "rate"),
                 Metric("opex", "OPEX / L", row["opex_per_litre"], "rate"),
                 Metric("milk", "Milk Produced", row["milk"], "litres"),
                 Metric("cost", "Total Cost", row["total_cost"], "money")],
        notes=notes,
        reconciliation=[ReconciliationCheck("OPEX components equal OPEX used by the COP authority", row["opex"],
                                            sum(components.values(), money(0)))],
    )


MONTHLY_COLUMNS = column_set(
    *PERIOD_COLUMNS, Column("official_coml", "Official Locked COML / L (PKR)", "rate", "Official", "default"))


def build_monthly_cost(ctx: ReportContext) -> ReportResult:
    official = {to_date(r.month_start): r for r in ctx.factory.coml().get_all()}
    columns = MONTHLY_COLUMNS
    rows = []
    for first, last in month_sequence(ctx.period.start, ctx.period.end):
        row = _cop_row(first.strftime("%B %Y"), first, last, integrated(ctx, first, last))
        locked = official.get(first.replace(day=1))
        row["official_coml"] = float(locked.total_coml_per_liter) if locked is not None else None
        rows.append(row)
    return ReportResult(
        sections=[Section("months", "Monthly Cost Summary", columns, rows, _totals(rows), primary=True,
                          note="A first or last month is partial when the selected range does not cover it fully. "
                               "Official Locked COML applies to the whole calendar month.")],
        summary=[Metric("cop", "Cost of Production / L", _totals(rows)["cop_per_litre"], "rate",
                        "Total cost divided by total milk across the listed months"),
                 Metric("milk", "Milk Produced", _totals(rows)["milk"], "litres")],
    )


def build_daily_cost(ctx: ReportContext) -> ReportResult:
    if ctx.period.days > MAX_DAILY_DAYS:
        raise ReportParameterError(f"Daily Cost of Milk calls the cost authority for each day. Select {MAX_DAILY_DAYS} days or fewer.")
    rows = []
    day, last = ctx.period.start, min(ctx.period.end, ctx.today)
    while day <= last:
        row = _cop_row(format_date(day), day, day, integrated(ctx, day, day))
        row["date"] = day
        if row["milk"] or row["feed_cost"] or row["opex"]:
            rows.append(row)
        day += timedelta(days=1)
    columns = column_set(Column("date", "Date", "date"), *[c for c in PERIOD_COLUMNS if c.key not in {"period", "from_date", "to_date"}])
    return ReportResult(
        sections=[Section("days", "Daily Cost of Milk", columns, rows, _totals(rows), primary=True,
                          note="Periodic and allocated OPEX is spread evenly over its coverage dates by the attribution authority.")],
        summary=[Metric("cop", "Cost of Production / L", _totals(rows)["cop_per_litre"], "rate"),
                 Metric("days", "Days Listed", len(rows), "integer")],
    )


OFFICIAL_COLUMNS = column_set(
    Column("month", "Month"), Column("feed_per_litre", "Feed Cost / L (PKR)", "rate"),
    Column("opex_per_litre", "OPEX / L (PKR)", "rate"), Column("coml_per_litre", "COML / L (PKR)", "rate"),
    Column("status", "Status", "status"), Column("locked_date", "Locked On", "date"), Column("locked_by", "Locked By"),
    Column("notes", "Notes", "text", "Details", "optional"),
)


def build_official_history(ctx: ReportContext) -> ReportResult:
    rows = [{"month": r.month_start.strftime("%B %Y"), "_sort": r.month_start,
             "feed_per_litre": float(r.feed_cost_per_liter), "opex_per_litre": float(r.opex_cost_per_liter),
             "coml_per_litre": float(r.total_coml_per_liter), "status": clean_text(r.status),
             "locked_date": to_date(r.locked_at), "locked_by": clean_text(r.updated_by), "notes": clean_text(r.notes)}
            for r in sorted(ctx.factory.coml().get_all(), key=lambda r: r.month_start)]
    return ReportResult(
        sections=[Section("official", "Official Monthly COML", OFFICIAL_COLUMNS, rows, primary=True)],
        summary=[Metric("months", "Months Locked", len(rows), "integer"),
                 Metric("latest", "Latest Official COML / L", rows[-1]["coml_per_litre"] if rows else None, "rate")],
        notes=["Official COML is the monthly figure locked on the COML tab. It is a recorded decision and is not recalculated here."],
    )


def _definition(report_id, title, purpose, builder, **kwargs) -> ReportDefinition:
    kwargs.setdefault("authority", AUTHORITY)
    kwargs.setdefault("basis", "CALCULATED")
    return ReportDefinition(id=report_id, area=AREA, title=title, purpose=purpose,
                            permission=PERMISSION, builder=builder, **kwargs)


REPORTS: tuple[ReportDefinition, ...] = (
    _definition("cost-period", "Cost of Milk & Component Breakdown",
                "Feed cost, OPEX and cost of production per litre for the period, broken down by cost component.",
                build_period_cost, period="range", columns=COMPONENT_COLUMNS, default_period="CURRENT_MONTH"),
    _definition("cost-monthly-summary", "Monthly Cost Summary",
                "Milk volume, feed cost, OPEX and cost per litre for each month, beside the official locked COML.",
                build_monthly_cost, period="range", columns=MONTHLY_COLUMNS, default_period="YEAR_TO_DATE"),
    _definition("cost-daily", "Daily Cost of Milk",
                "Milk volume against feed cost, OPEX and cost per litre for each day: the cost trend.",
                build_daily_cost, period="range", default_period="LAST_30_DAYS", default_sort=("date", "asc")),
    _definition("cost-official-history", "Official COML History",
                "The locked official monthly COML records.",
                build_official_history, columns=OFFICIAL_COLUMNS, authority="Official monthly COML records (COMLRecord)",
                basis="RECORDED", empty_message="No official monthly COML has been locked yet."),
)
