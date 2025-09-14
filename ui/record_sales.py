import customtkinter as ctk
from tkinter import messagebox
from models.product import Product
from models.sale import Sale
from datetime import datetime
from ui.receipt_window import ReceiptWindow

class RecordSaleWindow:
    def __init__(self, master, theme="System"):
        self.window = ctk.CTkToplevel(master)
        self.window.title("Record Sale")
        self.window.geometry("600x600")

        ctk.set_appearance_mode(theme)

        # ---- MAIN SCROLLABLE FRAME ----
        self.scroll_frame = ctk.CTkScrollableFrame(self.window)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # -------- UI Content --------
        ctk.CTkLabel(
            self.scroll_frame,
            text="🛒 Record New Sale",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=15)

        # Vars
        self.selected_product = None
        self.selected_product_var = ctk.StringVar()
        self.price_var = ctk.StringVar(value="0.00")
        self.quantity_var = ctk.StringVar()
        self.total_var = ctk.StringVar(value="0.00")
        self.cart = []

        # Load products
        self.products = Product.get_all()
        product_names = [f"{p.name} (Stock: {p.quantity})" for p in self.products]
        self.product_dict = {f"{p.name} (Stock: {p.quantity})": p for p in self.products}
        print("Loaded products:", [(p.name, p.price, p.quantity) for p in self.products])

        # Form
        form = ctk.CTkFrame(self.scroll_frame, corner_radius=15)
        form.pack(padx=30, pady=10, fill="x")

        ctk.CTkLabel(form, text="Select Product:").pack(anchor="w", pady=(10, 0))
        self.product_dropdown = ctk.CTkOptionMenu(
            form,
            variable=self.selected_product_var,
            values=product_names,
            command=self.on_product_selected
        )
        self.product_dropdown.pack(fill="x", pady=5)
        
        # Preselect first product if available
        if product_names:
            self.selected_product_var.set(product_names[0])
            self.on_product_selected(product_names[0])

        self.price_entry = ctk.CTkLabel(form, text="Price per Unit: ", font=ctk.CTkFont(size=16, weight="bold"))
        self.price_entry.pack(anchor="w", pady=5)
        

        ctk.CTkLabel(form, text="Quantity:").pack(anchor="w", pady=(10, 0))
        self.quantity_entry = ctk.CTkEntry(form, textvariable=self.quantity_var)
        self.quantity_entry.pack(fill="x", pady=5)
        self.quantity_trace_id = self.quantity_var.trace_add("write", lambda *args: self.calculate_total())
        self.quantity_entry.bind("<KeyRelease>", lambda e: self.calculate_total())

        ctk.CTkButton(form, text="➕ Add to Cart", command=self.add_to_cart).pack(pady=10)

        # Cart area
        ctk.CTkLabel(
            self.scroll_frame,
            text="🛍️ Cart Items",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack()
        self.cart_frame = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
        self.cart_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.cart_listbox = ctk.CTkTextbox(self.cart_frame, height=200, width=500)
        self.cart_listbox.pack(padx=10, pady=10, fill="both", expand=True)
        self.cart_listbox.configure(state="disabled")
         
         
        # Total
        self.total_entry = ctk.CTkLabel(self.scroll_frame, text="Total: ₦0.00", font=ctk.CTkFont(size=14))
        self.total_entry.pack(pady=5)

        # Save button
        ctk.CTkButton(
            self.scroll_frame,
            text="💾 Save Sale",
            command=self.save_sale
        ).pack(pady=15)

    def on_product_selected(self, selection):
        """Update price when product is chosen"""
        print(f"Selected product: {selection}")
        product = self.product_dict.get(selection)
        if product:
            self.selected_product = product
            try:
                price = float(product.price) if product.price is not None else 0.0
                self.price_var.set(f"{price:.2f}")
                print(f"Set price to: {self.price_var.get()}")
            except (ValueError, TypeError) as e:
                print(f"Invalid price for {product.name}: {product.price}, error: {e}")
                self.price_var.set("0.00")
            self.calculate_total()
            self.window.update()  # Force UI refresh
        else:
            self.price_var.set("0.00")
            self.total_var.set("0.00")
            print("No product selected, resetting price and total")
            self.window.update()

    def calculate_total(self, *args):
        """Auto-calculate total safely"""
        try:
            if not hasattr(self, 'quantity_entry') or not self.quantity_entry.winfo_exists():
                print("Warning: quantity_entry not available yet")
                self.total_var.set("")
                return

            qty_str = self.quantity_entry.get().strip()
            print(f"Calculating total: qty_str='{qty_str}', price='{self.price_var.get()}'")
            if not qty_str or not qty_str.isdigit() or int(qty_str) <= 0:
                self.total_var.set("0.00")
                return

            qty = int(qty_str)
            price = float(self.price_var.get()) if self.price_var.get() and self.price_var.get() != "0.00" else 0.0
            total = qty * price
            self.total_var.set(f"{total:,.2f}")
            self.price_entry.configure(text=f"Price per Unit: ₦{total:,.2f}")
            print(f"Total set to: {self.total_var.get()}")
            self.window.update()  # Force UI refresh
        except Exception as e:
            print(f"Error in calculate_total: {e}")
            self.total_var.set("0.00")
            self.window.update()

    def add_to_cart(self):
        try:
            if not self.selected_product:
                raise ValueError("No product selected.")

            qty_str = self.quantity_entry.get().strip()
            print(f"Add to cart: qty_str='{qty_str}', product={self.selected_product.name if self.selected_product else 'None'}")
            if not qty_str or not qty_str.isdigit():
                raise ValueError("Quantity must be a positive integer.")

            qty = int(qty_str)
            if qty <= 0:
                raise ValueError("Quantity must be a positive integer.")
            if qty > self.selected_product.quantity:
                raise ValueError(f"Not enough stock available for {self.selected_product.name}. Available: {self.selected_product.quantity}")

            price = float(self.price_var.get() or 0)
            total = qty * price

            self.cart.append({
                "product": self.selected_product,
                "quantity": qty,
                "price": price,
                "total": total
            })

            self.refresh_cart()  # Update cart and total
            # Temporarily disable trace to avoid recalculation with empty qty
            self.quantity_var.trace_remove("write", self.quantity_trace_id)
            self.quantity_entry.delete(0, "end")
            self.quantity_var.set("")
            self.quantity_trace_id = self.quantity_var.trace_add("write", lambda *args: self.calculate_total())
            print(f"Added to cart: {self.selected_product.name}, qty={qty}, total={total}")

        except ValueError as ve:
            print(f"ValueError in add_to_cart: {ve}")
            messagebox.showerror("Input Error", str(ve))
        except Exception as e:
            print(f"Error in add_to_cart: {e}")
            messagebox.showerror("Error", f"An error occurred:\n{e}")

    def refresh_cart(self):
        self.cart_listbox.configure(state="normal")
        self.cart_listbox.delete("1.0", "end")

        total_sum = 0.0
        for item in self.cart:
            line = f"{item['product'].name} x{item['quantity']} @ {item['price']:.2f} = {item['total']:.2f}\n"
            self.cart_listbox.insert("end", line)
            total_sum += item["total"]
            self.total_entry.configure(text=f"Total: ₦{total_sum:,.2f}")

        self.cart_listbox.configure(state="disabled")
        self.total_var.set(f"{total_sum:,.2f}")  # Update total from cart
        print(f"Cart refreshed, total: {total_sum}")
        self.window.update()
    
    def save_sale(self):
        try:
            if not self.cart:
                raise ValueError("Cart is empty. Please add products before saving.")

            from models.transactions import create_transaction, finalize_transaction
            from models.sale import Sale
            from models.product import Product

            transaction_id = create_transaction()
            sale_records = []

            for item in self.cart:
                product = item["product"]
                qty = item["quantity"]
                price = item["price"]
                total = item["total"]

                if qty > product.quantity:
                    raise ValueError(f"Not enough stock for {product.name}. Available: {product.quantity}")

                profit = (price - (product.cost_price or 0)) * qty

                sale_id = Sale.add(
                    product_id=product.id,
                    quantity_sold=qty,
                    total_price=total,
                    profit=profit,
                    transaction_id=transaction_id
                )

                Product.update_quantity(product.id, product.quantity - qty)

                sale_records.append({
                    "product": product.name,
                    "quantity": qty,
                    "price": price,
                    "total": total
                })

            grand_total = finalize_transaction(transaction_id)
            from models.transactions import get_transaction_details
            transaction = get_transaction_details(transaction_id)

            ReceiptWindow(
                self.window,
                sale_data={
                    "id": transaction_id,
                    "date": transaction["timestamp"],
                    "items": sale_records,
                    "grand_total": grand_total
                }
            )
            self.window.withdraw()

        except ValueError as ve:
            print(f"ValueError in save_sale: {ve}")
            messagebox.showerror("Input Error", str(ve))
        except Exception as e:
            print(f"Error in save_sale: {e}")
            messagebox.showerror("Error", f"An error occurred:\n{e}")
