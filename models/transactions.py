from datetime import datetime
from db.database import get_connection
from utils.backup import auto_backup
from models.sale import Sale   # so we can call sales.add()

def create_transaction():
    """
    Create a new empty transaction and return its ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO transactions (timestamp, grand_total)
        VALUES (?, 0)
    """, (timestamp,))

    transaction_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return transaction_id


def finalize_transaction(transaction_id):
    """
    Finalize a transaction by summing all sales linked to it.
    Updates grand_total in transactions table.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Sum sales total for this transaction
    cursor.execute("""
        SELECT COALESCE(SUM(total_price), 0)
        FROM sales
        WHERE transaction_id = ?
    """, (transaction_id,))
    grand_total = cursor.fetchone()[0]

    # Update transaction record
    cursor.execute("""
        UPDATE transactions
        SET grand_total = ?
        WHERE id = ?
    """, (grand_total, transaction_id))

    conn.commit()
    conn.close()
    auto_backup()

    return grand_total


def get_transaction_details(transaction_id):
    """
    Get transaction summary + all related sales.
    Returns dict: { 'id': ..., 'timestamp': ..., 'grand_total': ..., 'sales': [...] }
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch transaction
    cursor.execute("""
        SELECT id, timestamp, grand_total
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))
    transaction = cursor.fetchone()

    if not transaction:
        conn.close()
        return None

    # Fetch related sales
    cursor.execute("""
        SELECT id, product_id, product_name, quantity_sold, total_price, profit, timestamp
        FROM sales
        WHERE transaction_id = ?
    """, (transaction_id,))
    sales_rows = cursor.fetchall()

    conn.close()

    return {
        "id": transaction[0],
        "timestamp": transaction[1],
        "grand_total": transaction[2],
        "sales": [
            {
                "id": row[0],
                "product_id": row[1],
                "product_name": row[2],
                "quantity_sold": row[3],
                "total_price": row[4],
                "profit": row[5],
                "timestamp": row[6],
            }
            for row in sales_rows
        ]
    }
