# -*- coding: utf-8 -*-
import requests
import json
from datetime import date
from dairyos.app import app

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" FORENSIC PHASE 6: FINANCIAL ENGINE & COST RECONCILIATION AUDIT")
print("=" * 85)

# Locate the exact POST finance endpoint
target_route = None
for r in app.routes:
    p = getattr(r, "path", "")
    if "POST" in getattr(r, "methods", []) and ("finan" in p or "transaction" in p):
        target_route = p
        break

if not target_route:
    target_route = "/farm/financial"

print(f"Using Ingestion Endpoint: {target_route}")

# 1. Post Milk Revenue
print("\n[6.1] Recording Milk Sales Revenue (237.0 L @ 155.00 PKR/L = 36,735.00 PKR)...")
rev_payload = {
    "transaction_type": "INCOME",
    "amount": 36735.0,
    "category": "MILK_SALES",
    "payment_method": "BANK_TRANSFER",
    "counterparty": "ENGRO_FOODS_DAIRY",
    "notes": "Morning saleable milk shipment (237L @ 155 PKR/L)",
    "transaction_date": str(date.today()),
    "operator": "FINANCE_OFFICER_01"
}
r_rev = requests.post(f"{API_BASE}{target_route}", json=rev_payload, timeout=5)
print(f"  Revenue Status [{r_rev.status_code}]: {r_rev.text[:100]}")

# 2. Post Operating Expenses
print("\n[6.2] Recording Operating Expense Ledger Entries...")
expenses = [
    {"category": "FEED", "amount": 15000.0, "counterparty": "PUNJAB_SILAGE_CORP", "notes": "Morning fresh TMR feed allocation"},
    {"category": "LABOUR", "amount": 4000.0, "counterparty": "FARMWORKER_PAYROLL", "notes": "Shift labor wages (Milkers & Feeders)"},
    {"category": "HEALTH", "amount": 2500.0, "counterparty": "VET_CLINIC_SERVICES", "notes": "Clinical exam & Oxytetracycline treatment"},
    {"category": "UTILITIES", "amount": 2200.0, "counterparty": "ELECTRICITY_WAPDA", "notes": "Chiller and parlor power consumption"}
]

for exp in expenses:
    payload = {
        "transaction_type": "EXPENSE",
        "amount": exp["amount"],
        "category": exp["category"],
        "payment_method": "BANK_TRANSFER",
        "counterparty": exp["counterparty"],
        "notes": exp["notes"],
        "transaction_date": str(date.today()),
        "operator": "FINANCE_OFFICER_01"
    }
    r_exp = requests.post(f"{API_BASE}{target_route}", json=payload, timeout=5)
    print(f"  Expense [{r_exp.status_code}]: {exp['category']} -> {exp['amount']:.2f} PKR")

# 3. Query Live Cost of Production Engine
print("\n[6.3] Fetching Live Cost of Production Breakdown...")
r_cop = requests.get(f"{API_BASE}/farm/finance/cost-of-production", timeout=5)
print(f"  Cost of Production Status [{r_cop.status_code}]:")
if r_cop.status_code == 200:
    print(json.dumps(r_cop.json(), indent=2))

# 4. Query General Ledger Reconciliation
print("\n[6.4] Fetching Live General Ledger Reconciliation...")
r_rec = requests.get(f"{API_BASE}/farm/finance/reconciliation", timeout=5)
print(f"  Reconciliation Status [{r_rec.status_code}]:")
if r_rec.status_code == 200:
    print(json.dumps(r_rec.json(), indent=2))

print("\n" + "=" * 85)
print(">>> FORENSIC PHASE 6 AUDIT COMPLETE <<<")
print("=" * 85)