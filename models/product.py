from db.database import get_connection
from utils.backup import auto_backup
import time


class Product:
    def __init__(self, id, name, category, quantity, price, cost_price):
        self.id = id
        self.name = name
        self.category = category
        self.quantity = quantity
        self.price = price
        self.cost_price = cost_price

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO products (name, category, quantity, price, cost_price)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.name, self.category, self.quantity, self.price, self.cost_price))

        conn.commit()
        conn.close()
        auto_backup()  # Backup after adding
        

    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, category, quantity, price, cost_price
            FROM products
        """)
        products = cursor.fetchall()
        conn.close()
        return [Product(*p) for p in products]


    @staticmethod
    def get_by_id(product_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, category, quantity, price, cost_price
            FROM products
            WHERE id = ?
        """, (product_id,))
        product = cursor.fetchone()
        conn.close()
        if product:
            return Product(*product)
        return None
    
    @staticmethod
    def update_quantity(product_id, new_quantity):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products
            SET quantity = ?
            WHERE id = ?
        ''', (new_quantity, product_id))
        conn.commit()
        conn.close()
        auto_backup()

    @staticmethod
    def get_all_categories():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category ASC")
        rows = cursor.fetchall()
        conn.close()

        categories = []
        has_no_category = False

        for row in rows:
            if row[0] and row[0].strip():
                categories.append(row[0])
            else:
                has_no_category = True

        if has_no_category:
            categories.insert(0, "No Category")

        return categories
    
    @staticmethod
    def rename_category(old_category, new_category):
        """
        Rename a category for all products.
        Handles 'No Category' as empty/NULL in DB.
        Ignores case differences and trims spaces.
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Handle the "No Category" pseudo-category in UI
        if old_category.strip().lower() == "no category":
            cursor.execute("""
                UPDATE products
                SET category = ?
                WHERE category IS NULL
                OR TRIM(category) = ''
            """, (new_category.strip(),))
        else:
            cursor.execute("""
                UPDATE products
                SET category = ?
                WHERE LOWER(TRIM(category)) = LOWER(?)
            """, (new_category.strip(), old_category.strip()))

        conn.commit()
        conn.close()



    @staticmethod
    def get_low_stock(threshold=5):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, quantity FROM products WHERE quantity < ?", (threshold,))
        items = cursor.fetchall()
        conn.close()
        return items
    
    
    @staticmethod
    def update_product(product_id, name, category, quantity, price, cost_price):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products
            SET name = ?, category = ?, quantity = ?, price = ?, cost_price = ?
            WHERE id = ?
        ''', (name, category, quantity, price, cost_price, product_id))
        conn.commit()
        conn.close()
        auto_backup()

    @staticmethod
    def restock_product(product_id, added_quantity):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products
            SET quantity = quantity + ?
            WHERE id = ?
        ''', (added_quantity, product_id))
        conn.commit()
        conn.close()
        auto_backup()


    @staticmethod
    def delete(product_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()
        auto_backup()

    @staticmethod
    def clear_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products")
        conn.commit()
        conn.close()
        auto_backup()
        
        
    @staticmethod
    def get_all_migration_logs():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM migration_log ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows



