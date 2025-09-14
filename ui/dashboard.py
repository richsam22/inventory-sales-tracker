import customtkinter as ctk
import tkinter.messagebox as mb
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.add_product import AddProductWindow
from ui.view_products import ViewProductsWindow
from ui.sell_product import SellProductWindow
from ui.view_sales import ViewSalesWindow
from ui.record_sales import RecordSaleWindow
from ui.settings import SettingsWindow
from ui.manage_staff import ManageStaffWindow
from ui.about import AboutWindow
from models.product import Product
from models.sale import Sale
from matplotlib import pyplot as plt
from PIL import Image
from utils.path_helper import resource_path

DASHBOARD_LOGO = ctk.CTkImage(light_image=Image.open(resource_path("assets/inventory_logo.png")),
                              dark_image=Image.open(resource_path("assets/inventory_logo.png")),
                              size=(200, 200))


class Dashboard(ctk.CTkToplevel):
    def __init__(self, parent, username, role, app_version):
        super().__init__(parent)
        self.title("📊 Inventory & Sales Tracker")
        self.geometry("900x650")
        self.current_theme = "System"
        self.username = username
        self.role = role
        self.app_version = app_version

        

        # Theme Setup
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme("blue")
        self.configure(bg=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

        # Main scrollable frame
        self.frame = ctk.CTkScrollableFrame(master=self, height=600, corner_radius=10)
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        
        self.logo_label = ctk.CTkLabel(self.frame, image=DASHBOARD_LOGO, text="")
        self.logo_label.pack(pady=(0, 0))
        
        # Title
        ctk.CTkLabel(
            master=self.frame,
            text=f"📦 Inventory & Sales Tracker {app_version}",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(0, 5))
        
        # Title
        self.welcome = ctk.CTkLabel(
            master=self.frame,
            text=f"Welcome {username} ({role})",
            font=ctk.CTkFont(size=15)
        )
        self.welcome.pack(pady=(0, 15))
        
        self.welcome = ctk.CTkLabel(
            master=self.frame,
            text="Choose an action below 👇",
            font=ctk.CTkFont(size=15)
        )
        self.welcome.pack(pady=(0, 15))
        
        # Theme Selector
        ctk.CTkLabel(master=self.frame, text="🌓 Theme Mode:", anchor="w").pack(padx=20, fill="x")
        self.theme_selector = ctk.CTkOptionMenu(
            master=self.frame,
            values=["System", "Light", "Dark"],
            command=self.change_theme
        )
        self.theme_selector.set(self.current_theme)
        self.theme_selector.pack(pady=(0, 15), padx=20, fill="x")

        # --- OVERVIEW METRICS FRAME ---
        self.overview_frame = ctk.CTkFrame(master=self.frame, corner_radius=8)
        self.overview_frame.pack(pady=5, padx=20, fill="x")

        for i in range(5):
            self.overview_frame.grid_columnconfigure(i, weight=1)

        # Metric Cards
        self.total_products_card = self.create_metric_card("🧮 Products\n0")
        self.total_sales_card = self.create_metric_card("💰 Sales\n0")
        self.best_seller_card = self.create_metric_card("🏆 Best Seller:\nN/A", width=240)
        self.total_revenue_card = self.create_metric_card("📈 Revenue\n₦0", width=180)
        self.profit_card = self.create_metric_card("💰 Total Profit\n₦0", fg_color="#4CAF50", width=140)

        self.total_products_card.grid(row=0, column=0, padx=5, pady=5)
        self.total_sales_card.grid(row=0, column=1, padx=5, pady=5)
        self.best_seller_card.grid(row=0, column=2, padx=5, pady=5)
        self.total_revenue_card.grid(row=0, column=3, padx=5, pady=5)
        self.profit_card.grid(row=0, column=4, padx=5, pady=5, sticky="nsew")

        # --- BUTTONS FRAME ---
        self.buttons_frame = ctk.CTkFrame(master=self.frame, corner_radius=8)
        self.buttons_frame.pack(pady=10, padx=20, fill="x")
        self.create_action_buttons()
        
            
        if self.role == "admin":
            btn = ctk.CTkButton(self.buttons_frame, text="👥 Manage Staff", command=self.manage_staff)
            btn.pack(pady=6, fill="x", padx=10)


        # --- SALES CHART ---
        self.chart_frame = ctk.CTkFrame(master=self.frame, corner_radius=8, height=400)
        self.chart_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.create_chart_frame()

        # Load metrics
        self.update_overview()
        self.check_low_stock()
        
        # Bottom exit button
        bottom_frame = ctk.CTkFrame(master=self.frame, corner_radius=8)
        bottom_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(bottom_frame, text="🚪 Exit App", fg_color="gray", command=self.destroy).pack(pady=6, fill="x", padx=10)

    # ----- HELPER METHODS -----
    def create_metric_card(self, text, fg_color="gray20", width=100):
        card = ctk.CTkLabel(
            self.overview_frame,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            fg_color=fg_color,
            text_color="white",
            width=width,
            height=60
        )
        return card

    def create_action_buttons(self):
        self.buttons = {}  # store references here

        actions = [
            ("📦 View Products", self.view_products, "view_products"),
            ("➕ Add Product", self.add_product, "add_product"),
            ("🛒 Sell Product", self.sell_product, "sell_product"),
            ("📝 Record Sale", self.record_sale, "record_sale"),
            ("📈 View Sales", self.view_sales, "view_sales"),
            ("⚙️ Settings", self.settings, "settings"),
            ("About", self.about, "About")
        ]

        for text, cmd, key in actions:
            # Restrict staff
            if self.role == "staff" and text in ["➕ Add Product", "⚙️ Settings"]:
                continue  
            
            btn = ctk.CTkButton(self.buttons_frame, text=text, command=cmd)
            btn.pack(pady=6, fill="x", padx=10)

            # hover effects
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg_color="#1E90FF"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(
                fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"]
            ))

            # save reference
            self.buttons[key] = btn


    # ----- THEME -----
    def change_theme(self, new_theme):
        self.current_theme = new_theme
        for i in range(10, -1, -1):
            self.attributes("-alpha", i/10)
            self.update()
            self.after(5)
        ctk.set_appearance_mode(new_theme)
        for i in range(0, 11):
            self.attributes("-alpha", i/10)
            self.update()
            self.after(5)

    # ----- OVERVIEW METRICS -----
    def update_overview(self):
        products = Product.get_all()
        sales = Sale.get_all()

        self.animate_card_value(self.total_products_card, f"🧮 Products\n{len(products)}")
        self.animate_card_value(self.total_sales_card, f"💰 Sales\n{len(sales)}")
        total_revenue = sum(s[3] for s in sales)
        self.animate_card_value(self.total_revenue_card, f"📈 Revenue\n₦{total_revenue:,.2f}")
        
        # Highlight low stock products
        self.highlight_low_stock()

        best_seller_data = Sale.get_best_selling_product()
        if best_seller_data:
            _, product_name, qty_sold, revenue = best_seller_data
            self.animate_card_value(self.best_seller_card,
                                    f"🏆 Best Seller\n{product_name} ({qty_sold} sold, ₦{revenue:,.2f})")
        else:
            self.animate_card_value(self.best_seller_card, "🏆 Best Seller: N/A")

        total_profit = Sale.get_total_profit()
        self.animate_card_value(self.profit_card, f"💰 Total Profit\n₦{total_profit:,.2f}")
    
        # --- ANIMATED CARD UPDATE ---
    # def animate_card_value(self, card, new_text, steps=5):
    #     # Slide-in + fade effect
    #     original_x = card.winfo_x()
    #     card.place(x=-200, y=card.winfo_y())
    #     card.configure(text=new_text)

    #     def animate(step=0):
    #         if step > steps:
    #             card.place(x=original_x)
    #             return
    #         alpha = step / steps
    #         x_pos = int(-200 + (original_x + 200) * alpha)
    #         card.place(x=x_pos)
    #         self.root.after(20, lambda: animate(step + 1))

    #     animate()
    
    def animate_card_value(self, card, new_text, steps=5):
            # Slide-in + fade effect
        original_x = card.winfo_x()
        card.configure(text=new_text)
        card.after(0, lambda: card.configure(fg_color="#0077CC"))
        
        
        def animate(step=0):
            if step > steps:
                card.place(x=original_x)
                return
            alpha = step / steps
            x_pos = int(-200 + (original_x + 200) * alpha)
            card.place(x=x_pos)
            self.after(20, lambda: animate(step + 1))

        animate()

    def highlight_low_stock(self):
        LOW_STOCK_THRESHOLD = 5
        low_stock = any(p.quantity < LOW_STOCK_THRESHOLD for p in Product.get_all())
        if low_stock:
            self.total_products_card.configure(fg_color="#FF4500")
        else:
            self.total_products_card.configure(fg_color="gray20")

    # ----- CHART -----
    def create_chart_frame(self):
        self.chart_type_var = ctk.StringVar(value="Pie")

        top_frame = ctk.CTkFrame(self.chart_frame)
        top_frame.pack(fill="x", pady=5)

        chart_selector = ctk.CTkOptionMenu(
            top_frame,
            values=["Pie", "Doughnut", "Line", "Area", "Bar"],
            variable=self.chart_type_var,
            command=lambda _: self.refresh_chart()
        )
        chart_selector.pack(pady=5)

        self.chart_display_frame = ctk.CTkFrame(self.chart_frame)
        self.chart_display_frame.pack(fill="both", expand=True)
        self.refresh_chart()
        
    
    def create_sales_chart(self):
        for widget in self.chart_display_frame.winfo_children():
            widget.destroy()

        sales_data = Sale.get_sales_summary_per_product()
        if not sales_data:
            ctk.CTkLabel(self.chart_display_frame, text="No sales data available").pack(pady=10)
            return

        product_names = [row[0] for row in sales_data]
        quantities = [row[1] for row in sales_data]

        colors = ["#1E1EFF", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]

        fig = Figure(figsize=(5, 4), dpi=111)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor(None)
        ax.set_facecolor("#DBE9FA" if self.current_theme != "Dark" else "#1E1E1E")

        chart_type = self.chart_type_var.get()

        if chart_type == "Pie":
            ax.pie(quantities, labels=product_names, autopct="%1.1f%%", colors=colors)
            ax.set_title("Sales Distribution", color="#FFEF00")
        elif chart_type == "Doughnut":
            wedges, texts, autotexts = ax.pie(quantities, labels=product_names, autopct="%1.1f%%", colors=colors)
            centre_circle = plt.Circle((0, 0), 0.70, fc=None)
            fig.gca().add_artist(centre_circle)
            ax.set_title("Sales Doughnut", color="#FFEF00")
        elif chart_type == "Line":
            ax.plot(product_names, quantities, marker="o", color="#1e90ff", linewidth=2)
            ax.set_title("Sales Over Products", color="#FFEF00")
        elif chart_type == "Area":
            ax.fill_between(product_names, quantities, color="#1e90ff", alpha=0.4)
            ax.plot(product_names, quantities, marker="o", color="#1e90ff")
            ax.set_title("Sales Area Chart", color="#FFEF00")
        elif chart_type == "Bar":
            ax.bar(product_names, quantities, color=colors)
            ax.set_title("Sales per Product", color="#FFEF00")

        ax.set_xlabel("Product", color="#FFEF00")
        ax.set_ylabel("Quantity Sold", color="#FFEF00")
        ax.tick_params(axis='x', rotation=20, colors="#FFFFFF" if self.current_theme=="Dark" else "#000000")
        ax.tick_params(axis='y', colors="#FFFFFF" if self.current_theme=="Dark" else "#000000")

        canvas = FigureCanvasTkAgg(fig, master=self.chart_display_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        

    def refresh_chart(self):
        self.create_sales_chart()

    # ----- LOW STOCK ALERT -----
    def check_low_stock(self):
        LOW_STOCK_THRESHOLD = 5
        low_stock_items = [(p.name, p.quantity) for p in Product.get_all() if p.quantity < LOW_STOCK_THRESHOLD]
        if low_stock_items:
            items_list = "\n".join([f"{name} ({qty} left)" for name, qty in low_stock_items])
            mb.showwarning(title="Low Stock Alert", message=f"The following items are low in stock:\n\n{items_list}")

    # ----- ACTION WINDOWS -----
    def view_products(self): ViewProductsWindow(self, self.current_theme, role=self.role)
    
    def add_product(self):
        win = AddProductWindow(self, self.current_theme)
        self.wait_window(win)
        self.update_overview()
        self.refresh_chart()
        
    def sell_product(self):
        win = SellProductWindow(self, self.current_theme)
        self.wait_window(win.window)
        self.update_overview()
        self.refresh_chart()
        
    def record_sale(self):
        win = RecordSaleWindow(self, self.current_theme)
        self.wait_window(win.window)
        self.update_overview()
        self.refresh_chart()
        
    def view_sales(self):
        win = ViewSalesWindow(self, self.current_theme)
        self.wait_window(win.window)
        self.update_overview()
        self.refresh_chart()
        
    def manage_staff(self):
        ManageStaffWindow(self)
        
    def settings(self):
        win = SettingsWindow(self, self.current_theme)
        self.wait_window(win.window)
        self.update_overview()
        self.refresh_chart()
        
    def about(self):
        AboutWindow(self, self.current_theme, self.app_version)
        
    




   

      