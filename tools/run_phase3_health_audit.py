# -*- coding: utf-8 -*-
import requests
import json

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" FORENSIC PHASE 3: CLINICAL HEALTH & DRUG WITHHOLDING AUDIT")
print("=" * 85)

# 1. Open Clinical Health Case on TD-003
print("\n[3.1] Opening Clinical Health Case (Subclinical Ketosis) on TD-003...")
case_payload = {
    "animal_id": "TD-003",
    "diagnosis": "Subclinical Ketosis",
    "severity": "MODERATE",
    "notes": "BHB meter reading 1.4 mmol/L on fresh check.",
    "operator": "DR_ASIF_VET"
}
r_case = requests.post(f"{API_BASE}/farm/health-cases", json=case_payload, timeout=5)
case_data = r_case.json()
case_id = case_data.get("id")
print(f"  Health Case Created [{r_case.status_code}]: ID={case_id}, Code={case_data.get('case_id')}")

# 2. Record Treatment with Antibiotic / Medication Withholding
print("\n[3.2] Logging Treatment Record with Milk Withholding Period...")
treat_payload = {
    "animal_id": "TD-003",
    "health_case_id": case_id,
    "medicine": "Oxytetracycline LA",
    "dose": "20ml IM single injection",
    "treated_by": "DR_ASIF_VET",
    "milk_withdrawal_days": 4.0,
    "notes": "Broad-spectrum coverage for secondary post-calving infection.",
    "operator": "DR_ASIF_VET"
}
r_treat = requests.post(f"{API_BASE}/farm/treatments", json=treat_payload, timeout=5)
treat_data = r_treat.json()
print(f"  Treatment Logged [{r_treat.status_code}]:")
print(json.dumps(treat_data, indent=2))

# 3. Verify Health Case Withdrawal Propagation
print("\n[3.3] Verifying Health Case Withdrawal Sync...")
r_get_case = requests.get(f"{API_BASE}/farm/health-cases/{case_id}", timeout=5)
case_detail = r_get_case.json()
print(f"  Health Case #{case_id} Status:")
print(f"    • Diagnosis:         {case_detail.get('diagnosis')}")
print(f"    • Status:            {case_detail.get('status')}")
print(f"    • Withdrawal Until:  {case_detail.get('withdrawal_until')}")
print(f"    • Linked Treatments: {len(case_detail.get('treatments', []))}")

# 4. Verify Milking Withholding Interceptor Flag
print("\n[3.4] Testing Milking Shift Withholding Interceptor for TD-003...")
milk_payload = {
    "animal_id": "TD-003",
    "shift": "MORNING",
    "yield_litres": 14.5,
    "is_valid": True,
    "operator": "MILKER_LEADER"
}
r_milk = requests.post(f"{API_BASE}/farm/milk", json=milk_payload, timeout=5)
print(f"  Milk Submission Under Withdrawal [{r_milk.status_code}]:")
print(json.dumps(r_milk.json(), indent=2))

print("\n" + "=" * 85)
print(">>> FORENSIC PHASE 3 CLINICAL HEALTH & WITHHOLDING AUDIT COMPLETE <<<")
print("=" * 85)