import customtkinter as ctk
from PIL import Image
from ui.dashboard import Dashboard
from ui.login import LoginWindow
from ui.splash_screen import SplashScreen
from db.migrations import run_migrations
from utils.backup import auto_backup
from cloud_backup import upload_backup, download_backup
from sync_products import ensure_last_updated_columns, sync_to_firebase, sync_from_firebase, start_listeners, stop_listeners
from utils.path_helper import resource_path


def get_version():
    try:
        with open("version.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "v0.0.0"  # fallback if missing




def open_dashboard(username, role, login_window):
    
    # Called after successful login
    dashboard = Dashboard(login_window.master, username, role, APP_VERSION)
    
    def _destroy_login():
        if login_window.winfo_exists():
            login_window.destroy()
    dashboard.after(100, _destroy_login)   # destroy login *after* dashboard finishes

    # Attach cloud backup on dashboard exit too
    def on_dashboard_exit():
        print("💾 Saving backup before exit (dashboard)...")
        upload_backup()
        dashboard.destroy()

    dashboard.protocol("WM_DELETE_WINDOW", on_dashboard_exit)

if __name__ == "__main__":
    APP_VERSION = get_version()
    # -------- Database + Sync -------- #
    run_migrations()

    print("🔄 Checking for cloud backup...")
    download_backup()   # restore latest cloud copy first
    auto_backup()       # then make sure a local backup copy exists
    ensure_last_updated_columns()
    sync_to_firebase()    # push local changes up first (optional)
    sync_from_firebase()  # pull remote (merges with ts resolution)
    start_listeners()     # keep real-time listeners running

    # -------- UI Setup -------- #
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.withdraw()

    # Show splash first
    splash = SplashScreen(root, logo_path=resource_path("assets/inventory_logo.png"))
    root.wait_window(splash)

    # Open login window
    login_window = LoginWindow(root, on_login=open_dashboard)

    
    root.mainloop()


    # Attach backup to login exit
    def on_exit():
        print("💾 Saving backup before exit (login)...")
        upload_backup()
        stop_listeners()
        root.destroy()

    login_window.protocol("WM_DELETE_WINDOW", on_exit)
    login_window.mainloop()





