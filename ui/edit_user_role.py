import customtkinter as ctk
from tkinter import messagebox
from firebase_config import fire_db

class EditUserRoleWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Edit User Role")
        self.geometry("400x300")

        # Dictionary: display_name -> UID
        self.user_map = {}

        ctk.CTkLabel(self, text="Select User").pack(pady=5)
        self.user_var = ctk.StringVar(value="")

        self.user_dropdown = ctk.CTkOptionMenu(self, variable=self.user_var, values=[])
        self.user_dropdown.pack(pady=5)

        # Load users from Firebase
        self.load_users()

        ctk.CTkLabel(self, text="New Role").pack(pady=5)
        self.role_var = ctk.StringVar(value="staff")
        self.role_dropdown = ctk.CTkOptionMenu(self, values=["admin", "staff"], variable=self.role_var)
        self.role_dropdown.pack(pady=5)

        save_btn = ctk.CTkButton(self, text="Update Role", command=self.update_role)
        save_btn.pack(pady=20)

    def load_users(self):
        try:
            users = fire_db.child("users").get()
            if users.each():
                for u in users.each():
                    uid = u.key()
                    user_data = u.val()

                    # Try multiple fields for display
                    name = (
                        user_data.get("username")
                        or user_data.get("email")
                        or user_data.get("name")
                        or uid
                    )
                    role = user_data.get("role", "unknown")

                    # Final display string (e.g., "samuel (admin)")
                    display_name = f"{name} ({role})"

                    self.user_map[display_name] = uid

                # Populate dropdown
                self.user_dropdown.configure(values=list(self.user_map.keys()))
                if self.user_map:
                    first_user = list(self.user_map.keys())[0]
                    self.user_var.set(first_user)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load users.\n{e}")

    def update_role(self):
        selected_user = self.user_var.get()
        if not selected_user:
            messagebox.showerror("Error", "Select a user")
            return

        uid = self.user_map[selected_user]
        new_role = self.role_var.get().lower()

        try:
            fire_db.child("users").child(uid).update({"role": new_role})
            messagebox.showinfo("Success", f"{selected_user} is now {new_role}")

            # 🔥 Refresh manage staff window if it exists
            if self.master and hasattr(self.master, "refresh_users"):
                self.master.refresh_users()

            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update role.\n{e}")


