"""Date-effective TMR valuation shared by storage reconciliation and COP."""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from types import SimpleNamespace

from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.models.feed_ration import FeedRation
from dairyos.farm.reproduction.services.post_calving_return_service import persisted_breeding_payloads

DAILY_GROUP = "TMR_DAILY_MATERIALIZED"


def herd_counts_for_day(factory, day):
    from dairyos.api.tmr import CATEGORY_STAGE_MAP, _as_date, _normalize_herd_category

    counts = dict.fromkeys(CATEGORY_STAGE_MAP, 0)
    events = [dict(row.payload or {}) for row in factory.session.query(EventJournalModel).all()]
    breeding = persisted_breeding_payloads(factory)
    for animal in factory.animal().get_all():
        birth = _as_date(animal.date_of_birth)
        acquired = _as_date(animal.date_of_acquisition)
        if (birth and birth > day) or (acquired and acquired > day):
            continue
        lifecycle = str(animal.lifecycle_status or "").upper()
        active = bool(animal.active)
        transitions = []
        for payload in events:
            if payload.get("animal_id") != animal.animal_id:
                continue
            when = _as_date(payload.get("effective_date") or payload.get("timestamp"))
            if when is None:
                continue
            kind = payload.get("input_type")
            if kind == "animal_lifecycle":
                transitions.append((when, str(payload.get("lifecycle_status") or "").upper(), payload.get("previous_status")))
            elif kind == "animal_disposition":
                transitions.append((when, str(payload.get("disposition") or "").upper(), None))
        for payload in breeding:
            if payload.get("animal_id") != animal.animal_id:
                continue
            when = _as_date(payload.get("timestamp"))
            kind = str(payload.get("event_type") or "").lower()
            if when and kind in {"calving", "calved", "parturition", "dry_off"}:
                transitions.append((when, "DRY", None))
        for row in factory.animal().get_milking_frequency_history(animal.animal_id):
            if row.reason == "POST_CALVING_PLANNED_RETURN":
                transitions.append((_as_date(row.effective_from), "LACTATING", "DRY"))
        transitions.sort(key=lambda item: item[0])
        applicable = [item for item in transitions if item[0] <= day]
        if applicable:
            lifecycle = applicable[-1][1]
            active = lifecycle not in {"SOLD", "DECEASED", "INACTIVE", "DEAD"}
        elif transitions:
            # An explicit prior state is the baseline before its transition.
            prior = transitions[0][2]
            if prior:
                lifecycle = str(prior).upper()
                active = True
            elif lifecycle in {"SOLD", "DECEASED"}:
                histories = factory.animal().get_milking_frequency_history(animal.animal_id)
                lifecycle = "LACTATING" if histories else ("BULL" if animal.sex == "MALE" else "HEIFER")
                active = True
            elif lifecycle == "LACTATING" and any(item[1] == "DRY" for item in transitions):
                lifecycle = "DRY"
        if not active:
            continue
        category = _normalize_herd_category(SimpleNamespace(
            lifecycle_status=lifecycle, sex=animal.sex, animal_type=animal.animal_type,
            is_currently_milking=lifecycle == "LACTATING",
        ))
        if category in counts:
            counts[category] += 1
    return counts


def summary_for_day(factory, day, today, live_summary):
    from dairyos.api.tmr import (
        CATEGORY_STAGE_MAP, STAGE_LABELS, _as_date, _category_costs,
        _endorsement_snapshots, _finance_price_authority, _priced_stage,
        _week_bounds,
    )

    if day == today:
        return live_summary, "LIVE_TMR"
    prices = _finance_price_authority(factory, day)
    week_start, _ = _week_bounds(day)
    endorsed = next((row for row in _endorsement_snapshots(factory)
                     if row.get("week_start") == week_start.isoformat()
                     and (_as_date(row.get("recorded_at")) or date.min) <= day), None)
    stages = {key: _priced_stage(factory, key, prices, as_of=day) for key in STAGE_LABELS}
    basis = "DATE_EFFECTIVE_TMR"
    if endorsed and endorsed.get("stages"):
        stages = deepcopy(endorsed["stages"])
        # Endorsement supplies the ration, never the week's frozen headcount
        # or a purchase rate from a different operational day.
        for stage in stages.values():
            for ingredient in stage["ingredients"]:
                source = ingredient.get("selected_price_source", ingredient.get("price_source"))
                finance = prices.get(ingredient["catalog_name"])
                rate = (finance["price_per_kg"] if source == "FINANCE" and finance
                        else ingredient.get("manual_price_per_kg", ingredient.get("fallback_price_per_kg", 0)))
                kg = float(ingredient["quantity"]) / (1000 if ingredient["dose_unit"] == "g" else 1)
                ingredient.update(price_per_kg=rate, cost_per_head_day=kg * rate)
            stage["cost_per_head_day"] = sum(row["cost_per_head_day"] for row in stage["ingredients"])
        basis = "WEEKLY_VET_ENDORSED_TMR"
    counts = herd_counts_for_day(factory, day)

    # Historical stage membership is not reconstructed from today's
    # production_group. Single-stage categories remain exact; Milking and Dry
    # require a previously locked daily snapshot to be authoritative.
    stage_counts = {stage: 0 for stage in STAGE_LABELS}
    unallocated = {category: 0 for category in CATEGORY_STAGE_MAP}
    for category, stage_keys in CATEGORY_STAGE_MAP.items():
        population = int(counts.get(category, 0))
        if len(stage_keys) == 1:
            stage_counts[stage_keys[0]] = population
        else:
            unallocated[category] = population

    categories = _category_costs(
        stages,
        counts,
        stage_counts=stage_counts,
        unallocated=unallocated,
    )
    allocation_complete = all(row["allocation_complete"] for row in categories)
    price_complete = all(
        str(ingredient.get("price_source") or "").upper() != "MANUAL_FALLBACK"
        for stage, population in stage_counts.items()
        if population > 0
        for ingredient in stages[stage]["ingredients"]
        if float(ingredient.get("quantity") or 0.0) > 0
    )
    return {
        **live_summary,
        "operational_date": day.isoformat(),
        "stages": stages,
        "herd_counts": counts,
        "categories": categories,
        "stage_allocation_complete": allocation_complete,
        "price_authority_complete": price_complete,
        "cop_authority_complete": allocation_complete and price_complete,
        "total_herd_feed_cost_per_day": sum(
            row["category_cost_per_day"] for row in categories
        ),
        "authoritative_total_herd_feed_cost_per_day": (
            sum(
                float(row["authoritative_category_cost_per_day"] or 0.0)
                for row in categories
            )
            if allocation_complete and price_complete
            else None
        ),
    }, basis


