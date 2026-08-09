import shutil
from datetime import datetime
from pathlib import Path

class BackupService:
    def __init__(self, source_dir: Path, backup_dir: Path):
        self.source_dir = source_dir
        self.backup_dir = backup_dir

    def perform_backup(self):
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        dest = self.backup_dir / f"backup_{timestamp}"
        shutil.copytree(self.source_dir, dest)
        return dest
