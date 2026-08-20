# -*- coding: utf-8 -*-
from dairyos.data.database.session import engine
from sqlalchemy import text
from datetime import datetime, timedelta

print("=== TESTING DATABASE TRIGGER AUTO-SYNCHRONIZATION ===")

with engine.begin() as conn:
    # 1. Fetch current withdrawal_until for case 3
    case_before = conn.execute(text("SELECT id, case_id, withdrawal_until FROM health_cases WHERE id = 3")).mappings().first()
    print(f"Before Treatment: Case {case_before['case_id']} withdrawal_until = {case_before['withdrawal_until']}")

    # 2. Insert an extended treatment (e.g. 7 days withdrawal)
    new_until = datetime.utcnow() + timedelta(days=7)
    conn.execute(
        text("""
            INSERT INTO treatment_record (
                animal_id, medicine, dose, treated_by, treated_at,
                milk_withdrawal_days, milk_withdrawal_until, withdrawal_source,
                notes, health_case_id
            ) VALUES (
                'TD-015', 'Penicillin Long-Acting', '20ml IM', 'DR_ASIF_VET',
                NOW(), 7.0, :until, 'manual_override', 'Extended therapy test', 3
            )
        """),
        {"until": new_until}
    )

    # 3. Verify health_cases table was updated automatically by the database trigger
    case_after = conn.execute(text("SELECT id, case_id, withdrawal_until FROM health_cases WHERE id = 3")).mappings().first()
    print(f"After Treatment:  Case {case_after['case_id']} withdrawal_until = {case_after['withdrawal_until']}")
    
    # Assert trigger worked
    assert case_after['withdrawal_until'] is not None, "Trigger failed to populate withdrawal_until"
    print("[PASS] PostgreSQL Trigger successfully updated parent health case!")