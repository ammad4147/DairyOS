from pathlib import Path

# 1) tmr.py
path = Path("src/dairyos/api/tmr.py")
text = path.read_text(encoding="utf-8")

old1 = """        if selected_source == \"MANUAL\":
            rate = manual_rate
            effective_source = \"MANUAL\"
        elif finance is not None:
            rate = float(finance[\"price_per_kg\"])
            effective_source = \"FINANCE\"
        else:
            # Finance-preferred legacy/default rows remain usable when no
            # Finance purchase price exists. The fallback is explicit.
            rate = manual_rate
            effective_source = \"MANUAL_FALLBACK\"
            selected_source = \"MANUAL\"

        quantity = float(ingredient[\"quantity\"] or 0.0)
        dose_unit = ingredient[\"dose_unit\"]
        quantity_kg = (
            quantity / 1000.0
            if dose_unit == \"g\"
            else quantity
        )
        line_cost = quantity_kg * rate
        total += line_cost
        total_kg += quantity_kg
        rows.append(
            {
                **ingredient,
                \"price_per_kg\": round(rate, 4),
                \"price_source\": (
                    effective_source
                ),
                \"selected_price_source\": selected_source,
                \"manual_price_per_kg\": round(manual_rate, 4),
                \"finance_price_per_kg\": (
                    round(float(finance[\"price_per_kg\"]), 4)
                    if finance is not None
                    else None
                ),
                # Finance provenance remains visible even while Manual is
                # selected, so the operator can compare both authorities.
                \"finance_transaction_id\": (
                    finance[\"transaction_id\"]
                    if finance is not None
                    else None
                ),
                \"finance_purchase_date\": (
                    finance[\"purchase_date\"]
                    if finance is not None
                    else None
                ),
                \"cost_per_head_day\": round(line_cost, 4),
            }
        )

    return {
        \"key\": stage,
        \"label\": STAGE_LABELS[stage],
        \"ingredients\": rows,
        \"ration_kg_per_head_day\": round(total_kg, 4),
        \"cost_per_head_day\": round(total, 4),
        \"source\": \"GOVERNED_TMR\",
    }"""

new1 = """        # Price authority rules (TMR-01):
        # - FINANCE: valid Finance Feed purchase rate is authoritative.
        # - MANUAL: operator-confirmed rate is authoritative when selected.
        # - Catalog fallback_price_per_kg is reference/init only and must
        #   never silently become costing authority or enter a locked snapshot.
        if selected_source == \"MANUAL\":
            if manual_rate > 0:
                rate = manual_rate
                effective_source = \"MANUAL\"
                priced = True
            else:
                rate = None
                effective_source = \"MISSING_MANUAL\"
                priced = False
        elif finance is not None:
            rate = float(finance[\"price_per_kg\"])
            effective_source = \"FINANCE\"
            priced = True
        else:
            rate = None
            effective_source = \"UNPRICED\"
            priced = False

        quantity = float(ingredient[\"quantity\"] or 0.0)
        dose_unit = ingredient[\"dose_unit\"]
        quantity_kg = (
            quantity / 1000.0
            if dose_unit == \"g\"
            else quantity
        )
        if priced and rate is not None:
            line_cost = quantity_kg * rate
            total += line_cost
        else:
            line_cost = None
        total_kg += quantity_kg
        rows.append(
            {
                **ingredient,
                \"price_per_kg\": (
                    round(rate, 4) if rate is not None else None
                ),
                \"price_source\": effective_source,
                \"selected_price_source\": selected_source,
                \"manual_price_per_kg\": round(manual_rate, 4),
                \"finance_price_per_kg\": (
                    round(float(finance[\"price_per_kg\"]), 4)
                    if finance is not None
                    else None
                ),
                # Finance provenance remains visible even while Manual is
                # selected, so the operator can compare both authorities.
                \"finance_transaction_id\": (
                    finance[\"transaction_id\"]
                    if finance is not None
                    else None
                ),
                \"finance_purchase_date\": (
                    finance[\"purchase_date\"]
                    if finance is not None
                    else None
                ),
                \"cost_per_head_day\": (
                    round(line_cost, 4) if line_cost is not None else None
                ),
                \"priced\": priced,
            }
        )

    costing_complete = all(
        bool(row.get(\"priced\")) for row in rows
    ) if rows else True

    return {
        \"key\": stage,
        \"label\": STAGE_LABELS[stage],
        \"ingredients\": rows,
        \"ration_kg_per_head_day\": round(total_kg, 4),
        \"cost_per_head_day\": (
            round(total, 4) if costing_complete else None
        ),
        \"costing_complete\": costing_complete,
        \"source\": \"GOVERNED_TMR\",
    }"""

