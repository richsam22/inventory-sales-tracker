import os
import zipfile
from datetime import datetime
from db.database import DB_PATH
from db.migrations import run_migrations 

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "backups")
MAX_BACKUPS = 5  # Keep only latest 5 backups

def auto_backup():
    """Automatically create a timestamped compressed DB backup and remove older ones."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    if not os.path.exists(DB_PATH):
        print(f"[Auto Backup] ⚠️ No database found at {DB_PATH}. Creating a fresh one...")
        run_migrations()   # create DB schema so we don’t crash

    # Create timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"backup_{timestamp}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    # Create zip archive
    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(DB_PATH, arcname="inventory.db")  # inside zip always named inventory.db

    print(f"[Auto Backup] ✅ Backup saved at {backup_path}")

    # Get list of all backups sorted by newest first
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".zip")],
        key=lambda f: os.path.getmtime(os.path.join(BACKUP_DIR, f)),
        reverse=True
    )

    # Delete backups beyond the MAX_BACKUPS limit
    for old_backup in backups[MAX_BACKUPS:]:
        os.remove(os.path.join(BACKUP_DIR, old_backup))
        print(f"[Auto Backup] 🗑️ Deleted old backup: {old_backup}")






