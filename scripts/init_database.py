"""Initialize the DairyOS PostgreSQL schema through the single DB boundary."""

from dairyos.data.database.database import initialize_database


if __name__ == "__main__":
    print("[*] Creating database tables...")
    initialize_database()
    print("[+] Database initialization completed")
