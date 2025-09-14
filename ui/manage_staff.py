import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from db.database import get_connection
from firebase_config import fire_db, auth, admin_auth, ADMIN_ENABLED



class ManageStaffWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("👥 Manage Staff")
        self.geometry("600x500")

        # ---- MAIN SCROLLABLE FRAME ----
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            self.scroll_frame,
            text="Staff Members",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=15)

        self.staff_listbox = tk.Listbox(self.scroll_frame, height=15, selectmode="single")
        self.staff_listbox.pack(pady=10, fill="both", expand=True)
        self.staff_listbox.bind("<<ListboxSelect>>", self.on_staff_select)

        # ---- Controls ----
        ctk.CTkButton(
            self, text="👤 Add Staff", fg_color="green", command=self.create_staff_user
        ).pack(pady=5)

        self.username_entry = ctk.CTkEntry(
            self, placeholder_text="Enter staff username/email", width=250
        )
        self.username_entry.pack(pady=5)

        self.new_password_entry = ctk.CTkEntry(
            self, placeholder_text="New password", show="*", width=250
        )
        self.new_password_entry.pack(pady=5)

        ctk.CTkButton(
            self, text="✏️ Change Password", command=self.change_password
        ).pack(pady=5)

        ctk.CTkButton(
            self, text="🗑️ Remove Staff", fg_color="red", command=self.remove_staff
        ).pack(pady=5)

        # ---- Role Management ----
        self.role_var = ctk.StringVar(value="staff")
        self.role_dropdown = ctk.CTkOptionMenu(
            self, variable=self.role_var, values=["staff", "admin"]
        )
        self.role_dropdown.pack(pady=5)

        ctk.CTkButton(
            self, text="🔄 Change Role", command=self.change_role
        ).pack(pady=5)

        # Initial load
        self.refresh_staff()

    # -------------------
    # Load staff from Firebase
    # -------------------
    def refresh_staff(self):
        self.staff_listbox.delete(0, "end")  # clear first

        try:
            users = fire_db.child("users").get()
            if users.each():
                for u in users.each():
                    data = u.val()
                    email = data.get("email", "unknown_email")
                    name = data.get("username") or data.get("email") or u.key()
                    role = data.get("role", "unknown")
                    self.staff_listbox.insert("end", f"{email} ({name}) ({role})")
            else:
                self.staff_listbox.insert("end", "No users found.")
        except Exception as e:
            self.staff_listbox.insert("end", f"Error loading users: {e}")


    # -------------------
    # Create staff (Firebase + Local)
    # -------------------
    def create_staff_user(self):
        email = simpledialog.askstring("New Staff", "Enter staff email:", parent=self)
        password = simpledialog.askstring("New Staff", "Enter staff password:", parent=self, show="*")

        if not email or not password:
            return

        # 1. Create in Firebase
        ok, msg = self.create_firebase_user(email, password)
        if not ok:
            messagebox.showerror("Error", msg)
            return
        else:
            messagebox.showinfo("Success", msg)

        # 2. Also cache locally in SQLite
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)",
                (email, password, "staff"),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("SQLite Error", str(e))

        # 3. Refresh staff list
        self.refresh_staff()

    # -------------------
    # Change password (local and Firebase)
    # -------------------
    def change_password(self):
        username = self.username_entry.get().strip()
        new_pass = self.new_password_entry.get().strip()

        if not username or not new_pass:
            messagebox.showerror("Error", "Please enter username and new password.")
            return

        try:
            # 🔹 Update in Firebase Auth via Admin SDK
            user = admin_auth.get_user_by_email(username)
            admin_auth.update_user(user.uid, password=new_pass)

            # 🔹 Also update in local SQLite (cache)
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pass, username))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", f"✅ Password updated for {username}")
            self.refresh_staff()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update password:\n{e}")

        # -------------------
        # Remove staff (Firebase + Local)
        # -------------------
    def remove_staff(self):
            selected = self.staff_listbox.curselection()
            if not selected:
                messagebox.showwarning("No Selection", "Select a staff to remove.")
                return

            # Extract email from listbox entry
            staff_entry = self.staff_listbox.get(selected[0])
            email = staff_entry.split(" ")[0]   # make sure your listbox always starts with email

            if not messagebox.askyesno("Confirm", f"Are you sure you want to remove {email}?"):
                return

            try:
                # 1. Find UID in Firebase by email
                users = fire_db.child("users").get()
                uid_to_delete = None
                if users.each():
                    for u in users.each():
                        if u.val().get("email") == email:
                            uid_to_delete = u.key()
                            break

                if uid_to_delete:
                    # Remove from Firebase Realtime DB
                    fire_db.child("users").child(uid_to_delete).remove()

                # 2. Remove from local SQLite
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username=?", (email,))
                conn.commit()
                conn.close()

                # 3. Refresh staff list
                self.refresh_staff()

                messagebox.showinfo("Success", f"Removed {email} from staff list.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove staff: {str(e)}")    



    # -------------------
    # Change role in Firebase
    # -------------------
    def change_role(self):
        new_role = self.role_var.get()
        email = self.username_entry.get().strip().lower()

        # 1️⃣ If nothing typed, try to use selected listbox item
        if not email:
            selected = self.staff_listbox.curselection()
            if not selected:
                messagebox.showerror("Error", "Select a staff or enter an email.")
                return
            email_with_role = self.staff_listbox.get(selected[0])
            email = email_with_role.split(" | ")[0].strip().lower()

        # 2️⃣ Ensure Admin SDK is enabled
        if not ADMIN_ENABLED:
            messagebox.showerror("Error", "Admin SDK not enabled. Cannot update role.")
            return

        try:
            users = fire_db.child("users").get()
            if not users.each():
                messagebox.showerror("Error", "No users in Firebase.")
                return

            found = False
            for u in users.each():
                uid = u.key()
                data = u.val()
                if data.get("email", "").lower() == email:
                    # ✅ Update Firebase
                    fire_db.child("users").child(uid).update({"role": new_role})

                    # ✅ Update local SQLite
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET role=? WHERE username=?", (new_role, email))
                    conn.commit()
                    conn.close()

                    messagebox.showinfo("Success", f"✅ {email} is now a {new_role}")
                    found = True
                    break

            if not found:
                messagebox.showerror("Error", f"User '{email}' not found in Firebase.")

            self.refresh_staff()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update role.\n{e}")


    def create_firebase_user(self, email, password, role="staff"):
        try:
            # Create user in Firebase Auth
            user = auth.create_user_with_email_and_password(email, password)
            uid = user["localId"]

            # Add full user profile immediately
            fire_db.child("users").child(uid).set({
                "email": email,
                "username": email.split("@")[0],  # or custom field
                "role": role
            })

            return True, f"✅ User {email} created successfully!"
        except Exception as e:
            return False, f"❌ Error creating user: {e}"

        
    def on_staff_select(self, event):
        selected = self.staff_listbox.curselection()
        if selected:
            username_with_role = self.staff_listbox.get(selected[0])
            username = username_with_role.split(" ")[0]  # extract username part
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, username)




