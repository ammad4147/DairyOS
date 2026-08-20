import math
import random
from datetime import datetime, timedelta
from dairyos.data.database.session import engine
from sqlalchemy import text

print("=== STARTING 5-YEAR DATA POPULATION ===")

start_date = datetime(2026, 1, 1)
total_days = 1825  # 5 Years

# Load registered foundation animals from DB
with engine.connect() as conn:
    animals = conn.execute(text("SELECT animal_id, ear_tag, milking_frequency FROM animal WHERE status = 'ACTIVE';")).fetchall()

print(f"Loaded {len(animals)} active foundation animals from database.")

milk_records = []
health_records = []
breeding_records = []
finance_records = []

# State tracking per animal
animal_state = {}
for a_id, tag, freq in animals:
    animal_state[a_id] = {
        "tag": tag,
        "freq": freq,
        "dim": random.randint(20, 60),
        "parity": random.choice([1, 2, 3]),
        "status": "LACTATING",
        "conception_day": None,
        "withholding": 0
    }

next_case_id = 1
next_tx_id = 1
anomalies_count = 0
credit_sales_liters = 0.0

for day in range(1, total_days + 1):
    sim_date = start_date + timedelta(days=day-1)
    date_str = sim_date.strftime("%Y-%m-%d")
    daily_bulk_milk = 0.0

    # 1. Milk Production & Yield
    for a_id, st in animal_state.items():
        if st["status"] == "LACTATING":
            st["dim"] += 1
            t = st["dim"]
            # Wood's curve
            base_yield = 18.0 * (math.pow(t, 0.22)) * math.exp(-0.0035 * t)
            freq_multiplier = 1.15 if st["freq"] == "THRICE_DAILY" else 1.0
            yield_val = round(max(base_yield * freq_multiplier + random.gauss(0, 0.5), 2.0), 2)

            # Anomaly injection (10 over 5 years)
            if anomalies_count < 10 and day % 120 == 40 and a_id == "TD-003":
                anomalies_count += 1
                severity = "CRITICAL" if anomalies_count % 2 == 0 else "SEVERE"
                yield_val = round(yield_val * 0.60, 2)
                st["withholding"] = 3
                
                # Health Case Record
                health_records.append({
                    "case_id": f"HC-{next_case_id:04d}",
                    "animal_id": a_id,
                    "severity": severity,
                    "diagnosis": "Clinical Mastitis - Quarter Swelling",
                    "notes": f"Drop in yield to {yield_val}L. Intramammary Cefquinome administered.",
                    "status": "RESOLVED",
                    "opened_at": sim_date
                })
                next_case_id += 1

            # Split across sessions
            if st["freq"] == "THRICE_DAILY":
                m = round(yield_val * 0.38, 2)
                a = round(yield_val * 0.32, 2)
                e = round(yield_val - m - a, 2)
            else:
                m = round(yield_val * 0.55, 2)
                a = 0.0
                e = round(yield_val - m, 2)

            if st["withholding"] > 0:
                st["withholding"] -= 1
            else:
                daily_bulk_milk += yield_val

            milk_records.append({
                "animal_id": a_id,
                "production_date": sim_date.date(),
                "morning_yield": m,
                "afternoon_yield": a,
                "evening_yield": e,
                "total_yield": yield_val,
                "status": "CONFIRMED"
            })

            # Breeding eligibility
            if st["dim"] >= 65 and st["conception_day"] is None:
                st["conception_day"] = day
                breeding_records.append({
                    "record_id": f"BR-{len(breeding_records)+1:04d}",
                    "animal_id": a_id,
                    "event_type": "insemination",
                    "result": "CONFIRMED",
                    "technician": "VET_SERVICE",
                    "timestamp": sim_date
                })

            # Gestation / Dry-off cycle
            if st["conception_day"]:
                days_preg = day - st["conception_day"]
                if days_preg == 222:
                    st["status"] = "DRY"
                elif days_preg >= 282:
                    st["conception_day"] = None
                    st["dim"] = 0
                    st["parity"] += 1
                    st["status"] = "LACTATING"
                    breeding_records.append({
                        "record_id": f"BR-{len(breeding_records)+1:04d}",
                        "animal_id": a_id,
                        "event_type": "calving",
                        "result": "HEALTHY_CALF",
                        "technician": "HERDSMAN",
                        "timestamp": sim_date
                    })

    # Deduct calf intake (8L) & domestic quota (10L)
    net_sales = max(daily_bulk_milk - 18.0, 0.0)
    credit_sales_liters += net_sales

    # 15-Day Accounts Receivable Settlement (PKR 225/L)
    if day % 15 == 0 and day > 0:
        rev_amount = credit_sales_liters * 225.0
        finance_records.append({
            "transaction_type": "INCOME",
            "category": "MILK_SALES",
            "amount": round(rev_amount, 2),
            "transaction_date": sim_date.date(),
            "reference": f"15-Day Settlement Day {day}",
            "status": "CLEARED",
            "currency": "PKR"
        })
        # Feed Expense
        finance_records.append({
            "transaction_type": "EXPENSE",
            "category": "FEED",
            "amount": round(20 * 2000.0 * 15, 2),
            "transaction_date": sim_date.date(),
            "reference": f"Feed Settlement Day {day}",
            "status": "CLEARED",
            "currency": "PKR"
        })
        credit_sales_liters = 0.0

print(f"Generated:")
print(f" - {len(milk_records)} Milk Production Records")
print(f" - {len(health_records)} Health / Treatment Records")
print(f" - {len(breeding_records)} Breeding & Calving Records")
print(f" - {len(finance_records)} Financial Ledger Transactions")

# Bulk Insert into Database
print("\nInserting into PostgreSQL...")
with engine.connect() as conn:
    if milk_records:
        conn.execute(
            text("""
                INSERT INTO milk_production (animal_id, production_date, morning_yield, afternoon_yield, evening_yield, total_yield, status)
                VALUES (:animal_id, :production_date, :morning_yield, :afternoon_yield, :evening_yield, :total_yield, :status)
            """),
            milk_records
        )
    if health_records:
        conn.execute(
            text("""
                INSERT INTO health_cases (case_id, animal_id, severity, diagnosis, notes, status, opened_at)
                VALUES (:case_id, :animal_id, :severity, :diagnosis, :notes, :status, :opened_at)
            """),
            health_records
        )
    if breeding_records:
        conn.execute(
            text("""
                INSERT INTO breeding_records (record_id, animal_id, event_type, result, technician, timestamp)
                VALUES (:record_id, :animal_id, :event_type, :result, :technician, :timestamp)
            """),
            breeding_records
        )
    if finance_records:
        conn.execute(
            text("""
                INSERT INTO financial_transactions (transaction_type, category, amount, transaction_date, reference, status, currency)
                VALUES (:transaction_type, :category, :amount, :transaction_date, :reference, :status, :currency)
            """),
            finance_records
        )
    conn.commit()

print(">>> ALL 5-YEAR RECORDS INSERTED DIRECTLY INTO DATABASE <<<")
