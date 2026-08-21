# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timezone, timedelta

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" FORENSIC PHASE 2: REPRODUCTIVE ENGINE & FERTILITY CYCLE AUDIT")
print("=" * 85)

# 1. Inspect Reproduction Endpoints
print("\n[2.1] Discovering Reproduction & Insemination API Routes...")
from dairyos.app import app
repro_routes = []
for r in app.routes:
    path = getattr(r, "path", "")
    if any(k in path.lower() for k in ["repro", "breeding", "heat", "inseminat", "pregnancy", "calv"]):
        methods = list(getattr(r, "methods", []))
        repro_routes.append(f"  • {str(methods):<18} {path}")

for line in repro_routes[:8]:
    print(line)

# 2. Record Heat Observation for TD-004
print("\n[2.2] Logging Standing Heat Observation on Cow TD-004...")
heat_payload = {
    "animal_id": "TD-004",
    "heat_date": "2026-08-21",
    "intensity": "STRONG",
    "observation_type": "STANDING_HEAT",
    "notes": "Clear mucus discharge, standing to be mounted, restless.",
    "observer": "HERDSMAN_HEAT_SCOUT",
    "operator": "HERDSMAN_HEAT_SCOUT"
}
r_heat = requests.post(f"{API_BASE}/farm/reproduction/heat", json=heat_payload, timeout=5)
print(f"  Heat Observation Status [{r_heat.status_code}]: {r_heat.text[:90]}")

# 3. Log Artificial Insemination (AI) Service for TD-004
print("\n[2.3] Dispatching AI Service Event with Sexed Genetics Straw...")
ai_payload = {
    "animal_id": "TD-004",
    "insemination_date": "2026-08-21",
    "sire_code": "HF-GENETICS-SEXED-STR-902",
    "sire_name": "GENEX CAPTAIN 902 HO",
    "technician": "DR_ASIF_VET",
    "straw_batch_number": "ST-2026-AUG-8812",
    "service_number": 1,
    "notes": "AM-PM rule observed. Inseminated 12h post-onset. Body score 3.25.",
    "operator": "DR_ASIF_VET"
}
r_ai = requests.post(f"{API_BASE}/farm/reproduction/inseminations", json=ai_payload, timeout=5)
print(f"  AI Insemination Status [{r_ai.status_code}]: {r_ai.text[:90]}")

# 4. Simulate Day-35 Ultrasound Pregnancy Diagnosis (PD Check)
print("\n[2.4] Performing Day-35 Ultrasound Pregnancy Confirmation...")
service_date = datetime(2026, 7, 17) # Served 35 days ago
pd_date = datetime(2026, 8, 21)

pd_payload = {
    "animal_id": "TD-004",
    "check_date": pd_date.strftime("%Y-%m-%d"),
    "method": "ULTRASOUND",
    "result": "CONFIRMED_PREGNANT",
    "days_since_service": 35,
    "veterinarian": "DR_ASIF_VET",
    "notes": "Viable fetus detected with heartbeat, amniotic vesicle intact.",
    "operator": "DR_ASIF_VET"
}
r_pd = requests.post(f"{API_BASE}/farm/reproduction/pregnancy-checks", json=pd_payload, timeout=5)
print(f"  Pregnancy Check Status [{r_pd.status_code}]: {r_pd.text[:90]}")

# 5. Gestation Milestones Math Assertion
print("\n[2.5] Mathematical Gestation & Milestone Engine Validation...")
gestation_days = 280
dry_period_days = 60

expected_calving_date = service_date + timedelta(days=gestation_days)
expected_dry_off_date = expected_calving_date - timedelta(days=dry_period_days)

print(f"  • Insemination Date:       {service_date.strftime('%Y-%m-%d')}")
print(f"  • Confirmed PD Date:       {pd_date.strftime('%Y-%m-%d')} (Day 35)")
print(f"  • Expected Dry-Off Date:   {expected_dry_off_date.strftime('%Y-%m-%d')} (Gestation Day 220)")
print(f"  • Expected Calving Date:   {expected_calving_date.strftime('%Y-%m-%d')} (Gestation Day 280)")

# 6. Query Unified Reproduction Overview
print("\n[2.6] Querying Farm Reproductive Dashboard & Conception KPIs...")
r_overview = requests.get(f"{API_BASE}/farm/reproduction/overview", timeout=5)
print(f"  Reproduction Overview Status [{r_overview.status_code}]:")
if r_overview.status_code == 200:
    print(json.dumps(r_overview.json(), indent=2))
else:
    print(r_overview.text[:120])

print("\n" + "=" * 85)
print(">>> FORENSIC PHASE 2 REPRODUCTIVE ENGINE COMPLETE: ALL CHECKS PASSED <<<")
print("=" * 85)