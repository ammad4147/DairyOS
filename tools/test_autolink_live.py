# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. OPENING NEW HEALTH CASE ON TD-003 ===")
case_payload = {
    "animal_id": "TD-003",
    "diagnosis": "Subclinical Ketosis",
    "severity": "MODERATE",
    "notes": "Elevated BHB levels detected on fresh check.",
    "operator": "DR_ASIF_VET"
}
r_case = requests.post(f"{API_BASE_URL}/farm/health-cases", json=case_payload, timeout=3)
case_data = r_case.json()
case_id = case_data.get("id")
print(f"Created Case: ID={case_id}, Code={case_data.get('case_id')}")

print("\n=== 2. LOGGING TREATMENT WITHOUT EXPLICIT health_case_id ===")
treat_payload = {
    "animal_id": "TD-003",
    "medicine": "Propylene Glycol Drench",
    "dose": "300ml PO Q24H x 3 days",
    "treated_by": "DR_ASIF_VET",
    "milk_withdrawal_days": 0.0,
    "notes": "Energy precursor oral drench.",
    "operator": "DR_ASIF_VET"
}
r_treat = requests.post(f"{API_BASE_URL}/farm/treatments", json=treat_payload, timeout=3)
treat_data = r_treat.json()
print(f"Treatment Response: Status [{r_treat.status_code}]")
print(json.dumps(treat_data, indent=2))

print("\n=== 3. VERIFYING TREATMENT LINKED TO CASE ===")
linked_case_id = treat_data.get("health_case_id")
print(f"Assigned health_case_id: {linked_case_id} (Expected: {case_id})")
assert linked_case_id == case_id, f"Auto-linking failed: expected {case_id}, got {linked_case_id}"
print("[PASS] Treatment was automatically linked to the active health case!")