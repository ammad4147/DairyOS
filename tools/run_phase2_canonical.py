# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timezone, timedelta

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" FORENSIC PHASE 2: CANONICAL REPRODUCTIVE ENGINE & FERTILITY AUDIT")
print("=" * 85)

# 1. Log Heat Observation on TD-004
print("\n[2.1] Logging Standing Heat Observation on TD-004...")
heat_payload = {
    "animal_id": "TD-004",
    "event_type": "HEAT",
    "event_date": "2026-08-21",
    "notes": "Standing heat, clear discharge, restlessness.",
    "operator": "HERDSMAN_HEAT_SCOUT"
}
r_heat = requests.post(f"{API_BASE}/farm/breeding", json=heat_payload, timeout=5)
print(f"  Heat Status [{r_heat.status_code}]: {r_heat.text[:100]}")

# 2. Log Artificial Insemination (AI) on TD-004
print("\n[2.2] Logging Artificial Insemination on TD-004...")
ai_payload = {
    "animal_id": "TD-004",
    "event_type": "INSEMINATION",
    "event_date": "2026-08-21",
    "sire_id": "HF-GENETICS-SEXED-STR-902",
    "technician": "DR_ASIF_VET",
    "notes": "Straw ST-8812, sexed female semen.",
    "operator": "DR_ASIF_VET"
}
r_ai = requests.post(f"{API_BASE}/farm/breeding", json=ai_payload, timeout=5)
print(f"  Insemination Status [{r_ai.status_code}]: {r_ai.text[:100]}")

# 3. Log Insemination on TD-005 (35 days prior) + Day-35 Positive Pregnancy Check
print("\n[2.3] Logging AI + Confirmed Ultrasound Pregnancy on TD-005...")
ai_prev = {
    "animal_id": "TD-005",
    "event_type": "INSEMINATION",
    "event_date": "2026-07-17",
    "sire_id": "HF-GENETICS-SEXED-STR-902",
    "technician": "DR_ASIF_VET",
    "notes": "Straw ST-8740.",
    "operator": "DR_ASIF_VET"
}
requests.post(f"{API_BASE}/farm/breeding", json=ai_prev, timeout=5)

pd_payload = {
    "animal_id": "TD-005",
    "event_type": "PREGNANCY_CHECK",
    "event_date": "2026-08-21",
    "result": "PREGNANT",
    "notes": "Ultrasound positive, viable fetus heartbeat detected.",
    "operator": "DR_ASIF_VET"
}
r_pd = requests.post(f"{API_BASE}/farm/breeding", json=pd_payload, timeout=5)
print(f"  Pregnancy Check Status [{r_pd.status_code}]: {r_pd.text[:100]}")

# 4. Verify Reproduction Overview & Conception KPIs
print("\n[2.4] Fetching Live Reproductive Overview & Conception Rate...")
r_overview = requests.get(f"{API_BASE}/farm/reproduction/overview", timeout=5)
print(f"  Overview Status [{r_overview.status_code}]:")
if r_overview.status_code == 200:
    print(json.dumps(r_overview.json(), indent=2))

# 5. Verify Animal-Specific Reproduction Passport for TD-005
print("\n[2.5] Querying TD-005 Reproductive Passport...")
r_passport = requests.get(f"{API_BASE}/farm/animals/TD-005/reproduction", timeout=5)
print(f"  Passport Status [{r_passport.status_code}]:")
if r_passport.status_code == 200:
    print(json.dumps(r_passport.json(), indent=2))

print("\n" + "=" * 85)
print(">>> FORENSIC PHASE 2 REPRODUCTIVE ENGINE COMPLETE <<<")
print("=" * 85)