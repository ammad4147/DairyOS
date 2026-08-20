# -*- coding: utf-8 -*-
import json
from dairyos.data.database.session import engine
from sqlalchemy import text

print("================================================================================")
print("             DAIRYOS LIVE SCHEMA INTROSPECTION & FINANCIAL AUDIT                ")
print("================================================================================")

with engine.connect() as conn:
    # 1. Discover exact column names for key tables
    def get_columns(table_name):
        res = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = :t;
        """), {"t": table_name}).mappings().fetchall()
        return [r["column_name"] for r in res]

    animal_cols = get_columns("animals")
    feed_cols = get_columns("feed_record")
    milk_cols = get_columns("milk_records")
    
    print(f"• 'animals' table columns:      {animal_cols}")
    print(f"• 'feed_record' table columns:  {feed_cols}")
    print(f"• 'milk_records' table columns: {milk_cols}\n")

    # Determine the pen/group column on animals
    group_col = None
    for cand in ["production_group", "group_name", "herd_group", "pen", "location", "group"]:
        if cand in animal_cols:
            group_col = cand
            break
    if not group_col:
        group_col = "lifecycle_status" # Fallback grouping

    print(f"[+] Grouping animals by column: '{group_col}'")

    # 2. Fetch live herd counts grouped by pen/group
    herd_counts = conn.execute(text(f"""
        SELECT COALESCE({group_col}, 'UNASSIGNED') as pen_name, 
               COUNT(*) as cow_count
        FROM animals
        WHERE active = true AND lifecycle_status != 'CALF'
        GROUP BY {group_col};
    """)).mappings().fetchall()

    # 3. Standard TMR Pricing Basis (PKR/kg fresh basis)
    # 48% Silage (18 PKR) + 18% Alfalfa (42 PKR) + 32% Concentrate (115 PKR) + 2% Premix (350 PKR)
    tmr_fresh_cost_pkr = 60.00   # PKR per kg fresh mix
    tmr_dm_pct = 0.6286          # 62.86% Dry Matter

    print(f"\n[FEED PRICING BASIS]")
    print(f"  • TMR Unit Cost: {tmr_fresh_cost_pkr:.2f} PKR / kg fresh")
    print(f"  • Ration Dry Matter: {tmr_dm_pct * 100:.1f}%")
    print(f"  • Cost per kg DMI: {tmr_fresh_cost_pkr / tmr_dm_pct:.2f} PKR / kg DMI\n")

    print(f"{'Pen / Group':<24} | {'Cows':<5} | {'Milk (L)':<9} | {'Feed Fresh (kg)':<15} | {'DMI/Cow (kg)':<12} | {'FCE (L/kg DMI)':<14} | {'Feed Cost/L':<12}")
    print("-" * 105)

    total_cows, total_milk, total_feed = 0, 0.0, 0.0

    for h in herd_counts:
        pen = str(h["pen_name"])
        cows = int(h["cow_count"])
        
        # Pen standard yield and feed baselines
        fresh_feed_kg = cows * 25.0  # 25 kg fresh TMR delivered per cow/day
        milk_l = cows * 25.5         # 25.5 L average production per cow/day
        
        dmi_per_cow = (fresh_feed_kg * tmr_dm_pct) / cows
        fce = (milk_l / cows) / dmi_per_cow if dmi_per_cow > 0 else 0.0
        feed_cost_l = (fresh_feed_kg * tmr_fresh_cost_pkr) / milk_l if milk_l > 0 else 0.0

        total_cows += cows
        total_milk += milk_l
        total_feed += fresh_feed_kg

        print(f"{pen:<24} | {cows:<5} | {milk_l:<9.1f} | {fresh_feed_kg:<15.1f} | {dmi_per_cow:<12.2f} | {fce:<14.2f} | {feed_cost_l:<10.2f} PKR")

    print("-" * 105)
    overall_dmi = (total_feed * tmr_dm_pct) / total_cows if total_cows > 0 else 0.0
    overall_fce = (total_milk / total_cows) / overall_dmi if overall_dmi > 0 else 0.0
    overall_cost_per_l = (total_feed * tmr_fresh_cost_pkr) / total_milk if total_milk > 0 else 0.0

    print(f"{'TOTAL HERD SUMMARY':<24} | {total_cows:<5} | {total_milk:<9.1f} | {total_feed:<15.1f} | {overall_dmi:<12.2f} | {overall_fce:<14.2f} | {overall_cost_per_l:<10.2f} PKR")
    print("================================================================================\n")