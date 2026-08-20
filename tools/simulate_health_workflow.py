# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta, timezone

API_BASE_URL = "http://127.0.0.1:8000"

print("=== EXECUTING CLINICAL HEALTH & WITHHOLDING SIMULATION ===")

# 1. Post Health Observation
print("\n[Step 1/3] Submitting Health Observation for TD-015...")
obs_payload = {
    "animal_id": "TD-015",
    "observation": "Left hind quarter swollen, hard, and painful to touch. Foremilk shows yellow flakes.",
    "symptom": "MASTITIS_CLINICAL",
    "temperature_c": 39.6,
    "severity": "HIGH",
    "operator": "HERD_SCOUT_01"
}
r_obs = requests.post(f"{API_BASE_URL}/farm/health-observations", json=obs_payload, timeout=3)
print(f"Observation Response [{r_obs.status_code}]: {r_obs.text}")

# 2. Open Clinical Case
print("\n[Step 2/3] Opening Clinical Case for TD-015...")
case_payload = {
    "animal_id": "TD-015",
    "diagnosis": "Grade 2 Clinical Mastitis (Left Hind Quarter)",
    "severity": "HIGH",
    "notes": "Intramammary infection confirmed. Prescribed 3-day antibiotic course + NSAID.",
    "follow_up_due_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
    "operator": "DR_ASIF_VET"
}
r_case = requests.post(f"{API_BASE_URL}/farm/health-cases", json=case_payload, timeout=3)
print(f"Case Response [{r_case.status_code}]: {r_case.text}")

case_data = r_case.json() if r_case.status_code == 200 else {}
case_id = case_data.get("id") or case_data.get("case_id")

# 3. Log Treatment with 4-Day Milk Withholding
print("\n[Step 3/3] Recording Antibiotic Treatment & 4-Day Milk Withholding Directive...")
treat_payload = {
    "animal_id": "TD-015",
    "medicine": "Cobactan LC (Cefquinome 75mg) + Finadyne",
    "diagnosis": "Grade 2 Clinical Mastitis",
    "dose": "1 intramammary syringe Q24H x 3 days + 15ml IV NSAID",
    "treated_by": "DR_ASIF_VET",
    "milk_withdrawal_days": 4.0,
    "notes": "Strict withholding directive: Milk must NOT enter bulk tank until 96h post-infusion.",
    "health_case_id": case_id if isinstance(case_id, int) else None,
    "operator": "DR_ASIF_VET"
}
r_treat = requests.post(f"{API_BASE_URL}/farm/treatments", json=treat_payload, timeout=3)
print(f"Treatment Response [{r_treat.status_code}]: {r_treat.text}")

print("\n>>> CLINICAL CASE & WITHHOLDING DIRECTIVE COMMITTED <<<")