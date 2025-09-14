import sqlite3
import os, sys
from datetime import datetime

def get_db_path():
    """Return correct DB path for dev vs PyInstaller build."""
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle → put DB next to the executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running normally (dev mode) → put DB next to this file
        base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, "inventory.db")

DB_PATH = get_db_path()

MIGRATIONS = {
    "products": {
        "cost_price": "REAL DEFAULT 0",
        "supplier_name": "TEXT DEFAULT 'Unknown'",
        "last_updated": "TEXT DEFAULT NULL"
    },
    "sales": {
        "product_name": "TEXT",
        "profit": "REAL DEFAULT 0",
        "transaction_id": "INTEGER"
    }
}

def log_migration(cursor, message):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO migration_log (timestamp, message) VALUES (?, ?)",
        (timestamp, message)
    )

def run_migrations():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()

    # --- Base table creation ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            total REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)
    conn.commit()

    # --- Ensure default admin user exists ---
    cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", "admin123", "admin"))
        print("✅ Default admin user created: username=admin, password=admin123")
    conn.commit()

    # --- Run migrations on other tables ---
    for table, columns in MIGRATIONS.items():
        cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = [col[1] for col in cursor.fetchall()]

        for col_name, col_type in columns.items():
            if col_name not in existing_columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                log_migration(cursor, f"Added column '{col_name}' ({col_type}) to table '{table}'")

    # Optional: update last_updated for all products
    now = datetime.now().isoformat()
    try:
        cursor.execute("UPDATE products SET last_updated = ?", (now,))
        log_migration(cursor, "Updated 'last_updated' for all products.")
    except sqlite3.OperationalError:
        # Skip if last_updated doesn’t exist yet
        pass

    conn.commit()
    log_migration(cursor, "Database migration completed successfully.")
    conn.commit()
    conn.close()

    print("✅ Migration completed. All required tables/columns now exist.")



if __name__ == "__main__":
    run_migrations()



