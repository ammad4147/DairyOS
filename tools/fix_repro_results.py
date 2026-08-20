# -*- coding: utf-8 -*-
from dairyos.data.database.session import engine
from sqlalchemy import text

print("=== RE-ALIGNING PREGNANCY CHECK RESULTS IN DATABASE ===")

with engine.connect() as conn:
    # Update 'CONFIRMED_PREGNANT' to 'CONFIRMED' for all pregnancy check records
    result = conn.execute(
        text("""
            UPDATE breeding_records
            SET result = 'CONFIRMED'
            WHERE event_type ILIKE '%PREGNANCY%' AND result = 'CONFIRMED_PREGNANT';
        """)
    )
    conn.commit()
    print(f"[OK] Updated {result.rowcount} pregnancy check records to canonical result 'CONFIRMED'.")