def daily_snapshots(factory):
    return {row.effective_date: row for row in reversed(factory.feed_rations().get_active_for_group(DAILY_GROUP))}


def materialize_daily_cost(factory, day, summary, basis, requirement, existing_for_day, record=None):
    """Freeze quantities and date-effective prices, including ingredients without stock."""
    from dairyos.api.feed_inventory import convert_quantity

    quantities = dict(requirement)
    locked = {}
    for row in existing_for_day:
        locked[row.item] = locked.get(row.item, 0.0) - float(convert_quantity(row.signed_quantity, row.unit, "kg"))
    quantities.update(locked)
    if not bool(summary.get("stage_allocation_complete")):
        raise ValueError(
            f"Cannot materialize TMR quantities for {day}: "
            "stage allocation is incomplete."
        )

    cost_authority_complete = bool(summary.get("price_authority_complete"))
    costs, weights = {}, {}
    for category in summary["categories"]:
        if not bool(category.get("allocation_complete")):
            raise ValueError(
                f"Cannot materialize TMR for {day}: incomplete stage allocation "
                f"for {category.get('category')}."
            )
        stage_counts = category.get("stage_counts") or {}
        for key in category["stage_keys"]:
            population = int(stage_counts.get(key) or 0)
            if population <= 0:
                continue
            for row in summary["stages"][key]["ingredients"]:
                kg = float(row["quantity"]) / (1000 if row["dose_unit"] == "g" else 1)
                quantity = kg * population
                name = row["catalog_name"]
                weights[name] = weights.get(name, 0.0) + quantity
                costs[name] = costs.get(name, 0.0) + quantity * float(row["price_per_kg"])
    lines = []
    for name, quantity in sorted(quantities.items()):
        rate = costs.get(name, 0.0) / weights[name] if weights.get(name) else None
        if rate is None and cost_authority_complete:
            from dairyos.api.tmr import _finance_price_authority
            price = _finance_price_authority(factory, day).get(name)
            if price is None and quantity:
                cost_authority_complete = False
            else:
                rate = price["price_per_kg"] if price else 0.0

        lines.append(
            {
                "item": name,
                "quantity_kg": quantity,
                "price_per_kg": rate if cost_authority_complete else None,
                "cost": quantity * rate if cost_authority_complete and rate is not None else None,
            }
        )
    if not cost_authority_complete:
        for line in lines:
            line["price_per_kg"] = None
            line["cost"] = None

    payload = {
        "date": day.isoformat(),
        "basis": basis,
        "herd_counts": summary["herd_counts"],
        "stage_counts": {
            category["category"]: category.get("stage_counts") or {}
            for category in summary["categories"]
        },
        "quantity_authority_complete": True,
        "authority_complete": cost_authority_complete,
        "ingredients": lines,
        "feed_cost": (
            sum(float(row["cost"] or 0.0) for row in lines)
            if cost_authority_complete
            else None
        ),
    }
    if record is None:
        record = FeedRation(name=f"Daily TMR {day}", animal_group=DAILY_GROUP,
            effective_date=day.isoformat(), operator="SYSTEM_TMR")
    record.ingredients_json = json.dumps(payload, sort_keys=True)
    factory.session.add(record)
    return payload
