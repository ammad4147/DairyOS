from pathlib import Path

# --- reporting ---
path = Path("src/dairyos/reporting/areas/feed.py")
text = path.read_text(encoding="utf-8")

old = """def build_current_tmr(ctx: ReportContext) -> ReportResult:
    from dairyos.reporting.areas.herd import CATEGORY_PLURALS

    summary = live_tmr(ctx)
    total = float(summary[\"total_herd_feed_cost_per_day\"] or 0)
    category_rows = [{
        \"category\": CATEGORY_PLURALS.get(row[\"category\"], row[\"category\"]), \"animals\": row[\"animal_count\"],
        \"cost_per_head_day\": money(row[\"cost_per_head_day\"]), \"category_cost_per_day\": money(row[\"category_cost_per_day\"]),
        \"share\": ratio(float(row[\"category_cost_per_day\"]) * 100, total, 1),
    } for row in summary[\"categories\"]]
"""

new = """def build_current_tmr(ctx: ReportContext) -> ReportResult:
    from dairyos.reporting.areas.herd import CATEGORY_PLURALS

    summary = live_tmr(ctx)
    # TMR-01: incomplete costing yields None totals — never float(None).
    raw_total = summary.get(\"total_herd_feed_cost_per_day\")
    total = float(raw_total) if raw_total is not None else 0.0
    costing_complete = bool(summary.get(\"costing_complete\", True))
    category_rows = []
    for row in summary[\"categories\"]:
        cat_cost = row.get(\"category_cost_per_day\")
        category_rows.append({
            \"category\": CATEGORY_PLURALS.get(row[\"category\"], row[\"category\"]),
            \"animals\": row[\"animal_count\"],
            \"cost_per_head_day\": money(row.get(\"cost_per_head_day\")),
            \"category_cost_per_day\": money(cat_cost),
            \"share\": (
                ratio(float(cat_cost) * 100, total, 1)
                if cat_cost is not None and total > 0
                else None
            ),
        })
"""

assert old in text, "reporting build_current_tmr block not found"
text = text.replace(old, new, 1)

old_metric = """        summary=[Metric(\"daily\", \"Herd Feed Cost per Day\", money(total), \"money\"),
                 Metric(\"milk\", \"Milk Today\", summary.get(\"milk_production_today_liters\"), \"litres\"),
                 Metric(\"per_litre\", \"Feed Cost per Litre Today\", summary.get(\"feed_cost_per_litre_today\"), \"rate\",
                        \"Not available until milk is recorded today\")],
        notes=[\"Category cost averages the feeding stages that make up the category, then multiplies by the animals \"
               \"currently in that category. This is the TMR authority's own method.\"],
"""

new_metric = """        summary=[Metric(\"daily\", \"Herd Feed Cost per Day\", money(total) if costing_complete else None, \"money\",
                        None if costing_complete else \"Incomplete ingredient price authority\"),
                 Metric(\"milk\", \"Milk Today\", summary.get(\"milk_production_today_liters\"), \"litres\"),
                 Metric(\"per_litre\", \"Feed Cost per Litre Today\", summary.get(\"feed_cost_per_litre_today\"), \"rate\",
                        \"Not available until milk is recorded today\" if summary.get(\"feed_cost_per_litre_today\") is None else None)],
        notes=[\"Category cost averages the feeding stages that make up the category, then multiplies by the animals \"
               \"currently in that category. This is the TMR authority's own method.\"]
               + ([] if costing_complete else [
                   \"One or more ingredients lack Finance or explicit Manual price authority; \"
                   \"herd feed cost is not presented as complete.\"
               ]),
"""

assert old_metric in text, "reporting metric block not found"
text = text.replace(old_metric, new_metric, 1)
path.write_text(text, encoding="utf-8")
print("reporting OK")

# --- integrated test ---
path = Path("tests/api/test_finance_tmr_cop_integrated_authority.py")
text = path.read_text(encoding="utf-8")

old = """    live = client.get(\"/farm/tmr\")
    assert live.status_code == 200, live.text
    live_summary = live.json()
    silage = next(
        ingredient
        for ingredient in live_summary[\"stages\"][\"early_milking\"][\"ingredients\"]
        if ingredient[\"catalog_name\"] == SILAGE
    )
    assert silage[\"price_per_kg\"] == 25
    assert silage[\"price_source\"] == \"FINANCE\"
    assert silage[\"finance_price_per_kg\"] == 25
    assert silage[\"price_per_kg\"] != 4000
"""

new = """    live = client.get(\"/farm/tmr\")
    assert live.status_code == 200, live.text
    live_summary = live.json()
    silage = next(
        ingredient
        for ingredient in live_summary[\"stages\"][\"early_milking\"][\"ingredients\"]
        if ingredient[\"catalog_name\"] == SILAGE
    )
    assert silage[\"price_per_kg\"] == 25
    assert silage[\"price_source\"] == \"FINANCE\"
    assert silage[\"finance_price_per_kg\"] == 25
    assert silage[\"price_per_kg\"] != 4000

    # TMR-01: catalog defaults are not costing authority. Explicit Manual rates
    # for remaining ingredients complete the ration so the Finance→snapshot→COP
    # chain can be certified without silent MANUAL_FALLBACK.
    early = live_summary[\"stages\"][\"early_milking\"]
    stage_payload = {
        \"stage\": \"early_milking\",
        \"operator\": \"Deep authority audit\",
        \"ingredients\": [
            {
                \"catalog_name\": item[\"catalog_name\"],
                \"quantity\": item[\"quantity\"],
                \"dose_unit\": item[\"dose_unit\"],
                \"fallback_price_per_kg\": float(
                    item.get(\"manual_price_per_kg\")
                    or item.get(\"fallback_price_per_kg\")
                    or 0
                ) or 1.0,
                \"price_source\": (
                    \"FINANCE\"
                    if item.get(\"finance_price_per_kg\")
                    else \"MANUAL\"
                ),
            }
            for item in early[\"ingredients\"]
        ],
        \"shared_price_preferences\": [
            {
                \"catalog_name\": item[\"catalog_name\"],
                \"fallback_price_per_kg\": float(
                    item.get(\"manual_price_per_kg\")
                    or item.get(\"fallback_price_per_kg\")
                    or 0
                ) or 1.0,
                \"price_source\": (
                    \"FINANCE\"
                    if item.get(\"finance_price_per_kg\")
                    else \"MANUAL\"
                ),
            }
            for item in early[\"ingredients\"]
        ],
    }
    saved = client.post(\"/farm/tmr/stages\", json=stage_payload)
    assert saved.status_code == 200, saved.text
    live = client.get(\"/farm/tmr\")
    assert live.status_code == 200, live.text
    live_summary = live.json()
    assert live_summary.get(\"costing_complete\") is True
"""

assert old in text, "integrated test block not found"
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("integrated test OK")
print("apply complete")
