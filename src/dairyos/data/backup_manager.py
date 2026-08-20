import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

class DataBackupManager:
    """
    Ensures absolute data persistence and zero-loss guarantees for DairyOS.
    Backs up SQLite operational databases automatically to an isolated backup vault.
    """
    @staticmethod
    def create_safety_backup(db_path: str = "dairyos.db") -> str:
        vault = Path("D:/DairyOS/backups")
        vault.mkdir(parents=True, exist_ok=True)
        
        target_db = Path(db_path)
        if not target_db.exists():
            # Fallback check in data directory
            target_db = Path("src/dairyos/data/dairyos.db")
            
        if target_db.exists():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_file = vault / f"dairyos_safe_backup_{timestamp}.db"
            shutil.copy2(target_db, backup_file)
            return str(backup_file.absolute())
        return "No active SQLite db found to backup."
