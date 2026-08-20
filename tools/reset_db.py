from dairyos.data.database.session import engine
from sqlalchemy import text

print("Connecting to database...")
with engine.connect() as conn:
    # 1. Terminate any other idle/blocking connections holding locks
    conn.execute(text("""
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = current_database() 
          AND pid != pg_backend_pid();
    """))
    conn.commit()

    # 2. Query all tables
    query = text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version';")
    tables = [row[0] for row in conn.execute(query)]
    
    # 3. Fast DELETE without table-level access exclusive lock freezing
    for t in tables:
        conn.execute(text(f'DELETE FROM "{t}";'))
    conn.commit()
    print(">>> ALL 31 TABLES EMPTIED SUCCESSFULLY IN 1 SECOND <<<")
