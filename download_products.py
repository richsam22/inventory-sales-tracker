from db.database import get_connection
from firebase_config import fire_db

def download_products(cursor):
    products = fire_db.child("products").get().val()
    count = 0

    if isinstance(products, dict):
        for _, p in products.items():
            cursor.execute("""
                INSERT OR REPLACE INTO products 
                (id, name, category, quantity, price, cost_price)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (p["id"], p["name"], p["category"], p["quantity"], p["price"], p["cost_price"]))
            count += 1
    return count


def download_sales(cursor):
    sales = fire_db.child("sales").get().val()
    count = 0

    if isinstance(sales, dict):
        for _, s in sales.items():
            cursor.execute("""
                INSERT OR REPLACE INTO sales 
                (id, product_id, quantity, total_price, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (s["id"], s["product_id"], s["quantity"], s["total_price"], s["timestamp"]))
            count += 1
    return count


def sync_from_firebase():
    conn = get_connection()
    cursor = conn.cursor()

    products_synced = download_products(cursor)
    sales_synced = download_sales(cursor)

    conn.commit()
    conn.close()

    print(f"✅ Sync complete: {products_synced} products, {sales_synced} sales downloaded from Firebase.")


    
if __name__ == "__main__":
    print("⬇️ Downloading products from Firebase...")
    sync_from_firebase()
    