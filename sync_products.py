# sync_products.py
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional


from db.database import get_connection
from firebase_config import fire_db

# Stream objects (pyrebase returns a Stream object)
_product_stream = None
_sales_stream = None
_stream_threads = []


# ----------------- Helpers ----------------- #
def now_iso() -> str:
    return datetime.utcnow().isoformat()


def ts_to_epoch(ts: Optional[Any]) -> float:
    """
    Convert remote/local timestamp (ISO str or numeric) to epoch float.
    If None or invalid => 0.0
    """
    if ts is None:
        return 0.0
    # numeric (stored as REAL)
    try:
        return float(ts)
    except Exception:
        pass
    # try ISO string
    try:
        return datetime.fromisoformat(str(ts)).timestamp()
    except Exception:
        # fallback
        return 0.0


def ensure_last_updated_columns():
    """Add last_updated columns to products & sales if missing (migration)."""
    conn = get_connection()
    cursor = conn.cursor()

    # products
    cursor.execute("PRAGMA table_info(products)")
    cols = [c[1] for c in cursor.fetchall()]
    if 'last_updated' not in cols:
        cursor.execute("ALTER TABLE products ADD COLUMN last_updated REAL DEFAULT 0")
        print("⚙️ Added 'last_updated' column to products (migration)")

    # sales
    cursor.execute("PRAGMA table_info(sales)")
    cols = [c[1] for c in cursor.fetchall()]
    if 'last_updated' not in cols:
        cursor.execute("ALTER TABLE sales ADD COLUMN last_updated REAL DEFAULT 0")
        print("⚙️ Added 'last_updated' column to sales (migration)")

    conn.commit()
    conn.close()


# ----------------- Local upsert from remote ----------------- #
def upsert_local_product(p: Dict[str, Any]):
    """
    Insert or update the local product ONLY if remote last_updated is newer.
    p: dict from Firebase, expected keys: id, name, category, quantity, price, cost_price, last_updated (opt)
    """
    if not p or 'id' not in p:
        return

    pid = int(p['id'])
    remote_ts = ts_to_epoch(p.get('last_updated'))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT last_updated FROM products WHERE id=?", (pid,))
    row = cursor.fetchone()
    local_ts = row[0] if row else 0.0

    # If remote is newer, overwrite local
    if remote_ts > ts_to_epoch(local_ts):
        cursor.execute("""
            INSERT INTO products (id, name, category, quantity, price, cost_price, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                category=excluded.category,
                quantity=excluded.quantity,
                price=excluded.price,
                cost_price=excluded.cost_price,
                last_updated=excluded.last_updated
        """, (
            pid,
            p.get('name'),
            p.get('category'),
            p.get('quantity') if p.get('quantity') is not None else 0,
            p.get('price') if p.get('price') is not None else 0.0,
            p.get('cost_price') if p.get('cost_price') is not None else 0.0,
            remote_ts
        ))
        print(f"⬇️ Applied remote product {pid} -> local (remote_ts={remote_ts}, local_ts={local_ts})")

    conn.commit()
    conn.close()


def upsert_local_sale(s: Dict[str, Any]):
    if not s or 'id' not in s:
        return
    sid = int(s['id'])
    remote_ts = ts_to_epoch(s.get('last_updated'))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT last_updated FROM sales WHERE id=?", (sid,))
    row = cursor.fetchone()
    local_ts = row[0] if row else 0.0

    if remote_ts > ts_to_epoch(local_ts):
        cursor.execute("""
            INSERT INTO sales (id, product_id, product_name, quantity_sold, total_price, profit, timestamp, transaction_id, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                product_id=excluded.product_id,
                product_name=excluded.product_name,
                quantity_sold=excluded.quantity_sold,
                total_price=excluded.total_price,
                profit=excluded.profit,
                timestamp=excluded.timestamp,
                transaction_id=excluded.transaction_id,
                last_updated=excluded.last_updated
        """, (
            sid,
            s.get('product_id'),
            s.get('product_name'),
            s.get('quantity_sold') if s.get('quantity_sold') is not None else 0,
            s.get('total_price') if s.get('total_price') is not None else 0.0,
            s.get('profit') if s.get('profit') is not None else 0.0,
            s.get('timestamp'),
            s.get('transaction_id'),
            remote_ts
        ))
        print(f"⬇️ Applied remote sale {sid} -> local (remote_ts={remote_ts}, local_ts={local_ts})")

    conn.commit()
    conn.close()


