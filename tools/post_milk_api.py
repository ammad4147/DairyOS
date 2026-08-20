import requests

API_BASE_URL = "http://127.0.0.1:8000"

print("--- Submitting Morning Milking Session via POST /farm/milk ---")

# 10 Thrice-Daily Cows (TD-001 to TD-010)
for i in range(1, 11):
    cow_id = f"TD-{i:03d}"
    morning_liters = round(13.5 + (10 - i) * 0.2, 2)
    payload = {
        "animal_id": cow_id,
        "session": "MORNING",
        "yield_litres": morning_liters,
        "recorded_by": "MILKER_MORNING_SHIFT",
        "operator": "MILKER_MORNING_SHIFT"
    }
    r = requests.post(f"{API_BASE_URL}/farm/milk", json=payload)
    print(f"[{r.status_code}] {cow_id}: {morning_liters} L -> {r.text[:60]}")

# 10 Twice-Daily Cows (TD-011 to TD-020)
for i in range(11, 21):
    cow_id = f"TD-{i:03d}"
    morning_liters = round(11.0 + (20 - i) * 0.15, 2)
    payload = {
        "animal_id": cow_id,
        "session": "MORNING",
        "yield_litres": morning_liters,
        "recorded_by": "MILKER_MORNING_SHIFT",
        "operator": "MILKER_MORNING_SHIFT"
    }
    r = requests.post(f"{API_BASE_URL}/farm/milk", json=payload)
    print(f"[{r.status_code}] {cow_id}: {morning_liters} L -> {r.text[:60]}")

print(">>> MORNING SESSIONS LOGGED VIA API <<<")
