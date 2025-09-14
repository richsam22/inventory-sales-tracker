import customtkinter as ctk
from tkinter import messagebox
from db.database import get_connection
from models.product import Product
import re

class EditProductWindow(ctk.CTkToplevel):
    def __init__(self, master, product_id, refresh_callback=None):
        super().__init__(master)
        
        self.product_id = product_id
        self.refresh_callback = refresh_callback

        self.title("✏ Edit Product")
        self.geometry("420x580")
        self.resizable(False, False)

        # --- Fetch product ---
        self.product = Product.get_by_id(product_id)
        if not self.product:
            messagebox.showerror("Error", "Product not found.")
            self.destroy()
            return

        # --- Header ---
        ctk.CTkLabel(self, text="✏ Edit Product", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(15, 10))

        # --- Form Frame ---
        form = ctk.CTkFrame(self)
        form.pack(pady=10, padx=10, fill="x")

        # --- Widgets ---
        self.entries = {}
        categories = Product.get_all_categories() or []
        print("DEBUG categories:", categories)
        print("DEBUG product data:", {
            "name": self.product.name,
            "category": self.product.category,
            "quantity": self.product.quantity,
            "price": self.product.price,
            "cost_price": self.product.cost_price
        })

        ctk.CTkLabel(form, text="Category:").pack(anchor="w", pady=8, padx=10)
        self.category_combo = ctk.CTkComboBox(form, values=categories, width=180)
        self.category_combo.set(self.product.category if self.product.category in categories else categories[0] if categories else "Select a category")
        self.category_combo.pack(fill="x", pady=8, padx=10)
        self.category_combo.bind("<<ComboboxSelected>>", 
                                lambda event: print(f"DEBUG Category selected: {self.category_combo.get()}"))
        self.category_combo.update()

        self._add_field(form, "Name:", "name", self.product.name)
        self._add_field(form, "Quantity:", "quantity", str(self.product.quantity), readonly=True)
        self._add_field(form, "Price:", "price", str(self.product.price))
        self._add_field(form, "Cost Price:", "cost_price", str(self.product.cost_price))

        # --- Buttons ---
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20, padx=30, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="💾 Save Changes",
            command=self.update_product,
            corner_radius=8,
            fg_color="#4CAF50",
            hover_color="#45A049"
        ).pack(side="left", expand=True, padx=(0, 5))
        

        ctk.CTkButton(
            btn_frame,
            text="➕ Restock",
            command=self.restock_product,
            corner_radius=8,
            fg_color="#2196F3",
            hover_color="#1976D2"
        ).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🗑 Delete",
            command=self.delete_product,
            corner_radius=8,
            fg_color="#f44336",
            hover_color="#e53935"
        ).pack(side="left", expand=True, padx=(5, 0))

        self.update_idletasks()  # Force UI refresh

    def _add_field(self, parent, label_text, key, initial_value, readonly=False):
        ctk.CTkLabel(parent, text=label_text).pack(anchor="w", pady=8, padx=10)
        entry = ctk.CTkEntry(parent)
        entry.insert(0, initial_value)
        if readonly:
            entry.configure(state="readonly")
        entry.pack(fill="x", pady=8, padx=10)
        if key == "name":
            entry.focus()
        self.entries[key] = entry
        entry.bind("<KeyRelease>", lambda event: print(f"DEBUG {label_text} {entry.get()}"))

    
    def update_product(self):
        name = self.entries["name"].get().strip()
        category = self.category_combo.get().strip()
        quantity = self.entries["quantity"].get().strip()
        price = self.entries["price"].get().strip()
        cost_price = self.entries["cost_price"].get().strip()

        if not all([name, category, quantity, price, cost_price]):
            messagebox.showerror("Validation Error", "All fields are required.")
            return

        try:
            quantity_val = int(quantity)
            price_val = float(re.sub(r'[^\d.]', '', price))
            cost_price_val = float(re.sub(r'[^\d.]', '', cost_price))
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be integer and prices must be valid numbers.")
            return

        try:
            # --- Local update ---
            Product.update_product(self.product_id, name, category, quantity_val, price_val, cost_price_val)

            # --- Firebase update ---
            from firebase_config import fire_db
            import time
            product = {
                "id": self.product_id,
                "name": name,
                "category": category,
                "quantity": quantity_val,
                "price": price_val,
                "cost_price": cost_price_val,
                "last_updated": int(time.time())   # ⬅️ ADD TIMESTAMP
            }
            fire_db.child("products").child(str(self.product_id)).set(product)
            print(f"✅ Synced update for product {self.product_id} to Firebase")

            messagebox.showinfo("Success", "✅ Product updated successfully.")
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred:\n{e}")

        
    def restock_product(self):
        amount = ctk.CTkInputDialog(text="Enter amount to restock:", title="Restock Product").get_input()
        if not amount:
            return
        try:
            amount_val = int(amount)

            # --- Local update ---
            Product.restock_product(self.product_id, amount_val)

            # --- Firebase sync ---
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id=?", (self.product_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                from firebase_config import fire_db
                import time
                product = {
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "quantity": row[3],
                    "price": row[4],
                    "cost_price": row[5],
                    "last_updated": int(time.time())  # ⬅️ ADD TIMESTAMP
                }
                fire_db.child("products").child(str(row[0])).set(product)
                print(f"✅ Synced restock for product {row[0]} to Firebase")

            messagebox.showinfo("Success", f"✅ Restocked {amount_val} units.")
            if self.refresh_callback:
                self.refresh_callback()
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity entered.")
    
    
    def delete_product(self):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
            # --- Local delete ---
            Product.delete(self.product_id)

            # --- Firebase delete ---
            try:
                from firebase_config import fire_db
                fire_db.child("products").child(str(self.product_id)).remove()
                print(f"🗑 Product {self.product_id} removed from Firebase")
            except Exception as e:
                print("⚠️ Firebase delete error:", e)

            messagebox.showinfo("Deleted", "🗑 Product deleted successfully.")
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
