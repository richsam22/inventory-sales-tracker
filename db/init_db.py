from database import get_connection

conn = get_connection()
cursor = conn.cursor()

# --- Products table (initial definition, without last_updated) ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        cost_price REAL NOT NULL DEFAULT 0
    )
''')

# --- Sales table (with profit + transaction_id) ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        product_name TEXT,
        quantity_sold INTEGER NOT NULL,
        total_price REAL NOT NULL,
        profit REAL NOT NULL DEFAULT 0,
        timestamp TEXT NOT NULL,
        transaction_id INTEGER,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
    )
''')

# --- Transactions table ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        grand_total REAL NOT NULL
    )
''')

# --- Users table ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','staff'))
    )
''')

# --- Safe migration for older DBs ---

# Ensure cost_price exists in products
cursor.execute("PRAGMA table_info(products)")
product_columns = [col[1] for col in cursor.fetchall()]
if 'cost_price' not in product_columns:
    cursor.execute("ALTER TABLE products ADD COLUMN cost_price REAL NOT NULL DEFAULT 0")
    print("Added 'cost_price' column to products table.")

# ✅ Remove last_updated column if it exists
cursor.execute("PRAGMA table_info(products)")
product_columns = [col[1] for col in cursor.fetchall()]
if 'last_updated' in product_columns:
    print("⚠️ last_updated column found, migrating products table...")

    # 1. Create new table without last_updated
    cursor.execute('''
        CREATE TABLE products_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            cost_price REAL NOT NULL DEFAULT 0
        )
    ''')

    # 2. Copy data except last_updated
    cursor.execute('''
        INSERT INTO products_new (id, name, category, quantity, price, cost_price)
        SELECT id, name, category, quantity, price, cost_price
        FROM products
    ''')

    # 3. Drop old products table
    cursor.execute("DROP TABLE products")

    # 4. Rename new table
    cursor.execute("ALTER TABLE products_new RENAME TO products")

    print("✅ Removed last_updated column from products table.")

# Ensure profit exists in sales
cursor.execute("PRAGMA table_info(sales)")
sales_columns = [col[1] for col in cursor.fetchall()]
if 'profit' not in sales_columns:
    cursor.execute("ALTER TABLE sales ADD COLUMN profit REAL NOT NULL DEFAULT 0")
    print("Added 'profit' column to sales table.")

# Ensure transaction_id exists in sales
if 'transaction_id' not in sales_columns:
    cursor.execute("ALTER TABLE sales ADD COLUMN transaction_id INTEGER")
    print("Added 'transaction_id' column to sales table.")

# Ensure default admin user exists
cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("admin", "admin123", "admin"))
    conn.commit()
    print("✅ Admin user created.")

conn.commit()
conn.close()

print("✅ Database initialized with transactions + profit tracking.")






