# Hack-o-ween Healthcare Application

A healthcare application for ASHA workers to manage patients and perform AI-powered disease detection.

## Features

- **ASHA Worker Management**: Database schema for ASHA workers with authentication
- **Patient Management**: Patient registration and disease history tracking
- **AI Disease Detection**: Gemini AI-powered image analysis for skin, eye, and oral conditions
- **Multi-language Support**: English, Hindi, and Kannada

## Database Schemas

### 1. ASHA Workers (`asha_workers` collection)
Stores ASHA worker information:
- `name`: Full name of the worker
- `asha_id`: Unique ASHA worker ID
- `mobile`: Mobile number (used for authentication)
- `education`: Education qualification
- `years`: Years of service
- `village`: Village/PHC assignment
- `password`: Encrypted password (should be hashed in production)
- `photo`: Profile photo (base64 encoded)
- `created`: Account creation timestamp
- `updated`: Last update timestamp

### 2. Patients (`users` collection)
Stores patient information:
- `username`: Patient name
- `phone`: Phone number (normalized)
- `diseases`: Array of disease records
  - `name`: Disease name
  - `detected_at`: Detection timestamp
- `created`: Account creation timestamp

## API Endpoints

### ASHA Worker Endpoints

#### Register ASHA Worker
```
POST /register_asha_worker
Body: {
  "name": "string",
  "ashaId": "string",
  "mobile": "string",
  "education": "string",
  "years": number,
  "village": "string",
  "password": "string"
}
```

#### Login ASHA Worker
```
POST /login_asha_worker
Body: {
  "mobile": "string",
  "otp": "string" (optional),
  "password": "string" (optional)
}
```

#### Get ASHA Worker
```
POST /get_asha_worker
Body: {
  "mobile": "string"
}
```

#### Update ASHA Worker
```
POST /update_asha_worker
Body: {
  "mobile": "string",
  "name": "string" (optional),
  "asha_id": "string" (optional),
  "education": "string" (optional),
  "years": number (optional),
  "village": "string" (optional),
  "photo": "string" (optional),
  "password": "string" (optional)
}
```

### Patient Endpoints

#### Add Patient
```
POST /add_patient
Body: {
  "name": "string",
  "phone": "string"
}
```

#### Add Disease
```
POST /add_disease
Body: {
  "username": "string",
  "disease_name": "string"
}
```

#### Search Patient
```
POST /search_patient
Body: {
  "name": "string" (optional),
  "phone": "string" (optional)
}
```

### AI Detection

#### Predict Disease
```
POST /predict
Form Data:
  - file: image file
  - category: "skin" | "eye" | "oral" | "other"
  - patient_name: "string" (optional)
  - age: number (optional)
  - extra_info: "string" (optional)
```

## Setup Instructions

1. Install dependencies:
```bash
pip install flask flask-cors pymongo google-generativeai pillow
```

2. Start MongoDB:
```bash
mongod
```

3. Run the application:
```bash
python app.py
```

4. Access the application:
```
http://localhost:5000
```

## File Structure

```
arch/
├── app.py                      # Main Flask application
├── asha_worker_schema.py       # ASHA worker database schema
├── user_schema.py              # Patient database schema
├── disease_schema.py           # Disease tracking schema
├── templates/
│   ├── Home.html              # ASHA worker dashboard
│   └── index.html             # Disease detection page
├── static/
│   ├── style.css              # Styles
│   └── uploads/               # Uploaded images
└── README.md                   # This file
```

## Notes

- All passwords should be hashed in production using bcrypt or similar
- OTP verification should be implemented with actual SMS service
- MongoDB connection string can be modified in schema files
- Gemini API key should be set as environment variable

## License

MIT License
