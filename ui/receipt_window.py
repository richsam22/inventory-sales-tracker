import customtkinter as ctk
from tkinter import messagebox, filedialog
import tempfile, os, platform, subprocess, json
from fpdf import FPDF

# --------- Printer Config Helpers ---------
CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "printer_config.json"))

def load_default_printer():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("default_printer")
    except Exception:
        pass
    return None

def save_default_printer(name):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"default_printer": name}, f)
    except Exception:
        pass

def list_printers_unix():
    try:
        out = subprocess.check_output(["lpstat", "-p"], text=True, stderr=subprocess.DEVNULL)
        return [line.split()[1] for line in out.splitlines() if line.startswith("printer")]
    except Exception:
        return []

def get_system_default_unix():
    try:
        out = subprocess.check_output(["lpstat", "-d"], text=True, stderr=subprocess.DEVNULL).strip()
        if ":" in out:
            return out.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


# --------- Cross-platform printing ---------
def print_receipt_pdf(pdf_path, parent):
    system = platform.system()

    if system == "Windows":
        try:
            os.startfile(pdf_path, "print")
            messagebox.showinfo("Print", "Sent to default printer.")
            return
        except Exception:
            try:
                import win32api, win32print
                default = win32print.GetDefaultPrinter()
                if default:
                    win32api.ShellExecute(0, "print", pdf_path, None, ".", 0)
                    messagebox.showinfo("Print", f"Sent to printer: {default}")
                    return
            except Exception:
                pass
        messagebox.showerror("Print Error", "No default printer found. Please configure one.")
        return

    else:
        saved = load_default_printer()
        if saved:
            try:
                subprocess.run(["lp", "-d", saved, pdf_path], check=True)
                messagebox.showinfo("Print", f"Sent to printer: {saved}")
                return
            except Exception:
                pass

        sys_default = get_system_default_unix()
        if sys_default:
            try:
                subprocess.run(["lp", pdf_path], check=True)
                messagebox.showinfo("Print", f"Sent to system default printer: {sys_default}")
                return
            except Exception:
                pass

        printers = list_printers_unix()
        if not printers:
            messagebox.showerror("Print Error", "No printers found. Please configure a printer.")
            return

        picker = ctk.CTkToplevel(parent)
        picker.title("Select Printer")
        picker.geometry("360x180")
        picker.resizable(False, False)

        ctk.CTkLabel(picker, text="Choose printer:").pack(pady=(12, 6))
        var = ctk.StringVar(value=printers[0])
        ctk.CTkOptionMenu(picker, values=printers, variable=var).pack(pady=6, padx=12, fill="x")

        remember = ctk.BooleanVar()
        ctk.CTkCheckBox(picker, text="Set as default", variable=remember).pack(pady=8)

        def do_print():
            printer = var.get()
            if remember.get():
                save_default_printer(printer)
            try:
                subprocess.run(["lp", "-d", printer, pdf_path], check=True)
                messagebox.showinfo("Print", f"Sent to printer: {printer}")
            except Exception as e:
                messagebox.showerror("Print Error", str(e))
            picker.destroy()

        ctk.CTkButton(picker, text="Print", command=do_print).pack(pady=10)


