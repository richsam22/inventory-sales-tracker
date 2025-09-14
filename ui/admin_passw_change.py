import customtkinter as ctk
from tkinter import messagebox
from db.database import get_connection


class ChangeAdminPasswordWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("🔑 Change Admin Password")
        self.geometry("400x250")

        ctk.CTkLabel(self, text="Change Admin Password", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        self.old_pass = ctk.CTkEntry(self, placeholder_text="Old Password", show="*")
        self.old_pass.pack(pady=5)

        self.new_pass = ctk.CTkEntry(self, placeholder_text="New Password", show="*")
        self.new_pass.pack(pady=5)

        self.confirm_pass = ctk.CTkEntry(self, placeholder_text="Confirm Password", show="*")
        self.confirm_pass.pack(pady=5)

        ctk.CTkButton(self, text="✅ Update Password", command=self.change_password).pack(pady=10)
        
        
    def change_password(self):
        old_pass = self.old_pass.get()
        new_pass = self.new_pass.get()
        confirm_pass = self.confirm_pass.get()

        if not old_pass or not new_pass:
            messagebox.showerror("Error", "All fields are required.")
            return
        if new_pass != confirm_pass:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username='admin'")
        current_pass = cursor.fetchone()[0]

        if old_pass != current_pass:
            messagebox.showerror("Error", "Old password incorrect.")
        else:
            cursor.execute("UPDATE users SET password=? WHERE username='admin'", (new_pass,))
            conn.commit()
            messagebox.showinfo("Success", "Admin password updated successfully!")
            self.destroy()

        conn.close()
        
    