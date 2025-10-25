from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Create subdirectories for organization
for subfolder in ['photos', 'reports', 'submissions']:
    path = os.path.join(UPLOAD_FOLDER, subfolder)
    if not os.path.exists(path):
        os.makedirs(path)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, subfolder):
    """Save uploaded file and return the filename"""
    if file and allowed_file(file.filename):
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{original_filename}"
        
        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, subfolder, filename)
        file.save(filepath)
        return filename
    return None

@app.route('/api/submit-patient-data', methods=['POST'])
def submit_patient_data():
    """Handle patient data submission"""
    try:
        # Get form data
        form_data = {}
        
        # Extract text fields
        text_fields = [
            'fullName', 'age', 'gender', 'phone', 'email', 'bloodGroup',
            'allergies', 'medications', 'medicalConditions',
            'chiefComplaint', 'symptoms', 'duration', 'severity', 'affectedBodyPart',
            'temperature', 'heartRate', 'bloodPressure', 'oxygenLevel',
            'additionalNotes', 'emergencyConsent', 'dataConsent',
            'submissionTime', 'photoCount', 'reportCount'
        ]
        
        for field in text_fields:
            value = request.form.get(field, '')
            form_data[field] = value
        
        # Handle file uploads
        uploaded_photos = []
        uploaded_reports = []
        
        # Process photos
        for key in request.files:
            file = request.files[key]
            if key.startswith('photo_'):
                filename = save_file(file, 'photos')
                if filename:
                    uploaded_photos.append(filename)
            elif key.startswith('report_'):
                filename = save_file(file, 'reports')
                if filename:
                    uploaded_reports.append(filename)
        
        # Add file information to form data
        form_data['uploadedPhotos'] = uploaded_photos
        form_data['uploadedReports'] = uploaded_reports
        
        # Generate unique submission ID
        submission_id = datetime.now().strftime('%Y%m%d%H%M%S')
        form_data['submissionId'] = submission_id
        
        # Save submission data as JSON
        submission_file = os.path.join(UPLOAD_FOLDER, 'submissions', f'submission_{submission_id}.json')
        with open(submission_file, 'w') as f:
            json.dump(form_data, f, indent=2)
        
        # Log submission
        print(f"\n{'='*50}")
        print(f"New Patient Submission: {submission_id}")
        print(f"{'='*50}")
        print(f"Patient Name: {form_data.get('fullName')}")
        print(f"Age: {form_data.get('age')}")
        print(f"Gender: {form_data.get('gender')}")
        print(f"Phone: {form_data.get('phone')}")
        print(f"Chief Complaint: {form_data.get('chiefComplaint')}")
        print(f"Severity: {form_data.get('severity')}")
        print(f"Photos Uploaded: {len(uploaded_photos)}")
        print(f"Reports Uploaded: {len(uploaded_reports)}")
        print(f"Submission Time: {form_data.get('submissionTime')}")
        print(f"{'='*50}\n")
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Patient data submitted successfully',
            'submissionId': submission_id,
            'photosUploaded': len(uploaded_photos),
            'reportsUploaded': len(uploaded_reports)
        }), 200
        
    except Exception as e:
        print(f"Error processing submission: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to submit patient data'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'AppAyu Healthcare Server is running',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    """Get all submissions (for admin/review purposes)"""
    try:
        submissions_dir = os.path.join(UPLOAD_FOLDER, 'submissions')
        submissions = []
        
        for filename in os.listdir(submissions_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(submissions_dir, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    submissions.append(data)
        
        # Sort by submission time (newest first)
        submissions.sort(key=lambda x: x.get('submissionTime', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(submissions),
            'submissions': submissions
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/submission/<submission_id>', methods=['GET'])
def get_submission(submission_id):
    """Get a specific submission by ID"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, 'submissions', f'submission_{submission_id}.json')
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'Submission not found'
            }), 404
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return jsonify({
            'success': True,
            'submission': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏥 AppAyu Healthcare Server Starting...")
    print("="*60)
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"🌐 Server will run on: http://localhost:5000")
    print(f"✅ Health check: http://localhost:5000/api/health")
    print(f"📊 View submissions: http://localhost:5000/api/submissions")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)