# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timezone

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. RECORDING CALVING EVENT ON DAM (TD-001) ===")
calving_payload = {
    "animal_id": "TD-001",
    "event_type": "CALVING",
    "result": "LIVE_HEIFER",
    "technician": "HERD_SCOUT_01",
    "notes": "Unassisted natural calving. Delivered healthy female calf TD-021. Dam vigorous.",
    "operator": "DR_ASIF_VET"
}
r_calv = requests.post(f"{API_BASE_URL}/farm/breeding", json=calving_payload, timeout=3)
print(f"Calving Record [{r_calv.status_code}]: {r_calv.text[:80]}")

print("\n=== 2. REGISTERING NEWBORN CALF (TD-021) WITH PEDIGREE ===")
calf_payload = {
    "animal_id": "TD-021",
    "animal_type": "HEIFER_CALF",
    "status": "ACTIVE",
    "dam_id": "TD-001",
    "sire_id": "HF-GENETICS-SEXED-STR-902",
    "birth_date": datetime.now(timezone.utc).date().isoformat(),
    "gender": "FEMALE",
    "breed": "HOLSTEIN_FRIESIAN",
    "birth_weight_kg": 38.5,
    "group_or_pen": "CALF_HUTCHES_A",
    "operator": "DR_ASIF_VET"
}

r_calf = requests.post(f"{API_BASE_URL}/farm/animals", json=calf_payload, timeout=3)
print(f"Calf Registration [/farm/animals] [{r_calf.status_code}]: {r_calf.text[:80]}")

print("\n=== 3. LOGGING INITIAL BIRTH WEIGHT & COLOSTRUM INTAKE ===")
growth_payload = {
    "weight_kg": 38.5,
    "wither_height_cm": 74.0,
    "notes": "Fed 4.0L first-milking colostrum (Brix 25%) within 2 hours of birth.",
    "operator": "HERD_SCOUT_01"
}
r_growth = requests.post(f"{API_BASE_URL}/farm/youngstock/TD-021/growth", json=growth_payload, timeout=3)
print(f"Youngstock Growth Tracker [{r_growth.status_code}]: {r_growth.text[:80]}")

print("\n>>> NEWBORN PEDIGREE & ANIMAL RECORD REGISTERED <<<")