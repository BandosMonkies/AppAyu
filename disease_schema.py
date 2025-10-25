from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["hospital_db"]
users = db["users"]
diseases = db["diseases"]

# Function to log disease detection
def add_disease(username, disease_name, asha_worker_info=None):
    disease_record = {
        "name": disease_name,
        "detected_at": datetime.now()
    }
    
    # Add ASHA worker information if provided
    if asha_worker_info:
        disease_record["checked_by"] = {
            "name": asha_worker_info.get("name"),
            "asha_id": asha_worker_info.get("ashaId") or asha_worker_info.get("asha_id"),
            "mobile": asha_worker_info.get("mobile")
        }

    result = users.update_one(
        {"username": username},
        {"$addToSet": {"diseases": disease_record}}
    )

    if result.modified_count > 0:
        return {"success": True, "message": f"Added disease '{disease_name}' for {username}"}
    else:
        return {"success": False, "message": "User not found"}
