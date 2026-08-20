from dairyos.data.database.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 1. Total Animals
    animal_res = conn.execute(text("SELECT count(*), lifecycle_status FROM animals GROUP BY lifecycle_status;")).fetchall()
    print("--- ANIMALS IN DATABASE ---")
    total_animals = 0
    for count, status in animal_res:
        print(f"Status: {status:<15} | Count: {count}")
        total_animals += count
    print(f"Total Animals: {total_animals}")

    # 2. Total Operational Events (Milking records)
    event_count = conn.execute(text("SELECT count(*) FROM operational_events;")).scalar()
    print(f"\n--- OPERATIONAL / MILK EVENTS ---")
    print(f"Total Milk Records: {event_count}")

    # 3. Total Breeding Records
    breeding_count = conn.execute(text("SELECT count(*) FROM breeding_records;")).scalar()
    print(f"Total Breeding Records: {breeding_count}")

    # 4. Check for any leftover old mock animals (e.g. non-TD tags)
    legacy_check = conn.execute(text("SELECT count(*) FROM animals WHERE ear_tag NOT LIKE 'PK-%';")).scalar()
    print(f"\n--- CLEANLINESS CHECK ---")
    print(f"Old / Unrecognized Animals: {legacy_check}")
