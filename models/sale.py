import time
from datetime import datetime
from db.database import get_connection
from utils.backup import auto_backup

class Sale:
    def __init__(self, product_id, quantity_sold):
        self.product_id = product_id
        self.quantity_sold = quantity_sold
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    def save(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT quantity, price, cost_price, name FROM products WHERE id = ?", (self.product_id,))
        product = cursor.fetchone()

        if not product:
            print("Product not found!")
            conn.close()
            return None  # return nothing if failed

        current_quantity, price_per_unit, cost_price, product_name = product

        if self.quantity_sold > current_quantity:
            print("Not enough stock!")
            conn.close()
            return None

        total_price = price_per_unit * self.quantity_sold
        profit_per_unit = price_per_unit - cost_price
        total_profit = profit_per_unit * self.quantity_sold
        

        cursor.execute('''
            INSERT INTO sales (product_id, product_name, quantity_sold, total_price, profit, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.product_id, product_name, self.quantity_sold, total_price, total_profit, self.timestamp))

        sale_id = cursor.lastrowid  # ✅ capture the ID

        new_quantity = current_quantity - self.quantity_sold
        cursor.execute('''
            UPDATE products
            SET quantity = ?
            WHERE id = ?
        ''', (new_quantity, self.product_id))

        conn.commit()
        conn.close()
        auto_backup()

        return sale_id  # ✅ return new sale id


        
    @staticmethod
    def add(product_id, quantity_sold, total_price=None, profit=None, transaction_id=None):
        conn = get_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        # Get product details
        cursor.execute("SELECT name, price, cost_price FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            conn.close()
            raise ValueError("Invalid product_id")

        product_name, selling_price, cost_price = product

        # Auto calculate total price if not provided
        if total_price is None:
            total_price = selling_price * quantity_sold

        # Auto calculate profit if not provided
        if profit is None:
            profit = (selling_price - cost_price) * quantity_sold

        cursor.execute("""
            INSERT INTO sales (product_id, product_name, quantity_sold, total_price, profit, timestamp, transaction_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (product_id, product_name, quantity_sold, total_price, profit, timestamp, transaction_id))

        conn.commit()
        sale_id = cursor.lastrowid
        conn.close()

        auto_backup()
        return sale_id


    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT sales.id, products.name, sales.quantity_sold, sales.total_price, 
                sales.profit, sales.timestamp
            FROM sales
            JOIN products ON sales.product_id = products.id
            ORDER BY sales.timestamp DESC
        ''')
        results = cursor.fetchall()

        conn.close()
        return results
    
    @staticmethod
    def get_by_id(sale_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sales.id, products.name, products.category, 
                   sales.quantity_sold, sales.total_price, sales.profit, sales.timestamp
            FROM sales
            JOIN products ON sales.product_id = products.id
            WHERE sales.id = ?
        """, (sale_id,))
        result = cursor.fetchone()
        conn.close()
        return result


        
    @staticmethod
    def get_best_selling_product():
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.product_id, p.name, 
                SUM(s.quantity_sold) AS total_qty, 
                SUM(s.total_price) AS revenue
            FROM sales s
            JOIN products p ON s.product_id = p.id
            GROUP BY s.product_id
            ORDER BY total_qty DESC
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        return result  # (product_id, product_name, total_qty, revenue)
    
    @staticmethod
    def get_total_profit():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(profit) FROM sales")
        total_profit = cursor.fetchone()[0] or 0
        conn.close()
        return total_profit



    
    @staticmethod
    def get_sales_summary_per_product():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.name, SUM(s.quantity_sold) AS total_quantity
            FROM sales s
            JOIN products p ON s.product_id = p.id
            GROUP BY p.id
            ORDER BY total_quantity DESC
        """)
        result = cursor.fetchall()
        conn.close()
        return result
    
    
    @staticmethod
    def get_all_with_category(category=None):
        conn = get_connection()
        cursor = conn.cursor()

        if category and category != "All":
            cursor.execute("""
                SELECT sales.id, products.name, products.category, sales.quantity_sold, 
                       sales.total_price, sales.timestamp
                FROM sales
                JOIN products ON sales.product_id = products.id
                WHERE products.category = ?
            """, (category,))
        else:
            cursor.execute("""
                SELECT sales.id, products.name, products.category, sales.quantity_sold, 
                       sales.total_price, sales.timestamp
                FROM sales
                JOIN products ON sales.product_id = products.id
            """)

        rows = cursor.fetchall()
        conn.close()
        return rows

    
    @staticmethod
    def clear_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sales")
        conn.commit()
        conn.close()
        auto_backup()
        

