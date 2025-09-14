import customtkinter as ctk
from db.database import get_connection

class MigrationLogsWindow:
    def __init__(self, master):
        self.window = ctk.CTkToplevel(master)
        self.window.title("Migration Logs")
        self.window.geometry("720x600")
        self.window.resizable(True, True)

        title_label = ctk.CTkLabel(self.window, text="📜 Migration Logs", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(10, 5))

        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.window, width=680, height=400)
        scroll_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Table header
        ctk.CTkLabel(scroll_frame, text="Timestamp", width=180, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=5, pady=10)
        ctk.CTkLabel(scroll_frame, text="Message", width=480, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", padx=15, pady=5)

        # Fetch data
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, message FROM migration_log ORDER BY timestamp DESC")
        logs = cursor.fetchall()
        conn.close()

        # Insert logs into the scrollable frame
        for i, (timestamp, message) in enumerate(logs, start=1):
            ctk.CTkLabel(scroll_frame, text=timestamp, width=180, anchor="w", wraplength=200).grid(row=i, column=0, sticky="w", padx=5, pady=10)
            ctk.CTkLabel(scroll_frame, text=message, width=490, anchor="w", wraplength=460, justify="left").grid(row=i, column=1, sticky="w", padx=15, pady=3)

        # Close button
        close_btn = ctk.CTkButton(self.window, text="Close", command=self.window.destroy)
        close_btn.pack(pady=10)

