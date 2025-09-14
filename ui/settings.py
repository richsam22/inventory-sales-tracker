import customtkinter as ctk
from ui.MigrationLogsWindow import MigrationLogsWindow
from tkinter import messagebox as mb, filedialog
from models.product import Product
from models.sale import Sale
from db.database import DB_PATH, get_connection
from ui.admin_passw_change import ChangeAdminPasswordWindow
from ui.edit_user_role import EditUserRoleWindow
from cloud_backup import download_backup, upload_backup
import shutil
import os
import zipfile
from PIL import Image


BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "backups")

class SettingsWindow:
    def __init__(self, master, theme="System"):
        self.window = ctk.CTkToplevel(master)
        self.window.title("⚙ Settings")
        self.window.geometry("720x550")
        self.window.resizable(False, False)

        # Ensure backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)

        ctk.set_appearance_mode(theme)
        
        # Title
        title_label = ctk.CTkLabel(
            self.window, text="Settings & Preferences",
            font=("Arial", 22, "bold")
        )
        title_label.pack(pady=15)
        
        # Theme Switcher
        theme_frame = ctk.CTkFrame(self.window, corner_radius=12)
        theme_frame.pack(pady=10, fill="x", padx=20)

        theme_label = ctk.CTkLabel(theme_frame, text="Theme", font=("Arial", 16))
        theme_label.pack(side="left", padx=10, pady=10)

        theme_options = ["System", "Light", "Dark"]
        self.theme_dropdown = ctk.CTkOptionMenu(
            theme_frame, values=theme_options,
            command=self.change_theme
        )
        self.theme_dropdown.set(theme)
        self.theme_dropdown.pack(side="right", padx=10, pady=10)
        
        # Change admin password
        change_password_btn = ctk.CTkButton(
            self.window,
            text="🔑 Change Admin Password",
            command=lambda: self.change_password()
        )
        change_password_btn.pack(pady=5)
        
        edit_role_btn = ctk.CTkButton(self.window, text="Edit User Role", command=self.open_edit_role)
        edit_role_btn.pack(pady=10)

        # View migration logs
        view_logs_btn = ctk.CTkButton(
            self.window,
            text="📜 View Migration Logs",
            command=lambda: MigrationLogsWindow(self.window)
        )
        view_logs_btn.pack(pady=5)
        
        # Backup to Cloud
        cloud_backup_btn = ctk.CTkButton(
            self.window, 
            text="☁️ Upload Backup to Cloud", 
            command=self.handle_upload
        )
        cloud_backup_btn.pack(pady=10)

        cloud_restore_btn = ctk.CTkButton(
            self.window, 
            text="⬇️ Restore Backup from Cloud", 
            command=self.handle_download
        )
        cloud_restore_btn.pack(pady=10)

        # Backup DB (Manual)
        backup_btn = ctk.CTkButton(
            self.window,
            text="💾 Backup Database",
            fg_color="#0078D7",
            hover_color="#005A9E",
            command=self.manual_backup,
            corner_radius=8
        )
        backup_btn.pack(pady=10)

        # Restore DB
        restore_btn = ctk.CTkButton(
            self.window,
            text="📂 Restore Database",
            fg_color="#00A86B",
            hover_color="#007F55",
            command=self.restore_database,
            corner_radius=8
        )
        restore_btn.pack(pady=10)

        # Clear all data
        clear_btn = ctk.CTkButton(
            self.window,
            text="🧹 Clear All Data",
            fg_color="red",
            hover_color="#990000",
            command=self.clear_all_data,
            corner_radius=8
        )
        clear_btn.pack(pady=10)
        
        
    def change_theme(self, new_theme):
        ctk.set_appearance_mode(new_theme)
        
    def open_edit_role(self):
        EditUserRoleWindow(self.window)
        
    def handle_upload(self):
        msg = upload_backup()
        mb.showinfo("Cloud Backup", msg)

    def handle_download(self):
        msg = download_backup()
        mb.showinfo("Cloud Restore", msg)

    def manual_backup(self):
        """Manual backup with file save dialog."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("SQLite DB", "*.db")],
                title="Save Database Backup"
            )
            if file_path:
                shutil.copy(DB_PATH, file_path)
                mb.showinfo("Success", f"✅ Backup saved to:\n{file_path}")
        except Exception as e:
            mb.showerror("Error", str(e))

    # Your backups are inside project/backups/
    BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "backups")
    
    def change_password(self):
        ChangeAdminPasswordWindow(self.window)
    
    def restore_database(self):
        try:
            file_path = filedialog.askopenfilename(
                initialdir=os.path.abspath(BACKUP_DIR),   # Open directly in backups/
                title="Select Database Backup to Restore",
                filetypes=[
                    ("Backup Files", "*.zip"),
                    ("SQLite Database", "*.db")
                ]
            )

            if not file_path or not os.path.isfile(file_path):
                return  # Cancelled

            # ⚠️ Confirm before overwriting
            confirm = mb.askyesno(
                "Confirm Restore",
                "⚠️ Restoring will overwrite your current database.\n\nDo you want to continue?"
            )
            if not confirm:
                return

            # Handle .zip backup
            if file_path.endswith(".zip"):
                with zipfile.ZipFile(file_path, "r") as zipf:
                    if "inventory.db" not in zipf.namelist():
                        mb.showerror("Error", "❌ This backup does not contain inventory.db")
                        return

                    extracted_db = zipf.extract("inventory.db", path=BACKUP_DIR)
                    shutil.copy(extracted_db, DB_PATH)
                    os.remove(extracted_db)
            else:
                # Handle raw .db backup
                shutil.copy(file_path, DB_PATH)

            mb.showinfo("Success", "✅ Database restored successfully.\nRestart the app to apply changes.")

        except Exception as e:
            mb.showerror("Error", f"❌ Restore failed:\n{str(e)}")

    def clear_all_data(self):
        confirm = mb.askyesno(
            "⚠ Confirm",
            "This will permanently delete all products and sales records.\nAre you sure?"
        )
        if confirm:
            try:
                Product.clear_all()
                Sale.clear_all()
                mb.showinfo("Success", "All product and sales data have been cleared.")
            except Exception as e:
                mb.showerror("Error", str(e))

