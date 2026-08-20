# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timezone

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. REGISTERING NEWBORN HEIFER CALF VIA /farm/animals ===")

calf_payload = {
    "animal_type": "CATTLE",
    "ear_tag": "PK-3X-121",
    "breed": "Holstein Friesian",
    "sex": "FEMALE",
    "lifecycle_status": "CALF",
    "dam_id": "TD-001",
    "sire_id": "HF-GENETICS-SEXED-STR-902",
    "date_of_birth": datetime.now(timezone.utc).date().isoformat(),
    "production_group": "CALF_HUTCHES_A"
}

r_calf = requests.post(f"{API_BASE_URL}/farm/animals", json=calf_payload, timeout=3)
print(f"Status [{r_calf.status_code}]:")
print(json.dumps(r_calf.json(), indent=2))

if r_calf.status_code == 200:
    new_animal = r_calf.json()
    new_id = new_animal.get("animal_id") or new_animal.get("id")
    print(f"\n[OK] Generated Animal ID: {new_id}")
    
    # 2. Log initial birth weight & colostrum intake
    print(f"\n=== 2. RECORDING BIRTH WEIGHT & COLOSTRUM INTAKE FOR {new_id} ===")
    growth_payload = {
        "weight_kg": 38.5,
        "wither_height_cm": 74.0,
        "notes": "Fed 4.0L first-milking colostrum (Brix 25%) within 2 hours of birth.",
        "operator": "HERD_SCOUT_01"
    }
    r_growth = requests.post(f"{API_BASE_URL}/farm/youngstock/{new_id}/growth", json=growth_payload, timeout=3)
    print(f"Youngstock Growth Status [{r_growth.status_code}]: {r_growth.text}")