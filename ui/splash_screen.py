import customtkinter as ctk
from tkinter import ttk
from PIL import Image
from utils.path_helper import resource_path

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent, logo_path=resource_path("assets/1.png")):
        super().__init__(parent)
        self.title("Loading...")
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 300) // 2
        self.geometry(f"+{x}+{y}")

        # Logo
        try:
            logo = ctk.CTkImage(light_image=Image.open(logo_path), size=(150, 150))
            ctk.CTkLabel(self, image=logo, text="").pack(pady=5)
        except:
            ctk.CTkLabel(self, text="📦", font=("Arial", 40)).pack(pady=20)

        # App Name
        ctk.CTkLabel(self, text="StockMate Pro", font=("Arial", 20, "bold")).pack(pady=5)
        ctk.CTkLabel(self, text="Inventory & Sales Tracker", font=("Arial", 14)).pack(pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(self, mode="determinate", length=250)
        self.progress.pack(pady=5)

        # Footer
        ctk.CTkLabel(self, text="Powered by SaenTechy", font=("Arial", 12)).pack(side="bottom", pady=10)

        # Start loading animation
        self.progress_value = 0
        self.after(30, self.load_step)

    def load_step(self):
        if self.progress_value < 100:
            self.progress_value += 1
            self.progress["value"] = self.progress_value
            self.after(30, self.load_step)  # schedule next update
        else:
            self.destroy()

