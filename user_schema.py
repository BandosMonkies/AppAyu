from pymongo import MongoClient
from datetime import datetime
import re

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["hospital_db"]

users = db["users"]
diseases = db["diseases"]


def normalize_phone(phone: str) -> str:
    """Normalize phone by removing non-digit characters.

    Keeps digits only. Frontend should also normalize before sending if possible.
    """
    if not phone:
        return phone
    digits = re.sub(r"\D", "", str(phone))
    return digits


def add_user(username, phone):
    """Add a new user.

    Behavior:
    - If a user exists with the same username, return that user (do not create a duplicate).
    - If username is new, create a new user even if the phone number is already in use by another name.
      This allows registering different people who share a phone (per your request).
    - Always return a dict containing `success`, `message` and `user` when possible so the frontend
      can show the patient information.
    """
    # Normalize phone before storing/searching
    phone = normalize_phone(phone)

    # Prefer matching by username first (username is considered the primary identifier here)
    existing_user_name = users.find_one({"username": username})
    if existing_user_name:
        return {
            "success": False,
            "message": "⚠️ Patient with this name already exists in database",
            "user": {
                "username": existing_user_name["username"],
                "phone": existing_user_name.get("phone"),
                "diseases": existing_user_name.get("diseases", [])
            }
        }

    # If username is new, create a new patient. We allow phone duplicates but include a warning
    # in the message if the phone is already present under another name.
    existing_user_phone = users.find_one({"phone": phone})

    patient = {
        "username": username,
        "phone": phone,
        "diseases": [],   # empty array initially
        "created": datetime.utcnow()
    }
    users.insert_one(patient)

    if existing_user_phone:
        return {
            "success": True,
            "message": "✅ New patient added successfully, note: this phone number was already registered to a different name",
            "user": patient
        }

    return {
        "success": True,
        "message": "✅ New patient added successfully to database",
        "user": patient
    }

