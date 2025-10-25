# AppAyu - AI-Powered Healthcare Application

A comprehensive healthcare web application featuring AI-powered skin disease detection and patient information management.

## Core Features

### AI Disease Detection
- Upload and analyze skin images
- AI-powered disease detection using Google Gemini AI
- Detailed analysis including:
  - Disease identification
  - Confidence level
  - Severity assessment
  - Visual characteristics
  - Treatment recommendations

### Patient Management
- Comprehensive patient form
  - Personal information (name, age, gender, contact details)
  - Medical history (allergies, medications, existing conditions)
  - Current symptoms with severity levels
  - Vital signs tracking
- Photo upload for affected body parts
- Medical reports/prescriptions upload

### Mobile-First Design
- Responsive layout optimized for mobile devices
- Touch-friendly form inputs
- Image capture from mobile camera
- Smooth scrolling and animations

### Data Security
- File size validation (max 5MB per file)
- File type restrictions
- Consent checkboxes for data processing
- Secure file uploads

## Technical Stack

- Backend: Flask (Python)
- AI Model: Google Gemini AI
- Frontend: HTML, CSS, JavaScript
- Image Processing: PIL (Python Imaging Library)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install flask google-generativeai pillow Flask-CORS Werkzeug
```

### 2. Configure Environment

Set up Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key"
```

### 3. Start the Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

## File Structure

```
AppAyu/
├── app.py            # Main Flask application
├── static/          
│   ├── style.css     # Mobile-optimized styles
│   └── uploads/      # Generated automatically
├── template/
│   └── index.html    # Main frontend interface
└── README.md
```

## API Endpoints

### POST `/detect`
Submit images for AI analysis
- Accepts: Image file
- Returns: AI analysis results

### GET `/`
Main application interface
- Returns: Web interface

## Usage

1. Open the application in your web browser
2. Upload a skin image
3. Click "Detect Disease"
4. View the detailed analysis results
5. Fill out additional patient information if needed

## Testing on Mobile

### Using ngrok (for testing on real mobile devices):

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5000
```

This will give you a public URL you can access from your mobile phone.

### Using Local Network:

1. Find your computer's local IP address
2. Access from mobile: `http://YOUR_LOCAL_IP:5000`

## Browser Compatibility

- ✅ Chrome (recommended)
- ✅ Safari
- ✅ Firefox
- ✅ Edge
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Security Notes

⚠️ This is a development version. For production use:
- Add authentication and authorization
- Implement HTTPS/SSL
- Add proper database integration
- Implement data encryption
- Add input sanitization and validation
- Implement rate limiting
- Add HIPAA compliance measures
- Use secure cloud storage

## Disclaimer

This is an AI-powered prediction tool for educational purposes only. Please consult a qualified healthcare professional for proper diagnosis and treatment.

## License

MIT License

## Support

For issues or questions:
1. Check the console logs in your browser (F12)
2. Check the terminal output from the Flask server
3. Submit an issue on GitHub
