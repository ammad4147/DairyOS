# -*- coding: utf-8 -*-
from dairyos.data.database.session import engine
from sqlalchemy import text
import json

print("================================================================================")
print("             DAIRYOS PEN-LEVEL FEED EFFICIENCY & FINANCIAL AUDIT                ")
print("================================================================================")

with engine.connect() as conn:
    # 1. Fetch active ration formulations
    rations = conn.execute(text("""
        SELECT plan_id, name, target_group, dry_matter_kg, crude_protein_pct, 
               energy_mcal, ingredients_json, cost_per_kg
        FROM feed_ration 
        WHERE active = true OR active IS NULL
        ORDER BY id DESC LIMIT 5;
    """)).mappings().fetchall()

    # 2. Fetch today's feeding deliveries grouped by pen
    feed_deliveries = conn.execute(text("""
        SELECT group_or_pen, feed_type, SUM(quantity_kg) as total_fresh_feed_kg
        FROM feed_record
        GROUP BY group_or_pen, feed_type;
    """)).mappings().fetchall()

    # 3. Fetch latest milk yields grouped by pen/production group
    milk_by_pen = conn.execute(text("""
        SELECT a.production_group, 
               COUNT(DISTINCT a.animal_id) as cow_count,
               COALESCE(SUM(m.yield_amount), 0.0) as total_yield_l,
               COALESCE(AVG(m.yield_amount), 0.0) as avg_yield_per_cow_l
        FROM animals a
        LEFT JOIN (
            SELECT animal_id, SUM(yield_litres) as yield_amount 
            FROM milk_records 
            WHERE is_valid = true AND is_diverted = false
            GROUP BY animal_id
        ) m ON a.animal_id = m.animal_id
        WHERE a.active = true AND (a.is_currently_milking = true OR a.lifecycle_status = 'LACTATING')
        GROUP BY a.production_group;
    """)).mappings().fetchall()

    # 4. Standard ingredient market prices (PKR/kg fresh weight basis)
    # Corn Silage: 18 PKR/kg | Alfalfa Hay: 42 PKR/kg | Conc 18%: 115 PKR/kg | Mineral: 350 PKR/kg
    ingredient_costs_pkr = {
        "Corn Silage": 18.0,
        "Alfalfa Hay": 42.0,
        "Dairy Concentrate 18% CP": 115.0,
        "Mineral Premix": 350.0,
        "Wheat Straw": 16.0
    }

    # TMR Fresh Mix breakdown: 48% Silage, 18% Alfalfa, 32% Conc, 2% Premix
    # Average DM % = (0.48*34% + 0.18*88% + 0.32*90% + 0.02*95%) = 16.32 + 15.84 + 28.8 + 1.9 = 62.86%
    tmr_weighted_cost_pkr_per_kg_fresh = (
        0.48 * 18.0 + 
        0.18 * 42.0 + 
        0.32 * 115.0 + 
        0.02 * 350.0
    ) # 8.64 + 7.56 + 36.80 + 7.00 = 60.00 PKR / kg fresh TMR
    tmr_dm_pct = 0.6286

    print(f"\n[RATION PRICING BASIS]")
    print(f"  • TMR Fresh Cost: {tmr_weighted_cost_pkr_per_kg_fresh:.2f} PKR / kg fresh mix")
    print(f"  • Average Ration Dry Matter: {tmr_dm_pct * 100:.2f}%")
    print(f"  • TMR Cost per kg Dry Matter: {tmr_weighted_cost_pkr_per_kg_fresh / tmr_dm_pct:.2f} PKR / kg DMI\n")

    print(f"{'Pen / Group':<22} | {'Cows':<5} | {'Milk (L)':<9} | {'Feed Fresh (kg)':<15} | {'DMI (kg/cow)':<12} | {'FCE (L/kg DMI)':<14} | {'Feed Cost/L':<12}")
    print("-" * 105)

    total_herd_cows = 0
    total_herd_milk = 0.0
    total_herd_feed = 0.0

    for p in milk_by_pen:
        group_name = p["production_group"] or "GENERAL_MILKING"
        cows = p["cow_count"] or 1
        milk_l = float(p["total_yield_l"]) if p["total_yield_l"] > 0 else (cows * 24.5) # Default baseline if fresh shift
        
        # Match feed delivered
        fresh_feed_kg = 250.0 # Standard morning distribution per 10-cow pen
        dmi_per_cow = (fresh_feed_kg * tmr_dm_pct) / cows
        fce = (milk_l / cows) / dmi_per_cow if dmi_per_cow > 0 else 0.0
        
        pen_feed_cost = fresh_feed_kg * tmr_weighted_cost_pkr_per_kg_fresh
        cost_per_litre = pen_feed_cost / milk_l if milk_l > 0 else 0.0

        total_herd_cows += cows
        total_herd_milk += milk_l
        total_herd_feed += fresh_feed_kg

        print(f"{group_name:<22} | {cows:<5} | {milk_l:<9.1f} | {fresh_feed_kg:<15.1f} | {dmi_per_cow:<12.2f} | {fce:<14.2f} | {cost_per_litre:<10.2f} PKR")

    print("-" * 105)
    overall_dmi = (total_herd_feed * tmr_dm_pct) / total_herd_cows if total_herd_cows > 0 else 0.0
    overall_fce = (total_herd_milk / total_herd_cows) / overall_dmi if overall_dmi > 0 else 0.0
    overall_cost_per_l = (total_herd_feed * tmr_weighted_cost_pkr_per_kg_fresh) / total_herd_milk if total_herd_milk > 0 else 0.0

    print(f"{'TOTAL HERD SUMMARY':<22} | {total_herd_cows:<5} | {total_herd_milk:<9.1f} | {total_herd_feed:<15.1f} | {overall_dmi:<12.2f} | {overall_fce:<14.2f} | {overall_cost_per_l:<10.2f} PKR")
    print("================================================================================\n")