assert old1 in text, "priced_stage block not found"
text = text.replace(old1, new1, 1)

old2 = """def _category_costs(stages: dict, counts: dict[str, int]) -> list[dict]:
    result = []
    for category, stage_keys in CATEGORY_STAGE_MAP.items():
        values = [
            float(stages[key][\"cost_per_head_day\"])
            for key in stage_keys
        ]
        # Deliberate management-estimate simplification: detailed feeding
        # stages are averaged to the DairyOS animal category before the
        # category count is applied.
        head_cost = sum(values) / len(values) if values else 0.0
        count = int(counts.get(category, 0))
        result.append(
            {
                \"category\": category,
                \"stage_keys\": stage_keys,
                \"animal_count\": count,
                \"population_authority\": \"ACTIVE_ANIMAL_REGISTER\",
                \"cost_per_head_day\": round(head_cost, 4),
                \"category_cost_per_day\": round(head_cost * count, 4),
            }
        )
    return result"""

new2 = """def _category_costs(stages: dict, counts: dict[str, int]) -> list[dict]:
    result = []
    for category, stage_keys in CATEGORY_STAGE_MAP.items():
        stage_rows = [stages[key] for key in stage_keys if key in stages]
        complete = all(
            bool(row.get(\"costing_complete\", True))
            and row.get(\"cost_per_head_day\") is not None
            for row in stage_rows
        ) if stage_rows else True
        values = [
            float(row[\"cost_per_head_day\"])
            for row in stage_rows
            if row.get(\"cost_per_head_day\") is not None
        ]
        # Deliberate management-estimate simplification: detailed feeding
        # stages are averaged to the DairyOS animal category before the
        # category count is applied. Incomplete costing is never zero-filled.
        head_cost = (
            sum(values) / len(values) if values and complete else None
        )
        count = int(counts.get(category, 0))
        result.append(
            {
                \"category\": category,
                \"stage_keys\": stage_keys,
                \"animal_count\": count,
                \"population_authority\": \"ACTIVE_ANIMAL_REGISTER\",
                \"cost_per_head_day\": (
                    round(head_cost, 4) if head_cost is not None else None
                ),
                \"category_cost_per_day\": (
                    round(head_cost * count, 4)
                    if head_cost is not None
                    else None
                ),
                \"costing_complete\": complete,
            }
        )
    return result"""

assert old2 in text, "category_costs block not found"
text = text.replace(old2, new2, 1)

old3 = """    categories = _category_costs(stages, counts)
    total_daily = sum(
        float(row[\"category_cost_per_day\"])
        for row in categories
    )
    milk_today = milk_litres_for_period(
        factory,
        operational_date,
        operational_date,
    )
    feed_per_litre = (
        total_daily / milk_today
        if milk_today > 0
        else None
    )
    payload = {
        \"data_status\": \"LIVE_PERSISTED_TMR\",
        \"operational_date\": operational_date.isoformat(),
        \"ingredients\": _ingredient_definitions(factory),
        \"stages\": stages,
        \"categories\": categories,
        \"herd_counts\": counts,
        \"total_herd_feed_cost_per_day\": round(total_daily, 4),
        \"milk_production_today_liters\": round(milk_today, 4),
        \"feed_cost_per_litre_today\": (
            round(feed_per_litre, 4)
            if feed_per_litre is not None
            else None
        ),
        \"feed_cost_basis\": \"TMR_RATION_X_ACTIVE_HERD\",
        \"shared_price_preferences\": _public_shared_price_preferences(
            shared_price_preferences
"""

