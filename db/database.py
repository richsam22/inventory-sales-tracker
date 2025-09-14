import sqlite3
import os, sys

def get_db_path():
    """Return correct DB path for dev vs PyInstaller build."""
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle → put DB next to the executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running normally (dev mode) → keep it in project/db
        base_dir = os.path.join(os.path.dirname(__file__), "..", "db")

        # Make sure the folder exists
        os.makedirs(base_dir, exist_ok=True)

    return os.path.join(base_dir, "inventory.db")

DB_PATH = get_db_path()


def get_connection():
    print("Using database at:", DB_PATH)
    return sqlite3.connect(DB_PATH, timeout=10)

