"""Feed reporting.

Authorities, consumed as they stand:

* Governed TMR (``build_live_tmr_summary``): rations per feeding stage, price
  per ingredient (Finance purchase price or manual), cost per head per day,
  and herd feed cost by category from the active Animal register.
* Daily TMR cost snapshots (``tmr_feed_cost_for_period``): the locked daily
  whole-herd feed cost that Cost of Milk uses.
* Feed Storage projection (``authoritative_feed_inventory``): Finance
  purchases in, governed TMR consumption out, signed manual corrections.
* Inventory movement ledger and Finance FEED purchases.

Reporting presents these results. It does not price feed itself.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.reporting.context import (
    ReportContext,
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
from dairyos.reporting.periods import format_date

AREA = "feed"
PERMISSION = "feed.view"
TMR_AUTHORITY = "Governed TMR rations priced by the TMR authority, populations from the active Animal register"

PRICE_SOURCE_LABELS = {"FINANCE": "Latest Finance purchase", "MANUAL": "Manual price",
                       "MANUAL_FALLBACK": "Manual price (no Finance purchase)",
                       "UNPRICED": "No price recorded"}


def _label(value: Any) -> str | None:
    text = clean_text(value)
    return text.replace("_", " ").title() if text else None


def live_tmr(ctx: ReportContext) -> dict[str, Any]:
    from dairyos.api.tmr import build_live_tmr_summary

    return ctx.cached("live_tmr", lambda: build_live_tmr_summary(ctx.factory, include_weekly_review=False,
                                                                operational_date=ctx.today))


CATEGORY_COST_COLUMNS = column_set(
    Column("category", "Herd Category"),
    Column("animals", "Animals", "integer", total=True),
    Column("cost_per_head_day", "Feed Cost per Animal per Day (PKR)", "money"),
    Column("category_cost_per_day", "Category Feed Cost per Day (PKR)", "money", total=True),
    Column("share", "% of Herd Feed Cost", "percent"),
)
RATION_COLUMNS = column_set(
    Column("stage", "Feeding Stage", "text", "Ration"),
    Column("ingredient", "Ingredient", "text", "Ration"),
    Column("quantity_kg", "Quantity per Animal per Day (kg)", "kg", "Ration", total=True),
    Column("price_per_kg", "Price per kg (PKR)", "rate", "Price"),
    Column("price_source", "Price Source", "text", "Price"),
    Column("cost_per_head_day", "Cost per Animal per Day (PKR)", "money", "Cost", total=True),
    Column("finance_purchase_date", "Price Purchase Date", "date", "Price", "optional"),
)


def _money_or_none(value: Any) -> Any:
    """Money, or nothing at all.

    ``money`` turns ``None`` into zero, which is right for an absent
    transaction and wrong for an absent price. An ingredient with no recorded
    price has no cost, and a blank cell says so. Zero would read as free feed.
    """
    return None if value is None else money(value)


def build_current_tmr(ctx: ReportContext) -> ReportResult:
    from dairyos.reporting.areas.herd import CATEGORY_PLURALS

    summary = live_tmr(ctx)
    total = float(summary["total_herd_feed_cost_per_day"] or 0)
    category_rows = [{
        "category": CATEGORY_PLURALS.get(row["category"], row["category"]), "animals": row["animal_count"],
        "cost_per_head_day": money(row["cost_per_head_day"]), "category_cost_per_day": money(row["category_cost_per_day"]),
        "share": ratio(float(row["category_cost_per_day"]) * 100, total, 1),
    } for row in summary["categories"]]
    stage_filter = ctx.filter("stage")
    ration_rows = []
    for key, stage in summary["stages"].items():
        if stage_filter and key != stage_filter:
            continue
        for item in stage.get("ingredients", []):
            quantity = float(item.get("quantity") or 0)
            ration_rows.append({
                "stage": stage.get("label") or _label(key),
                "ingredient": clean_text(item.get("display_name") or item.get("name") or item.get("catalog_name")),
                "quantity_kg": round(quantity / 1000.0 if item.get("dose_unit") == "g" else quantity, 4),
                "price_per_kg": item.get("price_per_kg"),
                "price_source": PRICE_SOURCE_LABELS.get(upper(item.get("price_source")), _label(item.get("price_source"))),
                "cost_per_head_day": _money_or_none(item.get("cost_per_head_day")),
                "finance_purchase_date": to_date(item.get("finance_purchase_date")),
            })
    unpriced = summary.get("unpriced_ingredients") or []
    return ReportResult(
        sections=[
            Section("categories", "Daily Feed Cost by Herd Category", CATEGORY_COST_COLUMNS, category_rows,
                    {"_label": "Whole Herd", "animals": sum(r["animals"] for r in category_rows),
                     "category_cost_per_day": money(total), "share": 100.0 if total else None}),
            Section("rations", "Ration Composition and Cost", RATION_COLUMNS, ration_rows,
                    {"_label": "Total (selected stages)", "quantity_kg": round(sum(r["quantity_kg"] for r in ration_rows), 4),
                     "cost_per_head_day": sum((r["cost_per_head_day"] for r in ration_rows
                                               if r["cost_per_head_day"] is not None), money(0))}, primary=True),
        ],
        summary=[Metric("daily", "Herd Feed Cost per Day", money(total), "money"),
                 Metric("milk", "Milk Today", summary.get("milk_production_today_liters"), "litres"),
                 Metric("per_litre", "Feed Cost per Litre Today", summary.get("feed_cost_per_litre_today"), "rate",
                        "Not available until milk is recorded today")],
        notes=["Category cost averages the feeding stages that make up the category, then multiplies by the animals "
               "currently in that category. This is the TMR authority's own method."]
        + (["Feed cost here covers the priced part of the ration only. "
            + ", ".join(str(name) for name in unpriced)
            + " has no Finance purchase price, no confirmed manual rate and no catalogue price, so it is shown as "
            "unpriced rather than as zero. Record a Finance FEED purchase or a manual rate to bring it into the "
            "cost."] if unpriced else []),
    )


DAILY_COST_COLUMNS = column_set(
    Column("date", "Date", "date"),
    Column("feed_cost", "Herd Feed Cost (PKR)", "money", total=True),
    Column("basis", "Cost Basis", "status"),
    Column("milk", "Milk Produced (L)", "litres", total=True),
    Column("feed_cost_per_litre", "Feed Cost per Litre (PKR)", "rate"),
    Column("animals", "Animals Fed", "integer", "Herd", "optional"),
    Column("cost_per_animal", "Feed Cost per Animal (PKR)", "money", "Herd", "optional"),
)


def feed_cost_basis(ctx: ReportContext) -> dict[str, Any]:
    from dairyos.api.tmr import tmr_feed_cost_for_period

    key = f"feed_basis:{ctx.period.start}:{ctx.period.end}"
    return ctx.cached(key, lambda: tmr_feed_cost_for_period(ctx.factory, ctx.period.start, ctx.period.end))


def _snapshot_herd_counts(ctx: ReportContext) -> dict[str, int]:
    from dairyos.api.tmr import _daily_cost_snapshots

    return ctx.cached("snapshot_counts", lambda: {
        str(s.get("operational_date")): sum(int(v or 0) for v in (s.get("herd_counts") or {}).values())
        for s in _daily_cost_snapshots(ctx.factory)})


def build_daily_feed_cost(ctx: ReportContext) -> ReportResult:
    from dairyos.reporting.areas.milk import _daily

    basis = feed_cost_basis(ctx)
    milk_by_day = {row["date"]: row["total"] for row in _daily(ctx, ctx.period.start, ctx.period.end)}
    counts = _snapshot_herd_counts(ctx)
    rows = []
    for item in basis.get("daily", []):
        day = to_date(item.get("date"))
        cost = item.get("feed_cost")
        milk = milk_by_day.get(day, 0.0)
        animals = counts.get(str(item.get("date")))
        rows.append({
            "date": day, "feed_cost": money(cost) if cost is not None else None, "basis": _label(item.get("basis")),
            "milk": milk, "feed_cost_per_litre": ratio(cost, milk, 4) if cost is not None else None,
            "animals": animals, "cost_per_animal": money(ratio(cost, animals, 2)) if cost is not None and animals else None,
        })
    total_cost = sum((r["feed_cost"] for r in rows if r["feed_cost"] is not None), money(0))
    total_milk = round(sum(r["milk"] for r in rows), 2)
    notes = []
    missing = basis.get("missing_authority_days") or []
    if missing:
        notes.append(f"{len(missing)} day(s) have no locked TMR cost snapshot. No feed cost has been substituted for them.")
    if basis.get("clamped_to_operational_date"):
        notes.append(f"Feed cost stops at the farm operational date, {format_date(ctx.today)}.")
    authority_total = basis.get("total_feed_cost")
    return ReportResult(
        sections=[Section("daily", "Daily Feed Cost", DAILY_COST_COLUMNS, rows,
                          {"_label": "Total", "feed_cost": total_cost, "milk": total_milk,
                           "feed_cost_per_litre": ratio(total_cost, total_milk, 4)}, primary=True)],
        summary=[Metric("cost", "Feed Cost for Period", total_cost, "money"),
                 Metric("milk", "Milk Produced", total_milk, "litres"),
                 Metric("per_litre", "Feed Cost per Litre", ratio(total_cost, total_milk, 4), "rate",
                        "Period feed cost divided by period milk"),
                 Metric("avg", "Average Feed Cost per Day", money(ratio(total_cost, len(rows), 2)) if rows else None, "money")],
        notes=notes,
        reconciliation=[ReconciliationCheck("Daily rows equal the TMR period feed cost authority",
                                            money(authority_total), total_cost)] if authority_total is not None else [],
    )


INVENTORY_COLUMNS = column_set(
    Column("item", "Feed Item"), Column("location", "Location", "text", "Details", "optional"),
    Column("purchased", "Purchased (Finance)", "kg", total=False), Column("consumed", "Consumed by TMR", "kg"),
    Column("adjusted", "Manual Corrections", "kg"), Column("balance", "Stock on Hand", "kg"),
    Column("unit", "Unit"), Column("reorder_level", "Reorder Level", "kg"), Column("status", "Stock Position", "status"),
    Column("unit_rate", "Latest Price (PKR)", "rate"), Column("stock_value", "Stock Value (PKR)", "money", total=True),
    Column("last_movement", "Last Movement", "date", "Details", "optional"),
)
STOCK_STATUS = {"OK": "Adequate", "LOW": "Low", "SHORTAGE": "Shortage", "NO_THRESHOLD": "No reorder level set"}


def build_inventory(ctx: ReportContext) -> ReportResult:
    from dairyos.api.feed_inventory_projection import authoritative_feed_inventory

    projection = authoritative_feed_inventory(container=ctx.container)
    only_attention = ctx.flag("only_attention")
    rows = []
    for item in projection.get("items", []):
        status = upper(item.get("status"))
        if only_attention and status not in {"LOW", "SHORTAGE"}:
            continue
        rate = item.get("latest_finance_unit_rate")
        balance = float(item.get("balance") or 0)
        rows.append({
            "item": clean_text(item.get("display_name") or item.get("item")), "location": clean_text(item.get("location")),
            "purchased": item.get("purchased_from_finance"), "consumed": item.get("auto_consumed_from_tmr"),
            "adjusted": item.get("manual_override_net"), "balance": balance, "unit": clean_text(item.get("unit")),
            "reorder_level": item.get("reorder_level"), "status": STOCK_STATUS.get(status, _label(status)),
            "unit_rate": float(rate) if rate is not None else None,
            "stock_value": money(balance * float(rate)) if rate is not None else None,
            "last_movement": to_date(item.get("last_movement_at")),
        })
    return ReportResult(
        sections=[Section("inventory", "Feed Inventory", INVENTORY_COLUMNS, rows,
                          {"_label": "Total", "stock_value": sum((r["stock_value"] for r in rows if r["stock_value"] is not None), money(0))},
                          primary=True)],
        summary=[Metric("items", "Feed Items", len(rows), "integer"),
                 Metric("low", "Low Stock", sum(1 for r in rows if r["status"] == "Low"), "integer"),
                 Metric("shortage", "In Shortage", sum(1 for r in rows if r["status"] == "Shortage"), "integer"),
                 Metric("value", "Stock Value", sum((r["stock_value"] for r in rows if r["stock_value"] is not None), money(0)),
                        "money", "Stock on hand at the latest Finance purchase price")],
        notes=["Stock Value is a derived figure: stock on hand multiplied by the latest Finance purchase price. "
               "Items never purchased through Finance carry no value."],
    )


MOVEMENT_COLUMNS = column_set(
    Column("date", "Date", "date"), Column("item", "Feed Item"), Column("movement", "Movement", "status"),
    Column("quantity_in", "In", "kg", total=True), Column("quantity_out", "Out", "kg", total=True),
    Column("unit", "Unit"), Column("source", "Source"), Column("supplier", "Supplier", "text", "Details", "optional"),
    Column("location", "Location", "text", "Details", "optional"), Column("recorded_by", "Recorded By", "text", "Details", "optional"),
    Column("notes", "Notes", "text", "Details", "optional"),
)


def build_stock_movement(ctx: ReportContext) -> ReportResult:
    start = datetime.combine(ctx.period.start, time.min)
    end = datetime.combine(ctx.period.end + timedelta(days=1), time.min)
    item_filter, kind = ctx.filter("item"), ctx.filter("movement_type")
    rows = []
    clinical_source_types = {"CLINICAL_RECEIPT", "TREATMENT_CONSUMPTION", "VACCINATION_CONSUMPTION"}
    for record in ctx.session.query(InventoryTransaction).filter(
        InventoryTransaction.recorded_at >= start, InventoryTransaction.recorded_at < end,
    ).order_by(InventoryTransaction.recorded_at, InventoryTransaction.id).all():
        # Clinical consumables have their own governed authority. They must
        # never be presented as feed or included in feed kg totals.
        if upper(record.source_type) in clinical_source_types:
            continue
        if item_filter and item_filter.lower() not in str(record.item or "").lower():
            continue
        if kind and upper(record.movement_type) != kind:
            continue
        signed = float(record.signed_quantity or 0)
        notes = clean_text(record.notes) or ""
        source = ("Governed TMR consumption" if "TMR_AUTO_CONSUMPTION_DATE=" in notes
                  else "Manual stock correction" if "FEED_STORAGE_MANUAL_OVERRIDE" in notes
                  else "Finance purchase" if notes.startswith("Finance transaction #") or upper(record.source_type) == "FINANCE"
                  else _label(record.source_type) or "Operator entry")
        rows.append({
            "date": to_date(record.recorded_at), "item": clean_text(record.item), "movement": _label(record.movement_type),
            "quantity_in": round(signed, 3) if signed > 0 else None, "quantity_out": round(-signed, 3) if signed < 0 else None,
            "unit": clean_text(record.unit), "source": source, "supplier": clean_text(record.supplier),
            "location": clean_text(record.location), "recorded_by": clean_text(record.recorded_by),
            "notes": None if source != "Operator entry" else notes or None,
        })
    return ReportResult(
        sections=[Section("movements", "Feed Stock Movement", MOVEMENT_COLUMNS, rows,
                          {"_label": "Total", "quantity_in": round(sum(r["quantity_in"] or 0 for r in rows), 3),
                           "quantity_out": round(sum(r["quantity_out"] or 0 for r in rows), 3)}, primary=True)],
        summary=[Metric("movements", "Movements", len(rows), "integer")],
        notes=["In and Out totals mix units when several feed items are listed. Filter by feed item for a meaningful total."],
    )


PURCHASE_COLUMNS = column_set(
    Column("date", "Date", "date"), Column("transaction_no", "Transaction No."), Column("group", "Feed Group"),
    Column("item", "Feed Item"), Column("supplier", "Supplier"), Column("quantity", "Quantity", "number"),
    Column("unit", "Unit"), Column("unit_rate", "Rate (PKR)", "rate"), Column("amount", "Amount (PKR)", "money", total=True),
    Column("status", "Status", "status"),
)


def build_purchases(ctx: ReportContext) -> ReportResult:
    from dairyos.finance import ledger_semantics as semantics
    from dairyos.reporting.areas.finance import ledger_rows

    rows = []
    for record in ledger_rows(ctx, ctx.period.start, ctx.period.end):
        if not classifier.is_expense(record):
            continue
        master, _code, group, item = semantics.expense_category(record)
        if master != "Feed" and not (master == "Legacy" and upper(record.category) == "FEED"):
            continue
        rows.append({"date": to_date(record.transaction_date), "transaction_no": f"FIN-{record.id}", "group": group,
                     "item": item, "supplier": clean_text(record.counterparty), "quantity": record.quantity,
                     "unit": clean_text(record.unit), "unit_rate": float(record.unit_rate) if record.unit_rate is not None else None,
                     "amount": money(record.amount), "status": upper(record.status) or "RECORDED"})
    total = sum((r["amount"] for r in rows), money(0))
    return ReportResult(
        sections=[Section("purchases", "Feed Purchases", PURCHASE_COLUMNS, rows, {"_label": "Total", "amount": total}, primary=True)],
        summary=[Metric("amount", "Feed Purchased", total, "money"), Metric("count", "Purchases", len(rows), "integer")],
        notes=["Feed purchases are Finance expenses. Feed cost in Cost of Milk comes from TMR consumption, not from purchases."],
    )


def _definition(report_id, title, purpose, builder, **kwargs) -> ReportDefinition:
    return ReportDefinition(id=report_id, area=AREA, title=title, purpose=purpose,
                            permission=PERMISSION, builder=builder, **kwargs)


def _stage_options() -> tuple[tuple[str, str], ...]:
    from dairyos.api.tmr import STAGE_LABELS

    return tuple((key, label) for key, label in STAGE_LABELS.items())


REPORTS: tuple[ReportDefinition, ...] = (
    _definition("feed-current-tmr", "Current TMR & Feed Cost by Category",
                "Today's rations, ingredient prices, feed cost per animal and herd feed cost by category.",
                build_current_tmr, columns=RATION_COLUMNS, authority=TMR_AUTHORITY, basis="CALCULATED",
                filters=(Filter("stage", "Feeding Stage", options=_stage_options()),)),
    _definition("feed-daily-cost", "Daily Feed Cost & Feed Cost per Litre",
                "Locked daily herd feed cost against milk produced, giving feed cost per litre for each day and the period.",
                build_daily_feed_cost, period="range", columns=DAILY_COST_COLUMNS, default_sort=("date", "asc"),
                authority="Daily TMR cost snapshots (the Cost of Milk feed authority) and the milk production ledger",
                basis="CALCULATED"),
    _definition("feed-inventory", "Feed Inventory",
                "Stock on hand for every feed item with purchases, TMR consumption, corrections and reorder position.",
                build_inventory, columns=INVENTORY_COLUMNS, default_sort=("item", "asc"),
                authority="Feed Storage projection: Finance purchases, governed TMR consumption, signed corrections",
                basis="CALCULATED",
                filters=(Filter("only_attention", "Only low stock and shortages", "toggle", default=False),)),
    _definition("feed-stock-movement", "Feed Stock Movement",
                "Every feed stock movement in the period: purchases in, TMR consumption out and manual corrections.",
                build_stock_movement, period="range", columns=MOVEMENT_COLUMNS, default_sort=("date", "asc"),
                authority="Inventory movement ledger",
                filters=(Filter("item", "Feed item contains", "text"),
                         Filter("movement_type", "Movement", options=(
                             ("PURCHASE", "Purchase"), ("RECEIPT", "Receipt"), ("CONSUMPTION", "Consumption"),
                             ("TRANSFER", "Transfer"), ("WASTAGE", "Wastage"), ("ADJUSTMENT", "Adjustment"))))),
    _definition("feed-purchases", "Feed Purchases",
                "Feed bought in the period by item and supplier, with quantity, rate and amount.",
                build_purchases, period="range", columns=PURCHASE_COLUMNS, default_sort=("date", "asc"),
                authority="Finance FEED expenses"),
)
