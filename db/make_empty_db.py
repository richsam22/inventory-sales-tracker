import sqlite3
import os

SRC_DB = os.path.join("db", "inventory.db")          # your dev/test DB
DEST_DB = os.path.join("db", "inventory_empty.db")   # clean copy for shipping

# Copy schema
with sqlite3.connect(SRC_DB) as src, sqlite3.connect(DEST_DB) as dest:
    src.backup(dest)

# Wipe products, sales, transactions but keep users
with sqlite3.connect(DEST_DB) as conn:
    c = conn.cursor()
    c.execute("DELETE FROM products")
    c.execute("DELETE FROM sales")
    c.execute("DELETE FROM transactions")
    # Reset auto-increment counters
    c.execute("DELETE FROM sqlite_sequence WHERE name IN ('products','sales','transactions')")
    conn.commit()

print(f"✅ Clean DB created at {DEST_DB}")
