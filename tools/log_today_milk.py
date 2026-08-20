import requests
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:8000"
today_str = "2026-08-21"

print(f"--- Logging Morning Milking Session for {today_str} ---")

# 10 Thrice-Daily Cows (TD-001 to TD-010): ~13.5 - 15.0 L morning shift
for i in range(1, 11):
    cow_id = f"TD-{i:03d}"
    morning_liters = round(13.5 + (10 - i) * 0.2, 2)
    payload = {
        "animal_id": cow_id,
        "morning_yield": morning_liters,
        "afternoon_yield": 0.0,
        "evening_yield": 0.0,
        "operator": "MILKER_MORNING_SHIFT",
        "date": today_str
    }
    try:
        r = requests.post(f"{API_BASE_URL}/farm/operational-events", json=payload, timeout=1)
        print(f"Logged Morning Milk for {cow_id}: {morning_liters} L (Status: {r.status_code})")
    except Exception as e:
        print(f"Error for {cow_id}: {e}")

# 10 Twice-Daily Cows (TD-011 to TD-020): ~11.0 - 12.5 L morning shift
for i in range(11, 21):
    cow_id = f"TD-{i:03d}"
    morning_liters = round(11.0 + (20 - i) * 0.15, 2)
    payload = {
        "animal_id": cow_id,
        "morning_yield": morning_liters,
        "afternoon_yield": 0.0,
        "evening_yield": 0.0,
        "operator": "MILKER_MORNING_SHIFT",
        "date": today_str
    }
    try:
        r = requests.post(f"{API_BASE_URL}/farm/operational-events", json=payload, timeout=1)
        print(f"Logged Morning Milk for {cow_id}: {morning_liters} L (Status: {r.status_code})")
    except Exception as e:
        print(f"Error for {cow_id}: {e}")

print(">>> TODAY'S MORNING MILK SESSION LOGGED <<<")
