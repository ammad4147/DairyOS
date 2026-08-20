# -*- coding: utf-8 -*-
from dairyos.data.database.session import engine
from sqlalchemy import text

print("=== FEED, RATION & NUTRITION TABLES ===")
with engine.connect() as conn:
    tables = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND (table_name ILIKE '%feed%' 
            OR table_name ILIKE '%ration%' 
            OR table_name ILIKE '%nutri%' 
            OR table_name ILIKE '%invent%')
        ORDER BY table_name;
    """)).fetchall()
    
    for t in tables:
        tname = t.table_name
        print(f"\n--- TABLE: {tname} ---")
        cols = conn.execute(text(f"""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = '{tname}' 
            ORDER BY ordinal_position;
        """)).fetchall()
        for c in cols:
            print(f"  • {c.column_name:<25} | {c.data_type:<18} | Nullable: {c.is_nullable}")