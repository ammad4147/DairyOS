# -*- coding: utf-8 -*-
import requests
import json
from datetime import date

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" DAIRYOS FINANCIAL ENGINE: 7-DOMAIN COST OF PRODUCTION RECONCILIATION")
print("=" * 85)

# 1. Ingest missing cost domains to achieve 100% domain coverage
remaining_expenses = [
    {
        "transaction_type": "EXPENSE",
        "category": "BREEDING",
        "amount": 1800.0,
        "payment_method": "BANK_TRANSFER",
        "counterparty": "GENEX_GENETICS_PK",
        "notes": "Sexed Holstein semen straws + AI sheath consumables",
        "transaction_date": str(date.today()),
        "operator": "FINANCE_OFFICER_01"
    },
    {
        "transaction_type": "EXPENSE",
        "category": "EQUIPMENT",
        "amount": 1500.0,
        "payment_method": "BANK_TRANSFER",
        "counterparty": "DELAVAL_MAINTENANCE",
        "notes": "Milking claw liner replacements & vacuum pump service",
        "transaction_date": str(date.today()),
        "operator": "FINANCE_OFFICER_01"
    },
    {
        "transaction_type": "EXPENSE",
        "category": "OTHER_OPERATING",
        "amount": 850.0,
        "payment_method": "CASH",
        "counterparty": "LOCAL_SUPPLIES",
        "notes": "Teat dip disinfectant cups & parlor sanitation consumables",
        "transaction_date": str(date.today()),
        "operator": "FINANCE_OFFICER_01"
    }
]

print("\n[1] Ingesting Remaining Cost Domains...")
for exp in remaining_expenses:
    r = requests.post(f"{API_BASE}/farm/financial", json=exp, timeout=5)
    print(f"  • {exp['category']:<16} -> {exp['amount']:>8.2f} PKR [{r.status_code}]")

# 2. Query Full Cost-of-Production Endpoint
print("\n[2] Fetching Live Cost of Production (/farm/finance/cost-of-production)...")
r_cop = requests.get(f"{API_BASE}/farm/finance/cost-of-production", timeout=5)
cop_data = r_cop.json()

print(f"Status: {r_cop.status_code}")
print(json.dumps(cop_data, indent=2))

# 3. Query Financial General Ledger Reconciliation
print("\n[3] Fetching General Ledger Reconciliation (/farm/finance/reconciliation)...")
r_rec = requests.get(f"{API_BASE}/farm/finance/reconciliation", timeout=5)
rec_data = r_rec.json()

print(f"Status: {r_rec.status_code}")
print(json.dumps(rec_data, indent=2))

# 4. Computed Unit Economics Summary
total_exp = rec_data.get("expenses", 0.0)
total_inc = rec_data.get("income", 0.0)
saleable_litres = 237.0 # Delivered saleable volume from morning shift

unit_cost_l = total_exp / saleable_litres if saleable_litres else 0.0
revenue_l = total_inc / saleable_litres if saleable_litres else 0.0
margin_l = revenue_l - unit_cost_l

print("\n" + "=" * 85)
print(" EXECUTIVE UNIT ECONOMICS BREAKDOWN")
print("=" * 85)
print(f"  • Total Saleable Milk Volume:    {saleable_litres:.1f} Litres")
print(f"  • Total Farm Operating Revenue:  {total_inc:>10.2f} PKR ({revenue_l:.2f} PKR/L)")
print(f"  • Total Farm Operating Expenses: {total_exp:>10.2f} PKR ({unit_cost_l:.2f} PKR/L)")
print(f"  -------------------------------------------------------------------------------")
print(f"  • Net Farm Operating Margin:     {total_inc - total_exp:>10.2f} PKR ({margin_l:.2f} PKR/L)")
print("=" * 85)