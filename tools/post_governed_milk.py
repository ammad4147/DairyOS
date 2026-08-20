import requests

API_BASE_URL = "http://127.0.0.1:8000"
today_str = "2026-08-21"

print(f"--- Submitting Governed Morning Milk Session for {today_str} ---")

success_count = 0
total_liters = 0.0

# 10 Thrice-Daily Animals (TD-001 to TD-010)
for i in range(1, 11):
    cow_id = f"TD-{i:03d}"
    morning_liters = round(13.5 + (10 - i) * 0.2, 2)
    payload = {
        "animal_id": cow_id,
        "morning_yield": morning_liters,
        "milking_session": "MORNING",
        "production_date": today_str,
        "operator": "MILKER_MORNING_SHIFT"
    }
    r = requests.post(f"{API_BASE_URL}/farm/milk", json=payload)
    if r.status_code in [200, 201]:
        success_count += 1
        total_liters += morning_liters
        print(f"[OK 200] {cow_id}: Logged {morning_liters} L")
    else:
        print(f"[{r.status_code}] {cow_id}: Failed -> {r.text}")

# 10 Twice-Daily Animals (TD-011 to TD-020)
for i in range(11, 21):
    cow_id = f"TD-{i:03d}"
    morning_liters = round(11.0 + (20 - i) * 0.15, 2)
    payload = {
        "animal_id": cow_id,
        "morning_yield": morning_liters,
        "milking_session": "MORNING",
        "production_date": today_str,
        "operator": "MILKER_MORNING_SHIFT"
    }
    r = requests.post(f"{API_BASE_URL}/farm/milk", json=payload)
    if r.status_code in [200, 201]:
        success_count += 1
        total_liters += morning_liters
        print(f"[OK 200] {cow_id}: Logged {morning_liters} L")
    else:
        print(f"[{r.status_code}] {cow_id}: Failed -> {r.text}")

avg_liters = round(total_liters / max(success_count, 1), 2)
print(f"\n>>> COMPLETED: {success_count}/20 cows recorded | Total Morning Milk: {total_liters:.2f} L (Avg: {avg_liters} L/cow) <<<")
