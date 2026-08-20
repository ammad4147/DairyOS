# -*- coding: utf-8 -*-
from dairyos.data.database.session import engine
from sqlalchemy import text

print("=== LINKING TREATMENT RECORD TO HEALTH CASE 3 ===")

with engine.connect() as conn:
    # 1. Update treatment_record to link to health_case_id = 3
    conn.execute(
        text("""
            UPDATE treatment_record
            SET health_case_id = 3
            WHERE id = 7;
        """)
    )
    
    # 2. Sync withdrawal_until on health_cases table from treatment record
    conn.execute(
        text("""
            UPDATE health_cases
            SET withdrawal_until = (
                SELECT milk_withdrawal_until 
                FROM treatment_record 
                WHERE id = 7
            )
            WHERE id = 3;
        """)
    )
    conn.commit()
    print("[OK] Treatment 7 linked to Health Case 3. Withdrawal deadline synchronized.")