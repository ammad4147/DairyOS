from dairyos.data.database.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("=== DATABASE TABLE & RECORD VERIFICATION ===")
    
    # Check tables of interest
    target_tables = ["animal", "animals", "milk_production", "operational_events", "breeding_records", "health_cases", "financial_transactions"]
    
    for tbl in target_tables:
        try:
            cnt = conn.execute(text(f'SELECT count(*) FROM "{tbl}";')).scalar()
            cols_res = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tbl}' ORDER BY ordinal_position;")).fetchall()
            cols = [c[0] for c in cols_res]
            print(f"\n[Table: {tbl}] -> Rows: {cnt}")
            print(f" Columns: {', '.join(cols[:8])} ...")
            
            # If records exist, show sample
            if cnt > 0 and tbl in ["animal", "animals"]:
                sample = conn.execute(text(f'SELECT * FROM "{tbl}" LIMIT 3;')).fetchall()
                print(" Sample records:")
                for s in sample:
                    print(f"   {s}")
        except Exception as e:
            print(f"\n[Table: {tbl}] -> Error: {e}")
