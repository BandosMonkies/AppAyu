# Hack-o-ween Healthcare Application

A healthcare application for ASHA workers to manage patients and perform AI-powered disease detection.

## Features

- **ASHA Worker Management**: Database schema for ASHA workers with authentication
- **Patient Management**: Patient registration and disease history tracking
- **AI Disease Detection**: Gemini AI-powered image analysis for skin, eye, and oral conditions
- **Multi-language Support**: English, Hindi, and Kannada

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

### Enable AI Translation (optional)

To display AI analysis in Hindi or Kannada, provide a Google Translation v2 API key via environment variable before starting the app:

```bash
export GOOGLE_TRANSLATE_API_KEY="<your_google_translation_api_key>"
python app.py
```

Notes:
- The app uses the Google Translation v2 REST API directly; only an API key is required (no service account needed).
- On the detection page, choose the desired Output Language before running analysis.
- If the key is missing or invalid, the app will gracefully fall back to English output.

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
