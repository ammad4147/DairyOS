# -*- coding: utf-8 -*-
import requests

API_BASE_URL = "http://127.0.0.1:8000"

print("=== EXECUTING REPRODUCTIVE LIFECYCLE SIMULATION (2026-08-21) ===")

# 1. Pregnancy Confirmation for TD-001 to TD-010 (Confirmed via Ultrasound)
print("\n[Phase 1/3] Logging Pregnancy Checks & Confirmations...")
for i in range(1, 11):
    cow_id = f"TD-{i:03d}"
    payload = {
        "animal_id": cow_id,
        "event_type": "PREGNANCY_CHECK",
        "result": "CONFIRMED_PREGNANT",
        "technician": "DR_ASIF_VET",
        "notes": "Ultrasound positive - viable fetus detected (~180d gestation)",
        "operator": "CHIEF_VET"
    }
    r = requests.post(f"{API_BASE_URL}/farm/breeding", json=payload, timeout=3)
    print(f" [{r.status_code}] {cow_id}: Confirmed Pregnant -> {r.text[:60]}")

# 2. Standing Heat Detection for TD-011 and TD-012
print("\n[Phase 2/3] Logging Standing Heat Observations...")
heat_cows = ["TD-011", "TD-012"]
for cow_id in heat_cows:
    payload = {
        "animal_id": cow_id,
        "event_type": "HEAT",
        "result": "STANDING_HEAT",
        "technician": "HERD_SCOUT_01",
        "notes": "Clear mucus discharge, standing to be mounted",
        "operator": "FARM_STAFF"
    }
    r = requests.post(f"{API_BASE_URL}/farm/breeding", json=payload, timeout=3)
    print(f" [{r.status_code}] {cow_id}: Standing Heat Logged -> {r.text[:60]}")

# 3. Timed Artificial Insemination (AI) for TD-011 and TD-012
print("\n[Phase 3/3] Logging AI Inseminations (Sexed Semen)...")
for cow_id in heat_cows:
    payload = {
        "animal_id": cow_id,
        "event_type": "INSEMINATION",
        "result": "INSEMINATED",
        "technician": "DR_ASIF_VET",
        "semen_or_bull": "HF-GENETICS-SEXED-STR-902",
        "notes": "AM/PM rule applied. Normal cervical deposition.",
        "operator": "CHIEF_VET"
    }
    r = requests.post(f"{API_BASE_URL}/farm/breeding", json=payload, timeout=3)
    print(f" [{r.status_code}] {cow_id}: AI Insemination Recorded -> {r.text[:60]}")

print("\n>>> REPRODUCTIVE EVENTS COMMITTED VIA GOVERNED REST API <<<")