import customtkinter as ctk
from tkinter import messagebox
from models.product import Product
from models.sale import Sale

class SellProductWindow:
    def __init__(self, master, theme="System"):
        self.window = ctk.CTkToplevel(master)
        self.window.title("Sell Product")
        self.window.geometry("420x360")
        self.window.resizable(False, False)
        
        ctk.set_appearance_mode(theme)

        # Load products and create dictionary
        self.products = Product.get_all()
        self.product_dict = {f"{p.name} (Stock: {p.quantity})": p for p in self.products}

        # Title
        ctk.CTkLabel(self.window, text="Sell Product", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        # Product Selector
        ctk.CTkLabel(self.window, text="Select Product:").pack(pady=5)
        self.product_combo = ctk.CTkComboBox(self.window, values=list(self.product_dict.keys()), command=self.update_total)
        self.product_combo.pack(pady=5, fill="x", padx=40)

        # Quantity Entry
        ctk.CTkLabel(self.window, text="Quantity to Sell:").pack(pady=(15, 5))
        self.qty_entry = ctk.CTkEntry(self.window)
        self.qty_entry.pack(pady=5, fill="x", padx=40)
        self.qty_entry.bind("<KeyRelease>", self.update_total)

        # Total Display
        self.total_label = ctk.CTkLabel(self.window, text="Total: ₦0.00", font=ctk.CTkFont(size=14))
        self.total_label.pack(pady=15)

        # Sell Button
        ctk.CTkButton(self.window, text="Sell Product", command=self.sell_product).pack(pady=10)

    def update_total(self, event=None):
        try:
            selected = self.product_dict.get(self.product_combo.get())
            qty = int(self.qty_entry.get())
            total = selected.price * qty
            self.total_label.configure(text=f"Total: ₦{total:.2f}")
        except:
            self.total_label.configure(text="Total: ₦0.00")

    def sell_product(self):
        try:
            selected_text = self.product_combo.get()
            product = self.product_dict.get(selected_text)
            qty = int(self.qty_entry.get())

            if not product:
                raise ValueError("Please select a valid product.")

            if qty <= 0:
                raise ValueError("Quantity must be greater than 0.")

            if qty > product.quantity:
                raise ValueError("Not enough stock available.")

            # Update product quantity
            new_qty = product.quantity - qty
            Product.update_quantity(product.id, new_qty)

            # Record the sale
            total = product.price * qty
            Sale.add(product.id, qty, total)

            messagebox.showinfo("Success", f"Sold {qty} units of {product.name} for ₦{total:.2f}")
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e))


            
    
