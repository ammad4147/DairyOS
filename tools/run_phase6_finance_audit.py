# -*- coding: utf-8 -*-
import requests
import json
from datetime import date

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" FORENSIC PHASE 6: FINANCIAL ENGINE & COST RECONCILIATION AUDIT")
print("=" * 85)

# 1. Ingest Milk Sales Operating Revenue
print("\n[6.1] Ingesting Milk Sales Revenue (237L @ 155 PKR/L)...")
milk_sale_payload = {
    "transaction_type": "INCOME",
    "amount": 36735.0,
    "category": "MILK_SALES",
    "payment_method": "BANK_TRANSFER",
    "counterparty": "ENGRO_FOODS_DAIRY",
    "notes": "Morning shift saleable milk delivery: 237.0 L @ 155 PKR/L",
    "transaction_date": str(date.today()),
    "operator": "FINANCE_OFFICER_01"
}
r_rev = requests.post(f"{API_BASE}/farm/finance", json=milk_sale_payload, timeout=5)
print(f"  Revenue Ingestion [{r_rev.status_code}]: {r_rev.text[:90]}")

# 2. Ingest Operational Operating Expenses
print("\n[6.2] Ingesting Operational Expense Ledger Entries...")
expenses = [
    {"category": "LABOUR", "amount": 12000.0, "counterparty": "FARMWORKER_PAYROLL", "notes": "Shift labor wages (Milkers & Feeders)"},
    {"category": "HEALTH", "amount": 4500.0, "counterparty": "VET_CLINIC_SERVICES", "notes": "Vet visit and clinical treatment supplies"},
    {"category": "UTILITIES", "amount": 6200.0, "counterparty": "ELECTRICITY_WAPDA", "notes": "Chilling tank and milking machine power"}
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
    r = requests.post(f"{API_BASE}/farm/finance", json=payload, timeout=5)
    print(f"  Expense Ingestion [{r.status_code}]: {exp['category']} -> {exp['amount']:.2f} PKR")

# 3. Query Unit Economics & Cost of Production Engine
print("\n[6.3] Fetching Cost of Production Breakdown (/farm/finance/cost-of-production)...")
r_cop = requests.get(f"{API_BASE}/farm/finance/cost-of-production", timeout=5)
print(f"  Cost of Production Status [{r_cop.status_code}]:")
if r_cop.status_code == 200:
    print(json.dumps(r_cop.json(), indent=2))
else:
    print(r_cop.text[:120])

# 4. Query Financial Ledger Reconciliation
print("\n[6.4] Fetching Financial Ledger Reconciliation (/farm/finance/reconciliation)...")
r_rec = requests.get(f"{API_BASE}/farm/finance/reconciliation", timeout=5)
print(f"  Reconciliation Status [{r_rec.status_code}]:")
if r_rec.status_code == 200:
    print(json.dumps(r_rec.json(), indent=2))
else:
    print(r_rec.text[:120])

print("\n" + "=" * 85)
print(">>> FORENSIC PHASE 6 FINANCIAL ENGINE COMPLETE <<<")
print("=" * 85)