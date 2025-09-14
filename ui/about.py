import customtkinter as ctk

class AboutWindow(ctk.CTkToplevel):
    def __init__(self, parent, app_version, theme="System"):
        super().__init__(parent)
        self.title("About / Instructions")
        self.geometry("600x500")
        self.resizable(False, False)
        
        ctk.set_appearance_mode(theme)

        # Main Frame
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text=f"📦 Inventory & Sales Tracker {app_version}",
            font=("Arial Bold", 18)
        )
        title_label.pack(pady=(15, 10))

        # Scrollable Instructions
        textbox = ctk.CTkTextbox(main_frame, wrap="word", font=("Arial", 13), activate_scrollbars=True)
        textbox.pack(fill="both", expand=True, padx=15, pady=15)

        about_text = f"""
Welcome to Inventory & Sales Tracker {app_version}

━━━━━━━━━━━━━━━━━━━━━━━━━━
Features:
- Manage Products (Add, Edit, Delete, View)
- Record Sales with automatic stock updates
- Track Profits & Revenue in real time
- Export Data (CSV, Excel, PDF)
- Low Stock Alerts
- Generate & Print Receipts
- Dashboard overview with charts
━━━━━━━━━━━━━━━━━━━━━━━━━━

Instructions:
1. Add Products via 'Add Product'
2. Record Sales via 'Record Product'
2. Sale Product via 'Sell Product'
3. View Products and Sales in their sections
4. Use Settings to customize preferences
5. Use Search & Filter to find records
━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍💻 Developer:
SaenTechy

📧 Support Contact:
saentechy@gmail.com

© {app_version} Inventory Tracker. All rights reserved.
"""

        textbox.insert("0.0", about_text)
        textbox.configure(state="disabled")  # Make read-only