# ----------------- Firebase stream handlers ----------------- #
def _products_stream_handler(message):
    """
    message: dict with keys 'event' (put/patch), 'path', 'data'
    """
    try:
        event = message.get("event")
        path = message.get("path")
        data = message.get("data")
    except Exception:
        # pyrebase may return other shaped objects; be defensive
        event = getattr(message, "event", None)
        path = getattr(message, "path", None)
        data = getattr(message, "data", None)

    # print("STREAM products:", event, path)
    if event in ("put", "patch"):
        # Full snapshot
        if path == "/" and isinstance(data, dict):
            for pid, pdata in data.items():
                if pdata:
                    # pdata could be raw values or product dict
                    if isinstance(pdata, dict):
                        upsert_local_product(pdata)
        else:
            # path to a single child like '/14' or '/14/quantity'
            if path.startswith("/"):
                parts = path.strip("/").split("/")
                if len(parts) == 1:
                    # whole child replaced/created
                    pid = parts[0]
                    pdata = data
                    if isinstance(pdata, dict):
                        # ensure id exists
                        if "id" not in pdata:
                            pdata["id"] = pid
                        upsert_local_product(pdata)
                else:
                    # partial field updated; fetch full object from Firebase to be safe
                    pid = parts[0]
                    full = fire_db.child("products").child(pid).get().val()
                    if full:
                        if "id" not in full:
                            full["id"] = pid
                        upsert_local_product(full)


def _sales_stream_handler(message):
    try:
        event = message.get("event")
        path = message.get("path")
        data = message.get("data")
    except Exception:
        event = getattr(message, "event", None)
        path = getattr(message, "path", None)
        data = getattr(message, "data", None)

    if event in ("put", "patch"):
        if path == "/" and isinstance(data, dict):
            for sid, sdata in data.items():
                if sdata:
                    if isinstance(sdata, dict):
                        if "id" not in sdata:
                            sdata["id"] = sid
                        upsert_local_sale(sdata)
        else:
            if path.startswith("/"):
                parts = path.strip("/").split("/")
                if len(parts) == 1:
                    sid = parts[0]
                    sdata = data
                    if isinstance(sdata, dict):
                        if "id" not in sdata:
                            sdata["id"] = sid
                        upsert_local_sale(sdata)
                else:
                    sid = parts[0]
                    full = fire_db.child("sales").child(sid).get().val()
                    if full:
                        if "id" not in full:
                            full["id"] = sid
                        upsert_local_sale(full)


# ----------------- Public: start/stop listeners ----------------- #
def start_listeners():
    """
    Start Firebase listeners in background threads.
    Call this once during app startup (after auth if required).
    """
    global _product_stream, _sales_stream, _stream_threads
    ensure_last_updated_columns()

    def run_products_stream():
        global _product_stream
        try:
            _product_stream = fire_db.child("products").stream(_products_stream_handler, None)
        except Exception as e:
            print("⚠️ products stream error:", e)

    def run_sales_stream():
        global _sales_stream
        try:
            _sales_stream = fire_db.child("sales").stream(_sales_stream_handler, None)
        except Exception as e:
            print("⚠️ sales stream error:", e)

    t1 = threading.Thread(target=run_products_stream, daemon=True)
    t2 = threading.Thread(target=run_sales_stream, daemon=True)
    t1.start()
    t2.start()
    _stream_threads = [t1, t2]
    print("🔁 Firebase listeners started (products + sales).")


