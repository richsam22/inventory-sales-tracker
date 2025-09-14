import firebase_admin
from firebase_admin import credentials, firestore, auth

# Path to your downloaded firebase.json
cred = credentials.Certificate("config/firebase.json")

# Initialize app (only once)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Firestore DB
db = firestore.client()
