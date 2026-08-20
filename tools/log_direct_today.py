from datetime import datetime
from dairyos.data.database.session import engine
from sqlalchemy import text

today_date = datetime(2026, 8, 21).date()
print(f"--- Direct Ingestion: Morning Milk Session for {today_date} ---")

records = []

# 10 Thrice-Daily Cows (TD-001 to TD-010)
for i in range(1, 11):
    cow_id = f"TD-{i:03d}"
    morning_liters = round(13.5 + (10 - i) * 0.2, 2)
    records.append({
        "animal_id": cow_id,
        "production_date": today_date,
        "morning_yield": morning_liters,
        "afternoon_yield": 0.0,
        "evening_yield": 0.0,
        "total_yield": morning_liters,
        "status": "CONFIRMED"
    })

# 10 Twice-Daily Cows (TD-011 to TD-020)
for i in range(11, 21):
    cow_id = f"TD-{i:03d}"
    morning_liters = round(11.0 + (20 - i) * 0.15, 2)
    records.append({
        "animal_id": cow_id,
        "production_date": today_date,
        "morning_yield": morning_liters,
        "afternoon_yield": 0.0,
        "evening_yield": 0.0,
        "total_yield": morning_liters,
        "status": "CONFIRMED"
    })

with engine.connect() as conn:
    # Delete any existing record for today if re-running
    conn.execute(text("DELETE FROM milk_production WHERE production_date = :d"), {"d": today_date})
    
    conn.execute(
        text("""
            INSERT INTO milk_production (animal_id, production_date, morning_yield, afternoon_yield, evening_yield, total_yield, status)
            VALUES (:animal_id, :production_date, :morning_yield, :afternoon_yield, :evening_yield, :total_yield, :status)
        """),
        records
    )
    conn.commit()

total_morning = sum(r["morning_yield"] for r in records)
avg_morning = round(total_morning / len(records), 2)
print(f">>> Logged {len(records)} entries. Total Farm Milk Today: {total_morning} L (Avg: {avg_morning} L/cow) <<<")
