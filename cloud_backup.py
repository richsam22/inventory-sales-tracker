import base64
import os
from firebase_config import fire_db
from db.database import DB_PATH

# -------- Convert file -> base64 -------- #
def encode_file_to_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print("❌ Failed to encode file:", e)
        return None


# -------- Convert base64 -> file -------- #
def decode_base64_to_file(data, file_path):
    try:
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(data))
    except Exception as e:
        print("❌ Failed to decode/restore file:", e)


# -------- Upload (Backup) -------- #
def upload_backup():
    if not os.path.exists(DB_PATH):
        msg = "❌ No local database found."
        print(msg)
        return msg

    data_b64 = encode_file_to_base64(DB_PATH)
    if not data_b64:
        return "❌ Failed to encode database."

    try:
        fire_db.child("backups").child("inventory_db").set(data_b64)
        msg = "✅ Backup uploaded to Firebase Realtime DB."
        print(msg)
        return msg
    except Exception as e:
        msg = f"❌ Upload failed: {e}"
        print(msg)
        return msg


# -------- Download (Restore) -------- #
def download_backup():
    try:
        data_b64 = fire_db.child("backups").child("inventory_db").get().val()
        if not data_b64:
            msg = "⚠️ No backup found in Firebase Realtime DB."
            print(msg)
            return msg

        # Backup current local DB first (safety net)
        if os.path.exists(DB_PATH):
            os.rename(DB_PATH, DB_PATH + ".local.bak")

        decode_base64_to_file(data_b64, DB_PATH)
        msg = f"✅ Backup restored locally: {DB_PATH}"
        print(msg)
        return msg

    except Exception as e:
        msg = f"❌ Restore failed: {e}"
        print(msg)
        return msg


if __name__ == "__main__":
    print("⬆️ Uploading DB to Firebase Realtime DB...")
    upload_backup()
    print("⬇️ Downloading DB from Firebase Realtime DB...")
    download_backup()


