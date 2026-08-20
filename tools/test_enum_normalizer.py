# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. TESTING INVENTORY MOVEMENT ALIAS ('in' -> 'RECEIPT') ===")
inv_payload = {
    "item": "Wheat Straw",
    "quantity": 2000.0,
    "unit": "kg",
    "movement_type": "in",
    "supplier": "LOCAL_SUPPLIER",
    "location": "BARN_C",
    "operator": "INVENTORY_MGR"
}
r_inv = requests.post(f"{API_BASE_URL}/farm/inventory", json=inv_payload, timeout=3)
print(f"Inventory Response [{r_inv.status_code}]: {r_inv.text[:90]}")

print("\n=== 2. TESTING HEALTH CASE SEVERITY ALIAS ('high' -> 'SEVERE') ===")
case_payload = {
    "animal_id": "TD-002",
    "diagnosis": "Mild Foot Rot Check",
    "severity": "high",
    "notes": "Testing alias middleware normalization.",
    "operator": "DR_ASIF_VET"
}
r_case = requests.post(f"{API_BASE_URL}/farm/health-cases", json=case_payload, timeout=3)
print(f"Health Case Response [{r_case.status_code}]: {r_case.text[:90]}")