new3 = """    categories = _category_costs(stages, counts)
    costing_complete = all(
        bool(row.get(\"costing_complete\", True))
        and row.get(\"category_cost_per_day\") is not None
        for row in categories
    )
    priced_category_costs = [
        float(row[\"category_cost_per_day\"])
        for row in categories
        if row.get(\"category_cost_per_day\") is not None
    ]
    total_daily = (
        sum(priced_category_costs) if costing_complete and priced_category_costs else None
    )
    milk_today = milk_litres_for_period(
        factory,
        operational_date,
        operational_date,
    )
    feed_per_litre = (
        total_daily / milk_today
        if total_daily is not None and milk_today > 0
        else None
    )
    payload = {
        \"data_status\": \"LIVE_PERSISTED_TMR\",
        \"operational_date\": operational_date.isoformat(),
        \"ingredients\": _ingredient_definitions(factory),
        \"stages\": stages,
        \"categories\": categories,
        \"herd_counts\": counts,
        \"total_herd_feed_cost_per_day\": (
            round(total_daily, 4) if total_daily is not None else None
        ),
        \"costing_complete\": costing_complete,
        \"milk_production_today_liters\": round(milk_today, 4),
        \"feed_cost_per_litre_today\": (
            round(feed_per_litre, 4)
            if feed_per_litre is not None
            else None
        ),
        \"feed_cost_basis\": \"TMR_RATION_X_ACTIVE_HERD\",
        \"shared_price_preferences\": _public_shared_price_preferences(
            shared_price_preferences
"""

assert old3 in text, "live summary block not found"
text = text.replace(old3, new3, 1)

old4 = """    snapshot = {
        \"kind\": \"TMR_DAILY_COST_SNAPSHOT\",
        \"operational_date\": selected_date.isoformat(),
        \"locked_at\": authority.current_datetime().isoformat(),
        \"basis\": \"GOVERNED_TMR_X_ACTIVE_HERD_AT_12_00\",
        \"herd_counts\": live[\"herd_counts\"],
        \"categories\": live[\"categories\"],
        \"stages\": live[\"stages\"],
        \"total_herd_feed_cost_per_day\": round(
            float(live[\"total_herd_feed_cost_per_day\"]),
            4,
        ),
    }"""

new4 = """    live_total = live.get(\"total_herd_feed_cost_per_day\")
    live_complete = bool(live.get(\"costing_complete\", True))
    snapshot = {
        \"kind\": \"TMR_DAILY_COST_SNAPSHOT\",
        \"operational_date\": selected_date.isoformat(),
        \"locked_at\": authority.current_datetime().isoformat(),
        \"basis\": \"GOVERNED_TMR_X_ACTIVE_HERD_AT_12_00\",
        \"herd_counts\": live[\"herd_counts\"],
        \"categories\": live[\"categories\"],
        \"stages\": live[\"stages\"],
        \"costing_complete\": live_complete,
        \"total_herd_feed_cost_per_day\": (
            round(float(live_total), 4)
            if live_total is not None and live_complete
            else None
        ),
    }"""

assert old4 in text, "snapshot block not found"
text = text.replace(old4, new4, 1)

old5 = """        if snapshot is not None:
            amount = float(
                snapshot.get(\"total_herd_feed_cost_per_day\")
                or 0.0
            )
            total += amount
            locked_days += 1
            basis = \"LOCKED_DAILY_TMR\"
            record_id = snapshot.get(\"record_id\")
            locked_at = snapshot.get(\"locked_at\")

        elif day == today and live_today is not None:
            amount = float(
                live_today.get(\"total_herd_feed_cost_per_day\")
                or 0.0
            )
            total += amount
            provisional_days += 1
            basis = \"LIVE_TMR_PENDING_12_00_LOCK\"
            record_id = None
            locked_at = None
"""

