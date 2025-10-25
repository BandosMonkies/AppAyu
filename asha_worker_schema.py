from pymongo import MongoClient
from datetime import datetime
import re

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["hospital_db"]

# ASHA workers collection
asha_workers = db["asha_workers"]


def normalize_phone(phone: str) -> str:
    """Normalize phone by removing non-digit characters.

    Keeps digits only. Frontend should also normalize before sending if possible.
    """
    if not phone:
        return phone
    digits = re.sub(r"\D", "", str(phone))
    return digits


def add_asha_worker(name, asha_id, mobile, education, years, village, password):
    """Add a new ASHA worker.

    Behavior:
    - If a worker exists with the same mobile or asha_id, return error message.
    - If both are new, create a new worker record.
    - Always return a dict containing `success`, `message` and `worker` when possible.
    """
    # Normalize phone before storing/searching
    mobile = normalize_phone(mobile)

    # Check if mobile already exists
    existing_by_mobile = asha_workers.find_one({"mobile": mobile})
    if existing_by_mobile:
        return {
            "success": False,
            "message": "⚠️ ASHA worker with this mobile number already exists",
            "worker": None
        }

    # Check if asha_id already exists
    existing_by_id = asha_workers.find_one({"asha_id": asha_id})
    if existing_by_id:
        return {
            "success": False,
            "message": "⚠️ ASHA worker with this ID already exists",
            "worker": None
        }

    # Create new worker record
    worker = {
        "name": name,
        "asha_id": asha_id,
        "mobile": mobile,
        "education": education,
        "years": int(years) if years else 0,
        "village": village,
        "password": password,  # In production, this should be hashed
        "photo": "",
        "created": datetime.utcnow()
    }
    
    result = asha_workers.insert_one(worker)
    worker["_id"] = result.inserted_id

    return {
        "success": True,
        "message": "✅ New ASHA worker added successfully to database",
        "worker": worker
    }


def find_asha_worker(mobile):
    """Find an ASHA worker by mobile number."""
    mobile = normalize_phone(mobile)
    worker = asha_workers.find_one({"mobile": mobile})
    return worker


def update_asha_worker(mobile, updates):
    """Update an ASHA worker's information.
    
    Updates can include: name, asha_id, education, years, village, photo, password
    """
    mobile = normalize_phone(mobile)
    
    # Normalize phone in updates if present
    if 'mobile' in updates:
        updates['mobile'] = normalize_phone(updates['mobile'])
    
    # Add updated timestamp
    updates['updated'] = datetime.utcnow()
    
    result = asha_workers.update_one(
        {"mobile": mobile},
        {"$set": updates}
    )
    
    if result.modified_count > 0:
        # Return updated worker
        updated_worker = asha_workers.find_one({"mobile": mobile})
        return {
            "success": True,
            "message": "Profile updated successfully",
            "worker": updated_worker
        }
    else:
        return {
            "success": False,
            "message": "Worker not found or no changes made",
            "worker": None
        }


def verify_asha_worker(mobile, password):
    """Verify ASHA worker credentials."""
    mobile = normalize_phone(mobile)
    worker = asha_workers.find_one({"mobile": mobile})
    
    if not worker:
        return {
            "success": False,
            "message": "Worker not found",
            "worker": None
        }
    
    # In production, this should use hashed passwords
    if worker.get("password") == password:
        # Remove password from returned worker
        worker_copy = worker.copy()
        worker_copy.pop("password", None)
        return {
            "success": True,
            "message": "Login successful",
            "worker": worker_copy
        }
    else:
        return {
            "success": False,
            "message": "Invalid password",
            "worker": None
        }