def stop_listeners():
    """
    Stop streams if possible. Pyrebase stream object supports close()
    """
    global _product_stream, _sales_stream
    try:
        if _product_stream:
            _product_stream.close()
            _product_stream = None
        if _sales_stream:
            _sales_stream.close()
            _sales_stream = None
    except Exception as e:
        print("⚠️ Error closing streams:", e)
    print("⛔ Firebase listeners stopped.")


# ----------------- Selective push helpers ----------------- #
def push_product_to_firebase(product_id: int):
    """
    Reads product from local DB and pushes it to Firebase with last_updated now.
    """
    ensure_last_updated_columns()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, quantity, price, cost_price, last_updated FROM products WHERE id=?", (product_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    pid, name, category, quantity, price, cost_price, local_ts = row
    local_ts = float(local_ts) if local_ts else time.time()
    # update local last_updated to now and push
    new_ts = time.time()
    cursor.execute("UPDATE products SET last_updated=? WHERE id=?", (new_ts, pid))
    conn.commit()
    conn.close()

    product = {
        "id": pid,
        "name": name,
        "category": category,
        "quantity": quantity,
        "price": price,
        "cost_price": cost_price,
        "last_updated": new_ts
    }
    fire_db.child("products").child(str(pid)).set(product)
    print(f"⬆️ Pushed product {pid} -> Firebase (ts={new_ts})")
    return True


def push_sale_to_firebase(sale_id: int):
    ensure_last_updated_columns()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_id, product_name, quantity_sold, total_price, profit, timestamp, transaction_id, last_updated FROM sales WHERE id=?", (sale_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    sid, product_id, product_name, quantity_sold, total_price, profit, timestamp, transaction_id, local_ts = row
    new_ts = time.time()
    cursor.execute("UPDATE sales SET last_updated=? WHERE id=?", (new_ts, sid))
    conn.commit()
    conn.close()

    sale = {
        "id": sid,
        "product_id": product_id,
        "product_name": product_name,
        "quantity_sold": quantity_sold,
        "total_price": total_price,
        "profit": profit,
        "timestamp": timestamp,
        "transaction_id": transaction_id,
        "last_updated": new_ts
    }
    fire_db.child("sales").child(str(sid)).set(sale)
    print(f"⬆️ Pushed sale {sid} -> Firebase (ts={new_ts})")
    return True


# ----------------- Bulk sync (kept for compatibility) ----------------- #
def download_products(cursor):
    """Bulk download (called at startup as initial sync)."""
    products = fire_db.child("products").get().val()
    count = 0
    if isinstance(products, dict):
        for _, p in products.items():
            # ensure last_updated exists (use 0 if missing)
            if isinstance(p, dict):
                if "last_updated" not in p:
                    p["last_updated"] = 0
                upsert_local_product(p)
                count += 1
    return count


def download_sales(cursor):
    sales = fire_db.child("sales").get().val()
    count = 0
    if isinstance(sales, dict):
        for _, s in sales.items():
            if isinstance(s, dict):
                if "last_updated" not in s:
                    s["last_updated"] = 0
                upsert_local_sale(s)
                count += 1
    return count


def sync_from_firebase():
    conn = get_connection()
    cursor = conn.cursor()
    ensure_last_updated_columns()
    products_synced = download_products(cursor)
    sales_synced = download_sales(cursor)
    conn.commit()
    conn.close()
    print(f"✅ Sync complete: {products_synced} products, {sales_synced} sales downloaded from Firebase.")


def upload_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products")
    rows = cursor.fetchall()
    count = 0
    for (pid,) in rows:
        push_product_to_firebase(pid)
        count += 1
    print(f"✅ {count} products pushed to Firebase.")
    conn.close()


def upload_sales():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sales")
    rows = cursor.fetchall()
    count = 0
    for (sid,) in rows:
        push_sale_to_firebase(sid)
        count += 1
    print(f"✅ {count} sales pushed to Firebase.")
    conn.close()


def sync_to_firebase():
    ensure_last_updated_columns()
    upload_products()
    upload_sales()
    
    

