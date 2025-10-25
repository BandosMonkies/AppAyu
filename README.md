# AppAyu - AI Skin Disease Detection

An AI-powered web application for skin disease detection and analysis using Flask and Google's Gemini AI.

## Features

- Upload and analyze skin images
- AI-powered disease detection
- Detailed analysis including:
  - Disease identification
  - Confidence level
  - Severity assessment
  - Visual characteristics
  - Treatment recommendations

## Technical Stack

- Backend: Flask (Python)
- AI Model: Google Gemini AI
- Frontend: HTML, CSS, JavaScript
- Image Processing: PIL (Python Imaging Library)

## Setup

1. Install dependencies:
```bash
pip install flask google-generativeai pillow
```

2. Set up Gemini API key:
```python
export GEMINI_API_KEY="your-api-key"
```

3. Run the application:
```bash
python app.py
```

## Usage

1. Open the application in your web browser
2. Upload a skin image
3. Click "Detect Disease"
4. View the detailed analysis results

## Disclaimer

This is an AI-powered prediction tool for educational purposes only. Please consult a qualified healthcare professional for proper diagnosis and treatment.