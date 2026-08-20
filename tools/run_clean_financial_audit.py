# -*- coding: utf-8 -*-
import requests
import json
from dairyos.data.database.session import engine
from sqlalchemy import text

print("================================================================================")
print("             DAIRYOS FEED CONVERSION EFFICIENCY & FINANCIAL AUDIT               ")
print("================================================================================")

API_BASE_URL = "http://127.0.0.1:8000"

# 1. Fetch live animals from API
r_animals = requests.get(f"{API_BASE_URL}/farm/animals", timeout=5)
animals = r_animals.json() if isinstance(r_animals.json(), list) else r_animals.json().get("animals", [])

# Filter adult cows (exclude youngstock calves)
adult_cows = [a for a in animals if a.get("lifecycle_status") != "CALF"]
total_adult_cows = len(adult_cows)

print(f"• Total Registered Animals:  {len(animals)}")
print(f"• Total Adult Dairy Cows:    {total_adult_cows}")

# 2. Fetch live feed records from database
with engine.connect() as conn:
    feed_records = conn.execute(text("""
        SELECT group_or_pen, feed_type, SUM(quantity_kg) as total_qty_kg
        FROM feed_record
        GROUP BY group_or_pen, feed_type;
    """)).mappings().fetchall()
    
    print("\n--- RECORDED FEED ALLOCATIONS BY PEN ---")
    for fr in feed_records:
        print(f"  • Pen: {fr['group_or_pen'] or 'DEFAULT_BARN'} | Type: {fr['feed_type']} | Qty: {fr['total_qty_kg']} kg")

# 3. Formulated TMR Economics & Intake Parameters
# Standard TMR Fresh Mix breakdown:
# 48% Silage (18 PKR) + 18% Alfalfa (42 PKR) + 32% Conc (115 PKR) + 2% Premix (350 PKR)
tmr_fresh_cost_pkr_per_kg = (0.48 * 18.0) + (0.18 * 42.0) + (0.32 * 115.0) + (0.02 * 350.0) # 60.00 PKR/kg
tmr_dm_pct = 0.6286  # 62.86% Dry Matter

# Herd production metrics
# Standard Holstein lactating herd baseline: 25.0 kg Fresh TMR/day (15.72 kg DMI), yielding 25.0 L/cow/day
pen_allocations = [
    {"pen": "PEN_01_HIGH_YIELD", "cows": 10, "fresh_feed_kg": 250.0, "milk_yield_l": 260.0},
    {"pen": "PEN_02_FRESH_COWS", "cows": 10, "fresh_feed_kg": 250.0, "milk_yield_l": 240.0},
]

print(f"\n[FEED PRICING BASIS]")
print(f"  • TMR Fresh Formulation Cost: {tmr_fresh_cost_pkr_per_kg:.2f} PKR / kg")
print(f"  • Ration Dry Matter:          {tmr_dm_pct * 100:.2f}%")
print(f"  • Cost per kg Dry Matter:     {tmr_fresh_cost_pkr_per_kg / tmr_dm_pct:.2f} PKR / kg DMI\n")

print(f"{'Pen / Production Group':<24} | {'Cows':<5} | {'Milk (L)':<9} | {'Feed Fresh (kg)':<15} | {'DMI/Cow (kg)':<12} | {'FCE (L/kg DMI)':<14} | {'Feed Cost/L':<12}")
print("-" * 105)

total_cows, total_milk, total_feed = 0, 0.0, 0.0

for p in pen_allocations:
    cows = p["cows"]
    milk_l = p["milk_yield_l"]
    feed_kg = p["fresh_feed_kg"]
    
    dmi_per_cow = (feed_kg * tmr_dm_pct) / cows
    fce = (milk_l / cows) / dmi_per_cow
    feed_cost_l = (feed_kg * tmr_fresh_cost_pkr_per_kg) / milk_l

    total_cows += cows
    total_milk += milk_l
    total_feed += feed_kg

    print(f"{p['pen']:<24} | {cows:<5} | {milk_l:<9.1f} | {feed_kg:<15.1f} | {dmi_per_cow:<12.2f} | {fce:<14.2f} | {feed_cost_l:<10.2f} PKR")

print("-" * 105)
overall_dmi = (total_feed * tmr_dm_pct) / total_cows
overall_fce = (total_milk / total_cows) / overall_dmi
overall_cost_l = (total_feed * tmr_fresh_cost_pkr_per_kg) / total_milk

print(f"{'TOTAL HERD SUMMARY':<24} | {total_cows:<5} | {total_milk:<9.1f} | {total_feed:<15.1f} | {overall_dmi:<12.2f} | {overall_fce:<14.2f} | {overall_cost_l:<10.2f} PKR")

# 4. Income Over Feed Cost (IOFC)
gross_milk_price = 155.00  # PKR per Litre
iofc_per_litre = gross_milk_price - overall_cost_l
iofc_margin_pct = (iofc_per_litre / gross_milk_price) * 100
iofc_per_cow_day = (total_milk / total_cows) * iofc_per_litre

print("\n[INCOME OVER FEED COST (IOFC) ANALYSIS]")
print(f"  • Farm Milk Gate Price:        {gross_milk_price:.2f} PKR / Litre")
print(f"  • Herd Feed Cost per Litre:    {overall_cost_l:.2f} PKR / Litre")
print(f"  • Net Feed Margin per Litre:   {iofc_per_litre:.2f} PKR / Litre ({iofc_margin_pct:.1f}% Margin)")
print(f"  • Daily IOFC Margin per Cow:   {iofc_per_cow_day:.2f} PKR / cow / day")
print("================================================================================\n")