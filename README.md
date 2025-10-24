# AppAyu Healthcare Web Application

A mobile-optimized healthcare web application for collecting patient information, symptoms, and medical photos.

## Features

✅ **Comprehensive Patient Form**
- Personal information (name, age, gender, contact details)
- Medical history (allergies, medications, existing conditions)
- Current symptoms with severity levels
- Vital signs tracking
- Photo upload for affected body parts
- Medical reports/prescriptions upload

✅ **Mobile-First Design**
- Responsive layout optimized for mobile devices
- Touch-friendly form inputs
- Image capture from mobile camera
- Smooth scrolling and animations

✅ **Data Security**
- File size validation (max 5MB per file)
- File type restrictions
- Consent checkboxes for data processing
- Secure file uploads

✅ **Backend Features**
- Flask REST API server
- File upload handling
- JSON data storage
- Admin endpoints to view submissions

## Setup Instructions

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or install manually:
```bash
pip install Flask Flask-CORS Werkzeug
```

### 2. Start the Backend Server

```bash
cd backend
python server.py
```

The server will start on `http://localhost:5000`

### 3. Open the Web Application

Simply open `index.html` in your web browser, or use a local server:

```bash
# Using Python's built-in server (from the project root)
python -m http.server 8080
```

Then visit: `http://localhost:8080`

## File Structure

```
AppAyu-MVP/
├── index.html          # Main HTML form
├── style.css           # Mobile-optimized styles
├── JavaScript.js       # Form handling and API calls
├── backend/
│   ├── server.py       # Flask backend server
│   ├── requirements.txt
│   └── uploads/        # Generated automatically
│       ├── photos/     # Patient photos
│       ├── reports/    # Medical reports
│       └── submissions/ # JSON data files
└── README.md
```

## API Endpoints

### POST `/api/submit-patient-data`
Submit patient information with files
- Accepts: FormData with text fields and files
- Returns: Submission ID and success status

### GET `/api/health`
Health check endpoint
- Returns: Server status

### GET `/api/submissions`
Get all patient submissions (admin)
- Returns: Array of all submissions

### GET `/api/submission/<id>`
Get specific submission by ID
- Returns: Single submission data

## Usage

1. **Fill out the form** with patient details
2. **Upload photos** of affected areas (optional)
3. **Upload medical reports** (optional)
4. **Accept consent** checkboxes
5. **Submit** the form

The data will be sent to the server and saved in the `uploads/submissions` folder as JSON files. Photos and reports are saved in their respective folders.

## Testing on Mobile

### Using ngrok (for testing on real mobile devices):

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8080
```

This will give you a public URL you can access from your mobile phone.

### Using Local Network:

1. Find your computer's local IP address:
   ```bash
   # Linux
   hostname -I
   
   # Or
   ip addr show
   ```

2. Update the API endpoint in `JavaScript.js`:
   ```javascript
   const API_ENDPOINT = 'http://YOUR_LOCAL_IP:5000/api/submit-patient-data';
   ```

3. Access from mobile: `http://YOUR_LOCAL_IP:8080`

## Browser Compatibility

- ✅ Chrome (recommended)
- ✅ Safari
- ✅ Firefox
- ✅ Edge
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Security Notes

⚠️ This is a MVP/Demo application. For production use:
- Add authentication and authorization
- Implement HTTPS/SSL
- Add database instead of JSON files
- Implement proper data encryption
- Add input sanitization and validation
- Implement rate limiting
- Add HIPAA compliance measures
- Use cloud storage for files

## License

MIT License - Feel free to use for your hackathon project!

## Support

For issues or questions, check the console logs in your browser (F12) and the terminal output from the Flask server.
