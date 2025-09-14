import pyrebase
import json
import os
import sys

# ---------------- Helper to locate files ----------------
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    if getattr(sys, 'frozen', False):  # running as bundled exe
        base_path = sys._MEIPASS
    else:  # running in normal python
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------------- Pyrebase Setup (client side) ----------------
CONFIG_PATH = resource_path(os.path.join("config", "firebase.json"))

with open(CONFIG_PATH, encoding="utf-8") as f:
    firebase_config = json.load(f)

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
fire_db = firebase.database()
storage = firebase.storage()

# ---------------- Firebase Admin SDK Setup (server side, optional) ----------------
try:
    import firebase_admin
    from firebase_admin import credentials, auth as admin_auth

    SERVICE_ACCOUNT_PATH = resource_path(os.path.join("config", "serviceAccountKey.json"))

    if os.path.exists(SERVICE_ACCOUNT_PATH):
        if not firebase_admin._apps:  # prevent double init
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred, {
                "databaseURL": firebase_config["databaseURL"]
            })
        ADMIN_ENABLED = True
    else:
        ADMIN_ENABLED = False
        admin_auth = None
        print("⚠️ serviceAccountKey.json not found — Admin SDK disabled.")

except ImportError:
    firebase_admin = None
    admin_auth = None
    ADMIN_ENABLED = False
    print("⚠️ firebase_admin not installed — Admin SDK disabled.")

