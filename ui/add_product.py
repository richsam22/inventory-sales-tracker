import customtkinter as ctk
from tkinter import messagebox
from models.product import Product
import re

class AddProductWindow(ctk.CTkToplevel):
    def __init__(self, master, theme="System"):
        super().__init__(master)
        ctk.set_appearance_mode(theme)
        
        self.title("➕ Add New Product")
        self.geometry("480x500")
        self.resizable(True, True)

        # --- Header ---
        ctk.CTkLabel(self, text="➕ Add New Product", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(15, 10))
        
        # ---- MAIN SCROLLABLE FRAME ----
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Form Frame ---
        form = ctk.CTkFrame(self.scroll_frame)
        form.pack(pady=10, padx=30, fill="x")

        # --- Widgets ---
        self.entries = {}
        ctk.CTkLabel(form, text="Category:").pack(anchor="w", pady=8, padx=10)
        categories = Product.get_all_categories() or ["Select a category"]
        print("DEBUG categories:", categories)
        self.category_combo = ctk.CTkComboBox(form, values=categories, width=180)
        self.category_combo.set(categories[0] if categories else "Select a category")
        self.category_combo.pack(fill="x", pady=8, padx=10)
        self.category_combo.bind("<<ComboboxSelected>>", 
                                lambda event: print(f"DEBUG Category selected: {self.category_combo.get()}"))

        self._add_field(form, "Name:", "name")
        self._add_field(form, "Quantity:", "quantity")
        self._add_field(form, "Price:", "price")
        self._add_field(form, "Cost Price:", "cost_price")

        # --- Buttons ---
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20, padx=30, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="💾 Save Product",
            command=self.save_product,
            corner_radius=8,
            fg_color="#4CAF50",
            hover_color="#45A049"
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            command=self.destroy,
            corner_radius=8,
            fg_color="#f44336",
            hover_color="#e53935"
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _add_field(self, parent, label_text, key):
        ctk.CTkLabel(parent, text=label_text).pack(anchor="w", pady=8, padx=10)
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", pady=8, padx=10)
        if key == "name":
            entry.focus()
        self.entries[key] = entry
        entry.bind("<KeyRelease>", lambda event: print(f"DEBUG {label_text} {entry.get()}"))

    def save_product(self):
        self.update_idletasks()
        name = self.entries["name"].get().strip()
        category = self.category_combo.get().strip()
        quantity = self.entries["quantity"].get().strip()
        price = self.entries["price"].get().strip()
        cost_price = self.entries["cost_price"].get().strip()
        
        print("DEBUG save_product:", {"name": name, "category": category, 
                                      "quantity": quantity, "price": price, 
                                      "cost_price": cost_price})

        # Validation
        missing_fields = []
        if not name:
            missing_fields.append("Name")
        if not category or category == "Select a category":
            missing_fields.append("Category")
        if not quantity:
            missing_fields.append("Quantity")
        if not price:
            missing_fields.append("Price")
        if not cost_price:
            missing_fields.append("Cost Price")
        
        if missing_fields:
            messagebox.showerror("Validation Error", f"Please fill in the following fields: {', '.join(missing_fields)}.")
            return

        try:
            quantity_val = int(quantity)
            price_val = float(re.sub(r'[^\d.]', '', price))
            cost_price_val = float(re.sub(r'[^\d.]', '', cost_price))
            if price_val <= 0 or cost_price_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be an integer and prices must be valid positive numbers.")
            return

        try:
            product = Product(
                id=None,
                name=name,
                category=category,
                quantity=quantity_val,
                price=price_val,
                cost_price=cost_price_val
            )
            product.save()
            messagebox.showinfo("Success", f"✅ Product '{name}' saved successfully.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred:\n{e}")



