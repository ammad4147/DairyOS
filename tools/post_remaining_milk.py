import requests

API_BASE_URL = "http://127.0.0.1:8000"
today_str = "2026-08-21"

print(f"--- Submitting Afternoon & Evening Milking Sessions for {today_str} ---")

# 1. Afternoon Milking for Thrice-Daily (TD-001 to TD-010)
print("\n[1/2] Logging AFTERNOON Session for 3x Milking Group...")
for i in range(1, 11):
    cow_id = f"TD-{i:03d}"
    afternoon_liters = round(11.0 + (10 - i) * 0.15, 2)
    payload = {
        "animal_id": cow_id,
        "morning_yield": None,
        "afternoon_yield": afternoon_liters,
        "evening_yield": None,
        "milking_session": "AFTERNOON",
        "production_date": today_str,
        "operator": "MILKER_AFTERNOON_SHIFT"
    }
    r = requests.post(f"{API_BASE_URL}/farm/milk", json=payload)
    print(f"[{r.status_code}] {cow_id}: Afternoon {afternoon_liters} L")

# 2. Evening Milking for ALL 20 Cows
print("\n[2/2] Logging EVENING Session for Entire Milking Herd...")
for i in range(1, 11):
    cow_id = f"TD-{i:03d}"
    evening_liters = round(10.0 + (10 - i) * 0.15, 2)
    payload = {
        "animal_id": cow_id,
        "morning_yield": None,
        "afternoon_yield": None,
        "evening_yield": evening_liters,
        "milking_session": "EVENING",
        "production_date": today_str,
        "operator": "MILKER_EVENING_SHIFT"
    }
    r = requests.post(f"{API_BASE_URL}/farm/milk", json=payload)
    print(f"[{r.status_code}] {cow_id} (3x Group): Evening {evening_liters} L")

for i in range(11, 21):
    cow_id = f"TD-{i:03d}"
    evening_liters = round(10.5 + (20 - i) * 0.1, 2)
    payload = {
        "animal_id": cow_id,
        "morning_yield": None,
        "afternoon_yield": None,
        "evening_yield": evening_liters,
        "milking_session": "EVENING",
        "production_date": today_str,
        "operator": "MILKER_EVENING_SHIFT"
    }
    r = requests.post(f"{API_BASE_URL}/farm/milk", json=payload)
    print(f"[{r.status_code}] {cow_id} (2x Group): Evening {evening_liters} L")

print("\n>>> FULL DAY MILKING SESSIONS SUCCESSFULLY RECORDED <<<")
