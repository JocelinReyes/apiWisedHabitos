import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

firebase_key = os.environ.get("FIREBASE_KEYS")

if not firebase_key:
    raise ValueError("FIREBASE_KEYS no está definida")

cred = credentials.Certificate(json.loads(firebase_key))
firebase_admin.initialize_app(cred)

db = firestore.client()
