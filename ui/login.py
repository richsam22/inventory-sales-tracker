import customtkinter as ctk
from tkinter import messagebox
from firebase_config import auth, fire_db  # <-- import Firebase auth
from db.database import get_connection  # keep this for fallback/local users
from ui.admin_passw_change import ChangeAdminPasswordWindow
from ui.dashboard import Dashboard


class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_login):
        super().__init__(parent)
        self.on_login = on_login
        self.title("Login")
        self.geometry("400x300")

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Email / Username")
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        login_btn = ctk.CTkButton(self, text="Login", command=self.attempt_login)
        login_btn.pack(pady=20)

        # Ensure default admin exists locally (for offline use)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", "admin123", "Admin")
            )
            conn.commit()
        conn.close()

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # --- Try Firebase First (source of truth) ---
        try:
            firebase_user = auth.sign_in_with_email_and_password(username, password)
            
            uid = firebase_user["localId"]

            # Fetch role from Firebase DB
            role = fire_db.child("users").child(uid).child("role").get().val()
            
            role = (role or "staff").lower()
            if role not in ["admin", "staff"]:
                role = "staff"

            # --- Ensure Firebase user has email + username stored ---
            fire_db.child("users").child(uid).update({
                "email": username,
                "username": username.split("@")[0],  # or ask full name later
                "role": role
            })
            
            # --- Always update local SQLite cache to keep in sync ---
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            conn.commit()
            conn.close()
            

            self.destroy()
            self.on_login(username, role)
            return

        except Exception as e:
            print("DEBUG: Firebase login failed:", e)

        # --- If Firebase fails, fallback to SQLite ---
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        conn.close()

        if result:
            role = result[0].lower()
            if role not in ["admin", "staff"]:
                role = "staff"

            if username == "admin" and password == "admin123":
                messagebox.showwarning("Security Warning", "⚠️ Default admin password in use. Change it in settings.")

            self.destroy()
            self.on_login(username, role, login_window=self)
            return

        # --- If neither works ---
        messagebox.showerror("Login Failed", "Invalid credentials (Firebase + local failed).")
        
        
    
