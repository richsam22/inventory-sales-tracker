import customtkinter as ctk
from tkinter import filedialog, messagebox
import csv
import os
import tempfile
import platform
import subprocess
from datetime import datetime
import pandas as pd
from fpdf import FPDF
from models.sale import Sale
from models.product import Product
import re

class ViewSalesWindow:
    def __init__(self, master, theme="System"):
        self.window = ctk.CTkToplevel(master)
        self.window.title("Sales History")
        self.window.geometry("900x550")
        self.window.resizable(False, False)

        ctk.set_appearance_mode(theme)

        # Title
        title = ctk.CTkLabel(self.window, text="Sales History", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)

        # Filter Row
        filter_frame = ctk.CTkFrame(self.window)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="Search:").pack(side="left", padx=(5, 5))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_sales())
        self.search_entry = ctk.CTkEntry(filter_frame, textvariable=self.search_var, placeholder_text="Type product name...")
        self.search_entry.pack(side="left", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", lambda e: self.on_search_keyrelease())
        self.search_entry.focus_set()

        ctk.CTkLabel(filter_frame, text="Category:").pack(side="left", padx=(5, 5))
        categories = self.get_categories_from_db()
        self.category_var = ctk.StringVar(value="All Categories")
        self.category_menu = ctk.CTkOptionMenu(filter_frame, variable=self.category_var, values=categories,
                                              command=lambda _: self.filter_sales())
        self.category_menu.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(filter_frame, text="From:").pack(side="left", padx=(5, 5))
        self.date_from = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD")
        self.date_from.pack(side="left", padx=5, pady=5)
        self.date_from.bind("<KeyRelease>", lambda e: self.filter_sales())

        ctk.CTkLabel(filter_frame, text="To:").pack(side="left", padx=(5, 5))
        self.date_to = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD")
        self.date_to.pack(side="left", padx=5, pady=5)
        self.date_to.bind("<KeyRelease>", lambda e: self.filter_sales())

        ctk.CTkButton(filter_frame, text="Reset Filters", command=self.reset_filters).pack(side="left", padx=5)

        # Export Row
        export_frame = ctk.CTkFrame(self.window)
        export_frame.pack(fill="x", padx=10, pady=(0, 5))

        ctk.CTkButton(export_frame, text="Export CSV", command=self.export_csv).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(export_frame, text="Export Excel", command=self.export_excel).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(export_frame, text="Export PDF", command=self.export_pdf).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(export_frame, text="Print", command=self.print_sales).pack(side="left", padx=5, pady=5)

        # Scrollable Table Frame
        self.table_frame = ctk.CTkScrollableFrame(self.window, width=850, height=350)
        self.table_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Table Headers
        headers = ["ID", "Product", "Category", "Quantity", "Total", "Date"]
        widths = [50, 180, 140, 100, 100, 180]
        for col, (title, width) in enumerate(zip(headers, widths)):
            header = ctk.CTkLabel(self.table_frame, text=title, font=ctk.CTkFont(weight="bold"))
            header.grid(row=0, column=col, padx=(0 if col == 0 else 10, 0), sticky="w")
            self.table_frame.grid_columnconfigure(col, minsize=width)

        # Load sales
        self.sales_data = Sale.get_all_with_category()
        self.filtered_data = self.sales_data.copy()
        print("Initial sales:", [(s[0], s[1], s[2], s[5]) for s in self.sales_data])
        print("Categories from DB:", categories)
        print("Unique sale categories:", list(set(s[2] for s in self.sales_data if s[2] is not None)))
        self.display_sales(self.sales_data)

    def get_categories_from_db(self):
        categories = Product.get_all_categories()
        return ["All Categories"] + categories

    def on_search_keyrelease(self):
        print("Search input (KeyRelease):", self.search_var.get(), "| Entry text:", self.search_entry.get())
        print("Search entry focused:", self.search_entry.focus_get() == self.search_entry)
        self.filter_sales()

    def reset_filters(self):
        self.search_var.set("")
        self.search_entry.delete(0, "end")
        self.category_var.set("All Categories")
        self.date_from.delete(0, "end")
        self.date_to.delete(0, "end")
        self.filtered_data = self.sales_data.copy()
        print("Filters reset")
        self.display_sales(self.filtered_data)
        self.window.update()

    def is_valid_date(self, date_str):
        """Check if date_str matches YYYY-MM-DD format."""
        if not date_str:
            return True
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str))

    def filter_sales(self):
        search_text = self.search_entry.get().strip().lower()
        category_filter = self.category_var.get().strip()
        from_date = self.date_from.get().strip()
        to_date = self.date_to.get().strip()
        print(f"Applying filters: search='{search_text}', category='{category_filter}', from='{from_date}', to='{to_date}'")

        from_dt = None
        to_dt = None
        if from_date and self.is_valid_date(from_date):
            try:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d")
                print(f"Parsed from_date: {from_dt}")
            except ValueError:
                print(f"Invalid 'from' date: '{from_date}', ignoring date filter")
                from_dt = None
        if to_date and self.is_valid_date(to_date):
            try:
                to_dt = datetime.strptime(to_date, "%Y-%m-%d")
                to_dt = to_dt.replace(hour=23, minute=59, second=59)
                print(f"Parsed to_date: {to_dt}")
            except ValueError:
                print(f"Invalid 'to' date: '{to_date}', ignoring date filter")
                to_dt = None

        filtered = []
        print(f"Total sales data rows: {len(self.sales_data)}")
        if not self.sales_data:
            print("No sales data available")
            messagebox.showinfo("No Results", "No sales data available in the database.")
            self.display_sales(filtered)
            self.window.update()
            return

        for row in self.sales_data:
            try:
                sale_id, product_name, category, quantity, total_price, date = row
                product_name = product_name.strip().lower() if isinstance(product_name, str) and product_name.strip() else ""
                category = category.strip() if isinstance(category, str) and category.strip() else "No Category"
                print(f"Processing sale ID {sale_id}: product='{product_name}', category='{category}', date='{date}', type={type(date)}")

                # Convert date to datetime if it's a string
                if isinstance(date, str):
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y"):
                        try:
                            date = datetime.strptime(date, fmt)
                            print(f"Parsed date for sale ID {sale_id}: {date}")
                            break
                        except ValueError:
                            continue
                    else:
                        print(f"Warning: Could not parse date '{date}' for sale ID {sale_id}, including anyway")
                        date = None

                # Apply filters
                if search_text and product_name and search_text not in product_name:
                    print(f"Skipping sale ID {sale_id}: product '{product_name}' does not match search '{search_text}'")
                    continue
                if category_filter != "All Categories" and category != category_filter:
                    print(f"Skipping sale ID {sale_id}: category '{category}' does not match filter '{category_filter}'")
                    continue
                if from_dt and date and date < from_dt:
                    print(f"Skipping sale ID {sale_id}: date {date} is before {from_dt}")
                    continue
                if to_dt and date and date > to_dt:
                    print(f"Skipping sale ID {sale_id}: date {date} is after {to_dt}")
                    continue

                filtered.append((sale_id, product_name.title() if product_name else "", category, quantity, total_price, date))
                print(f"Including sale ID {sale_id}")
            except Exception as e:
                print(f"Error processing sale ID {sale_id}: {e}")
                continue

        print(f"Filtered rows: {len(filtered)}")
        if not filtered:
            print("No sales matched filters. Check data formats and filter values.")
            messagebox.showinfo("No Results", "No sales match the applied filters. Check your filters or database data.")
        self.filtered_data = filtered
        self.display_sales(filtered)
        self.window.update()

    def display_sales(self, sales_list):
        for widget in self.table_frame.winfo_children():
            if widget.grid_info().get("row", 0) != 0:
                widget.destroy()

        if not sales_list:
            ctk.CTkLabel(self.table_frame, text="No sales data available", text_color="red").grid(row=1, column=0, columnspan=6, pady=10)
            return

        for i, row in enumerate(sales_list, start=1):
            sale_id, product_name, category, quantity, total_price, date = row
            date_str = date.strftime("%Y-%m-%d") if isinstance(date, datetime) else str(date) if date else "Unknown"
            values = [sale_id, product_name, category, quantity, total_price, date_str]
            for j, value in enumerate(values):
                label = ctk.CTkLabel(self.table_frame, text=str(value))
                label.grid(row=i, column=j, padx=5, pady=2, sticky="w")

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Product", "Category", "Quantity", "Total", "Date"])
            for row in self.filtered_data:
                row = list(row)
                row[5] = row[5].strftime("%Y-%m-%d") if isinstance(row[5], datetime) else str(row[5]) if row[5] else "Unknown"
                writer.writerow(row)
        messagebox.showinfo("Export", "CSV export successful!")

    def export_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if not file_path:
            return
        df = pd.DataFrame(self.filtered_data, columns=["ID", "Product", "Category", "Quantity", "Total", "Date"])
        df["Date"] = df["Date"].apply(lambda x: x.strftime("%Y-%m-%d") if isinstance(x, datetime) else str(x) if x else "Unknown")
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Export", "Excel export successful!")

    def export_pdf(self, file_path=None):
        if file_path is None:
            file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
            if not file_path:
                return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, "Sales Report", ln=True, align="C")
        pdf.ln(10)
        col_widths = [15, 40, 35, 20, 25, 60]
        row_height = 8
        pdf.set_fill_color(200, 200, 200)
        headers = ["ID", "Product", "Category", "Qty", "Total", "Date"]
        for w, header in zip(col_widths, headers):
            pdf.cell(w, row_height, header, border=1, fill=True)
        pdf.ln(row_height)
        for row in self.filtered_data:
            for w, item in zip(col_widths, row):
                item = item.strftime("%Y-%m-%d") if isinstance(item, datetime) else str(item) if item else "Unknown"
                pdf.cell(w, row_height, str(item), border=1)
            pdf.ln(row_height)
        pdf.output(file_path)
        messagebox.showinfo("Export Successful", f"Sales exported to {file_path}")

    def print_sales(self):
        temp_dir = tempfile.gettempdir()
        temp_pdf = os.path.join(temp_dir, "temp_sales_invoice.pdf")
        self.export_pdf(temp_pdf)
        if platform.system() == "Windows":
            os.startfile(temp_pdf, "print")
        elif platform.system() == "Darwin":
            subprocess.run(["open", temp_pdf])
        else:
            subprocess.run(["xdg-open", temp_pdf])