# --------- Receipt Window ---------
class ReceiptWindow:
    def __init__(self, master, sale_data, theme="System"):
        """
        sale_data = {
            "id": 123,
            "date": "...",
            "items": [
                {"product": "Coke", "quantity": 2, "price": 200.0, "total": 400.0},
                {"product": "Bread", "quantity": 1, "price": 500.0, "total": 500.0}
            ],
            "grand_total": 900.0
        }
        """
        self.sale_data = sale_data
        self.window = ctk.CTkToplevel(master)
        self.window.title("🧾 Receipt")
        self.window.geometry("420x520")
        self.window.resizable(False, False)
        ctk.set_appearance_mode(theme)

        ctk.CTkLabel(self.window, text="🧾 Sales Receipt",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=12)

        # Receipt text
        self.receipt_text = self._build_text()

        # Textbox
        box_frame = ctk.CTkFrame(self.window, corner_radius=12)
        box_frame.pack(padx=16, pady=10, fill="both", expand=True)
        tb = ctk.CTkTextbox(box_frame, wrap="word")
        tb.pack(padx=8, pady=8, fill="both", expand=True)
        tb.insert("1.0", self.receipt_text)
        tb.configure(state="disabled")

        # Buttons
        btns = ctk.CTkFrame(self.window, fg_color="transparent")
        btns.pack(pady=10)
        ctk.CTkButton(btns, text="🖨 Print", command=self.print_receipt, width=120).grid(row=0, column=0, padx=8)
        ctk.CTkButton(btns, text="💾 Save PDF", command=self.save_pdf, width=120).grid(row=0, column=1, padx=8)
        ctk.CTkButton(btns, text="💾 Save TXT", command=self.save_txt_dialog, width=120).grid(row=1, column=0, columnspan=2, pady=(8, 0))

    def _build_text(self):
        lines = [
            "Iventory & Sales Tracker",
            "Address / Phone (optional)",
            "----------------------------------------",
            f"Sale ID: {self.sale_data.get('id')}",
            f"Date: {self.sale_data.get('date')}",
            "----------------------------------------",
            f"{'Product':20} {'Qty':>3} {'Price':>10} {'Total':>10}",
            "----------------------------------------",
        ]

        for item in self.sale_data.get("items", []):
            product = item.get("product")
            qty = item.get("quantity")
            price = item.get("price")
            total = item.get("total")
            lines.append(f"{product:20} {qty:>3} ₦{price:>9,.2f} ₦{total:>9,.2f}")

        lines += [
            "----------------------------------------",
            f"GRAND TOTAL: ₦{self.sale_data.get('grand_total'):,.2f}",
            "",
            "Thank you for your purchase!"
        ]
        return "\n".join(lines)

    # ---------- PDF & TXT ----------
    def _font_paths(self):
        base = os.path.join(os.path.dirname(__file__), "fonts")
        return {
            "regular": os.path.join(base, "DejaVuSans.ttf"),
            "bold": os.path.join(base, "DejaVuSans-Bold.ttf"),
            "italic": os.path.join(base, "DejaVuSans-Oblique.ttf"),
        }

    def save_pdf(self, file_path=None):
        try:
            if not self.sale_data or "items" not in self.sale_data:
                raise ValueError("No receipt data available.")

            items = self.sale_data.get("items", [])
            grand_total = float(self.sale_data.get("grand_total", 0.0) or 0.0)
            receipt_id = self.sale_data.get("id", "N/A")
            receipt_date = self.sale_data.get("date", "N/A")

            if not items:
                raise ValueError("No items in the receipt to save.")

            # If no path provided, ask user
            if not file_path:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")]
                )
                if not file_path:
                    return  # User cancelled

            pdf = FPDF()
            pdf.add_page()

            # Title
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Receipt", ln=True, align="C")
            pdf.ln(5)

            # Receipt details
            pdf.set_font("Arial", "", 12)
            pdf.cell(100, 10, f"Receipt ID: {receipt_id}", ln=True)
            pdf.cell(100, 10, f"Date: {receipt_date}", ln=True)
            pdf.ln(5)

            # Table headers
            pdf.set_font("Arial", "B", 12)
            pdf.cell(50, 10, "Product", 1)
            pdf.cell(30, 10, "Qty", 1, align="C")
            pdf.cell(40, 10, "Price", 1, align="R")
            pdf.cell(40, 10, "Total", 1, align="R")
            pdf.ln()

            # Items
            pdf.set_font("Arial", "", 12)
            for item in items:
                name = str(item.get("product", "N/A"))
                qty = str(item.get("quantity", 0))
                price = float(item.get("price") or 0)
                total = float(item.get("total") or 0)

                pdf.cell(50, 10, name, 1)
                pdf.cell(30, 10, qty, 1, align="C")
                pdf.cell(40, 10, f"{price:.2f}", 1, align="R")
                pdf.cell(40, 10, f"{total:.2f}", 1, align="R")
                pdf.ln()

            # Grand total
            pdf.set_font("Arial", "B", 12)
            pdf.cell(120, 10, "Grand Total", 1)
            pdf.cell(40, 10, f"{grand_total:.2f}", 1, align="R")

            pdf.output(file_path)
            messagebox.showinfo("Success", f"Receipt saved as {file_path}")

        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF:\n{e}")


    def save_pdf_dialog(self):
        file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not file: 
            return
        try:
            self.save_pdf(file)
            messagebox.showinfo("Saved", f"PDF saved:\n{file}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def save_txt_dialog(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if not file:
            return
        try:
            # ✅ if receipt_text is CTkTextbox
            if hasattr(self.receipt_text, "get"):
                receipt_content = self.receipt_text.get("1.0", "end-1c")
            else:
                # ✅ if receipt_text is just a string
                receipt_content = str(self.receipt_text)

            with open(file, "w", encoding="utf-8") as f:
                f.write(receipt_content)

            messagebox.showinfo("Saved", f"TXT saved:\n{file}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def print_receipt(self):
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            self.save_pdf(tmp.name)   # ✅ now works
            print_receipt_pdf(tmp.name, self.window)
        except Exception as e:
            messagebox.showerror("Print Error", str(e))