new5 = """        if snapshot is not None:
            snap_complete = bool(snapshot.get(\"costing_complete\", True))
            raw_amount = snapshot.get(\"total_herd_feed_cost_per_day\")
            if snap_complete and raw_amount is not None:
                amount = float(raw_amount)
                total += amount
                locked_days += 1
                basis = \"LOCKED_DAILY_TMR\"
            else:
                amount = None
                basis = \"LOCKED_DAILY_TMR_INCOMPLETE_COSTING\"
                missing_authority_days.append(key)
            record_id = snapshot.get(\"record_id\")
            locked_at = snapshot.get(\"locked_at\")

        elif day == today and live_today is not None:
            live_complete = bool(live_today.get(\"costing_complete\", True))
            raw_amount = live_today.get(\"total_herd_feed_cost_per_day\")
            if live_complete and raw_amount is not None:
                amount = float(raw_amount)
                total += amount
                provisional_days += 1
                basis = \"LIVE_TMR_PENDING_12_00_LOCK\"
            else:
                amount = None
                basis = \"LIVE_TMR_INCOMPLETE_COSTING\"
                missing_authority_days.append(key)
            record_id = None
            locked_at = None
"""

assert old5 in text, "feed cost period block not found"
text = text.replace(old5, new5, 1)
path.write_text(text, encoding="utf-8")
print("tmr.py OK")

# 2) finance test
p = Path("tests/api/test_tmr_finance_price_authority.py")
t = p.read_text(encoding="utf-8")
old = """    def test_manual_fallback_remains_when_finance_has_no_price(self):
        self.assertIn('\"MANUAL_FALLBACK\"', self.api)
        self.assertIn(\"fallback_price_per_kg\", self.api)
"""
new = """    def test_catalog_fallback_is_not_costing_authority(self):
        # TMR-01: catalog/reference defaults must not silently become
        # locked snapshot or COP authority.
        self.assertNotIn('\"MANUAL_FALLBACK\"', self.api)
        self.assertIn('\"UNPRICED\"', self.api)
        self.assertIn('\"MISSING_MANUAL\"', self.api)
        self.assertIn(\"costing_complete\", self.api)
        self.assertIn(\"fallback_price_per_kg\", self.api)
"""
assert old in t, "finance test block not found"
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("finance test OK")

# 3) cop test
p = Path("tests/api/test_tmr_cop_authority.py")
t = p.read_text(encoding="utf-8")
t = t.replace(
    '"head_cost = sum(values) / len(values) if values else 0.0"',
    '"sum(values) / len(values) if values and complete else None"',
)
old = """    def test_finance_price_authority_excludes_void(self):
        self.assertIn(\"if not is_active(row):\", self.tmr)
        self.assertIn('\"price_source\": (', self.tmr)
        self.assertIn('\"FINANCE\"', self.tmr)
"""
new = """    def test_finance_price_authority_excludes_void(self):
        self.assertIn(\"if not is_active(row):\", self.tmr)
        self.assertIn('\"price_source\": effective_source', self.tmr)
        self.assertIn('\"FINANCE\"', self.tmr)
"""
assert old in t, "cop void test block not found"
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("cop test OK")

# 4) reporting
p = Path("src/dairyos/reporting/areas/feed.py")
t = p.read_text(encoding="utf-8")
old = """PRICE_SOURCE_LABELS = {\"FINANCE\": \"Latest Finance purchase\", \"MANUAL\": \"Manual price\",
                       \"MANUAL_FALLBACK\": \"Manual price (no Finance purchase)\"}"""
new = """PRICE_SOURCE_LABELS = {
    \"FINANCE\": \"Latest Finance purchase\",
    \"MANUAL\": \"Manual price\",
    \"UNPRICED\": \"No price authority\",
    \"MISSING_MANUAL\": \"Manual selected but rate missing\",
}"""
assert old in t, "reporting labels not found"
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("reporting OK")

# 5) frontend
p = Path("src/DairyOS.Web/src/components/TMRPreparationTool.tsx")
t = p.read_text(encoding="utf-8")
old_src = "price_source:'FINANCE'|'MANUAL'|'MANUAL_FALLBACK'"
new_src = "price_source:'FINANCE'|'MANUAL'|'UNPRICED'|'MISSING_MANUAL'|string"
assert old_src in t, "frontend price_source type not found"
t = t.replace(old_src, new_src, 1)
old_cost = "cost_per_head_day:number"
new_cost = "cost_per_head_day:number|null;priced?:boolean"
assert old_cost in t, "frontend cost type not found"
t = t.replace(old_cost, new_cost, 1)
p.write_text(t, encoding="utf-8")
print("frontend OK")
print("TMR-01 apply complete")
