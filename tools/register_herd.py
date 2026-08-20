import requests

API_BASE_URL = "http://127.0.0.1:8000"

print("--- Registering Foundation Herd with Governed Enums ---")

thrice_cows = []
twice_cows = []

# 10 Cows: 3x Daily Milking (THRICE_DAILY)
for i in range(1, 11):
    payload = {
        "ear_tag": f"PK-3X-{100 + i}",
        "animal_type": "CATTLE",
        "breed": "Holstein Friesian",
        "sex": "FEMALE",
        "lifecycle_status": "LACTATING",
        "is_currently_milking": True,
        "milking_frequency": "THRICE_DAILY",
        "production_group": "HIGH_YIELD_3X"
    }
    r = requests.post(f"{API_BASE_URL}/farm/animals", json=payload)
    if r.status_code in [200, 201]:
        data = r.json()
        animal_id = data.get("animal_id") or data.get("id")
        thrice_cows.append({"id": animal_id, "tag": payload["ear_tag"]})
        print(f"Registered Thrice-Daily Cow: Tag {payload['ear_tag']} -> System ID: {animal_id}")
    else:
        print(f"Failed Tag {payload['ear_tag']}: {r.status_code} - {r.text}")

# 10 Cows: 2x Daily Milking (TWICE_DAILY)
for i in range(1, 11):
    payload = {
        "ear_tag": f"PK-2X-{200 + i}",
        "animal_type": "CATTLE",
        "breed": "Holstein Friesian",
        "sex": "FEMALE",
        "lifecycle_status": "LACTATING",
        "is_currently_milking": True,
        "milking_frequency": "TWICE_DAILY",
        "production_group": "STANDARD_2X"
    }
    r = requests.post(f"{API_BASE_URL}/farm/animals", json=payload)
    if r.status_code in [200, 201]:
        data = r.json()
        animal_id = data.get("animal_id") or data.get("id")
        twice_cows.append({"id": animal_id, "tag": payload["ear_tag"]})
        print(f"Registered Twice-Daily Cow: Tag {payload['ear_tag']} -> System ID: {animal_id}")
    else:
        print(f"Failed Tag {payload['ear_tag']}: {r.status_code} - {r.text}")

print(f"\n>>> Total Successfully Registered: {len(thrice_cows) + len(twice_cows)} / 20 <<<")
