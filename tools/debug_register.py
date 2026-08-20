import requests

API_BASE_URL = "http://127.0.0.1:8000"

payload = {
    "animal_id": "COW-3X-01",
    "ear_tag": "PK-3X-101",
    "animal_type": "COW",
    "breed": "Holstein Friesian",
    "sex": "FEMALE",
    "lifecycle_status": "LACTATING",
    "status": "ACTIVE",
    "is_currently_milking": True,
    "milking_frequency": "3X",
    "production_group": "HIGH_YIELD_3X"
}

r = requests.post(f"{API_BASE_URL}/farm/animals", json=payload)
print(f"Status Code: {r.status_code}")
print(f"Response Body: {r.text}")

# Also fetch governed reference data to see valid values
r_ref = requests.get(f"{API_BASE_URL}/farm/reference-data")
if r_ref.status_code == 200:
    print(f"\nGoverned Reference Data:\n{r_ref.json()}")
