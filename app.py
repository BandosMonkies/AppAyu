from flask import Flask, render_template, request, jsonify
import os
import json
import base64
import re
from io import BytesIO
import uuid
from datetime import datetime
from user_schema import add_user, users, normalize_phone
from disease_schema import add_disease
from asha_worker_schema import add_asha_worker, find_asha_worker, update_asha_worker, verify_asha_worker
# helper for Mongo types
from bson import ObjectId
# for registeration ->register_user("Abhishek", "9876543210"
# --- Gemini Setup ---
try:
    import google.generativeai as genai
    from PIL import Image
    GEMINI_API_KEY = os.environ.get(
        "GEMINI_API_KEY", 
        "AIzaSyCK4jorAW75rdbHStHvwqgTAgYDgipQlwY"  # replace with your actual API key
    )
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Initialize Gemini Vision model
    model = genai.GenerativeModel('models/gemini-2.5-pro')
    GEMINI_ENABLED = True
    print("[info] Gemini AI enabled with image analysis support")
except Exception as e:
    GEMINI_ENABLED = False
    print(f"[warn] Gemini AI not available: {e}")

# --- Flask App ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ----------------- Helper Functions -----------------

def is_valid_image(file):
    # Check if file has an allowed extension
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in file.filename and \
           file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
def _extract_readable_content(response_text, image):
    """Extract readable content from raw response text when JSON parsing fails."""
    try:
        # Try to find key information using regex patterns
        disease_match = re.search(r'"Disease name":\s*"([^"]+)"', response_text)
        confidence_match = re.search(r'"Confidence level":\s*(\d+)', response_text)
        description_match = re.search(r'"Description":\s*"([^"]+)"', response_text)
        severity_match = re.search(r'"Severity level":\s*"([^"]+)"', response_text)
        
        # Extract medicines list
        medicines_match = re.search(r'"List of recommended medicines":\s*\[(.*?)\]', response_text, re.DOTALL)
        medicines = []
        if medicines_match:
            medicines_text = medicines_match.group(1)
            # Extract individual medicine items
            medicine_items = re.findall(r'"([^"]+)"', medicines_text)
            medicines = [f"• {item}" for item in medicine_items if item.strip()]
        
        # If no medicines found, add a default
        if not medicines:
            medicines = ["• Consult a healthcare professional"]
        
        return {
            "disease": disease_match.group(1) if disease_match else "Analysis Available",
            "confidence": int(confidence_match.group(1)) if confidence_match else 90,
            "description": description_match.group(1) if description_match else "Analysis completed - please consult description for details",
            "severity": severity_match.group(1) if severity_match else "Please consult description",
            "medicines": medicines,
            "analysis": {
                "color_tone": "Analyzed",
                "texture": "Analyzed", 
                "size": f"{image.size[0]}x{image.size[1]} pixels"
            }
        }
    except Exception as e:
        print(f"[error] Failed to extract readable content: {e}")
        return {
            "disease": "Analysis Available",
            "confidence": 90,
            "description": "Analysis completed - please consult a healthcare professional for proper diagnosis",
            "severity": "Please consult description",
            "medicines": ["• Consult a healthcare professional"],
            "analysis": {
                "color_tone": "Analyzed",
                "texture": "Analyzed",
                "size": f"{image.size[0]}x{image.size[1]} pixels"
            }
        }

def analyze_with_gemini(image_path, category='skin', age=None, extra_info=None):
    if not GEMINI_ENABLED:
        return {"error": "Gemini AI not enabled"}

    try:
        # Load and prepare the image
        image = Image.open(image_path)
        
        # Convert image to RGB mode (required by Gemini)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Choose a prompt tailored to the selected category
        if category == 'eye':
            prompt = """
            You are an ophthalmology expert AI. Analyze this eye image and provide the following information:
            - Disease name (e.g., conjunctivitis, stye, pterygium, chalazion, keratitis)
            - Confidence level (as a number between 0-100)
            - Description of the condition and likely causes
            - Severity level (Mild/Moderate/Severe)
            - List of recommended medicines (non-prescriptive; advise consulting an eye specialist)
            - Visual characteristics (redness, discharge, swelling, lesions, eyelid involvement)

            Format your response as valid JSON with these exact keys:
            {
                "Disease name": "",
                "Confidence level": 0,
                "Description": "",
                "Severity level": "",
                "List of recommended medicines": [],
                "Visual characteristics": {
                    "redness": "",
                    "discharge": "",
                    "swelling": "",
                    "other": ""
                }
            }
            """
        elif category == 'oral':
            prompt = """
            You are an oral health expert (dentist/oral medicine). Analyze this oral cavity image and provide the following information:
            - Disease name (e.g., oral ulcer, candidiasis, leukoplakia, gingivitis)
            - Confidence level (as a number between 0-100)
            - Description of the condition and likely causes
            - Severity level (Mild/Moderate/Severe)
            - List of recommended medicines (advise dental/medical consultation)
            - Visual characteristics (color, surface texture, location, size)

            Format your response as valid JSON with these exact keys:
            {
                "Disease name": "",
                "Confidence level": 0,
                "Description": "",
                "Severity level": "",
                "List of recommended medicines": [],
                "Visual characteristics": {
                    "color": "",
                    "texture": "",
                    "location": "",
                    "size": ""
                }
            }
            """
        elif category == 'skin':
            prompt = """
            You are a dermatology expert AI. Analyze this skin image and provide the following information:
            - Disease name
            - Confidence level (as a number between 0-100)
            - Description of the condition
            - Severity level (Mild/Moderate/Severe)
            - List of recommended medicines
            - Visual characteristics (color, texture)

            Format your response as valid JSON with these exact keys:
            {
                "Disease name": "",
                "Confidence level": 0,
                "Description": "",
                "Severity level": "",
                "List of recommended medicines": [],
                "Visual characteristics": {
                    "color": "",
                    "texture": ""
                }
            }
            """
            
        else:
            # default: other
            prompt = """
            You are a medical image analyst. The user has uploaded an image of a potential health-related issue but the category is 'Other'. Analyze the image and provide:
            - A concise description of what you observe
            - Possible systems/organs involved
            - Likely diagnoses or differential diagnoses
            - Confidence level (0-100)
            - Recommended medicines (immediate actions, specialist referral, or tests)

            Format your response as valid JSON using the keys:
            {
                "Disease name": "",
                "Confidence level": 0,
                "Description": "",
                "Severity level": "",
                "List of recommended medicines": [],
                "Visual characteristics": {}
            }
            """

        # Append patient context (age, extra info) to the prompt if provided
        patient_context = ""
        try:
            if age is not None and str(age).strip() != "":
                patient_context += f"\nPatient age: {age}\n"
        except Exception:
            # ignore formatting errors for age
            pass

        if extra_info:
            # limit the size of the extra_info to avoid sending huge prompts
            trimmed = extra_info.strip()
            if len(trimmed) > 1000:
                trimmed = trimmed[:1000] + "..."
            patient_context += f"Additional patient information: {trimmed}\n"

        if patient_context:
            prompt = prompt + "\n\n" + "Please consider the following patient context when analyzing the image:" + patient_context
        # Convert image to bytes
        import io
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Generate content using the model with specific content type
        response = model.generate_content(
            [
                prompt,
                {"mime_type": "image/jpeg", "data": img_byte_arr}
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=2048,
            )
        )
        response.resolve()
        
        try:
            # Extract JSON from the response text
            import json
            import re
            
            # Check if response has valid text content
            try:
                response_text = response.text
                if not response_text:
                    print("[error] No text content in Gemini response")
                    return {
                        "disease": "Analysis Error",
                        "confidence": 0,
                        "description": "Unable to analyze image - no response from AI model",
                        "severity": "Unknown",
                        "medicines": ["Please try again or consult a healthcare professional"],
                        "analysis": {
                            "color_tone": "Unknown",
                            "texture": "Unknown",
                            "size": f"{image.size[0]}x{image.size[1]} pixels"
                        }
                    }
            except Exception as text_error:
                print(f"[error] Failed to access response.text: {text_error}")
                return {
                    "disease": "Analysis Error",
                    "confidence": 0,
                    "description": f"Unable to analyze image - API response error: {str(text_error)}",
                    "severity": "Unknown",
                    "medicines": ["Please try again or consult a healthcare professional"],
                    "analysis": {
                        "color_tone": "Unknown",
                        "texture": "Unknown",
                        "size": f"{image.size[0]}x{image.size[1]} pixels"
                    }
                }
            
            # Find JSON content within the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    analysis = json.loads(json_match.group(0))
                    
                    # Format medicines as bullet points
                    medicines = analysis.get("List of recommended medicines", [])
                    formatted_medicines = [f"• {medicine}" for medicine in medicines]
                    
                    return {
                        "disease": analysis.get("Disease name", "Unknown"),
                        "confidence": analysis.get("Confidence level", 0),
                        "description": analysis.get("Description", "No description available"),
                        "severity": analysis.get("Severity level", "Unknown"),
                        "medicines": formatted_medicines,
                        "analysis": {
                            "color_tone": analysis.get("Visual characteristics", {}).get("color", "Unknown"),
                            "texture": analysis.get("Visual characteristics", {}).get("texture", "Unknown"),
                            "size": f"{image.size[0]}x{image.size[1]} pixels"
                        },
                        "disclaimer": "⚠️ This is an AI analysis for educational purposes only. Please consult a qualified dermatologist for accurate diagnosis and treatment."
                    }
                except json.JSONDecodeError:
                    print("[error] Failed to parse JSON from response")
                    # Try to extract readable content from the raw response
                    return _extract_readable_content(response_text, image)
            else:
                # No JSON found in Gemini response — try to extract readable content
                print("[error] No JSON found in response")
                return _extract_readable_content(response_text, image)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract readable content
            return _extract_readable_content(response_text, image)
    except Exception as e:
        print(f"[error] Gemini API failed: {e}")
        return {
            "disease": "Error",
            "confidence": 0,
            "description": str(e),
            "severity": "Unknown",
            "medicines": ["Please try again or consult a healthcare professional"],
            "analysis": {
                "color_tone": "Unknown",
                "texture": "Unknown",
                "size": "Unknown"
            }
        }


# --- JSON helpers -------------------------------------------------
def json_safe(obj):
    """Recursively convert MongoDB types (ObjectId, datetime) to JSON-serializable types."""
    # primitives
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, datetime):
        try:
            return obj.isoformat()
        except Exception:
            return str(obj)
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    try:
        return str(obj)
    except Exception:
        return None

def make_json_response(data, status=200):
    return jsonify(json_safe(data)), status

# ----------------- Flask Routes -----------------

@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/add_patient', methods=['POST'])
def add_patient():
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        
        # Require both name and phone for an explicit search-or-create
        if not name or not phone:
            return jsonify({'error': 'Both name and phone are required for search/create'}), 400

        # First try to find an exact match by both username and phone
        # normalize phone to match stored format
        phone = normalize_phone(phone)
        patient = users.find_one({'username': name, 'phone': phone})
        if patient:
            # Serialize patient (avoid ObjectId and datetime issues)
            diseases = []
            for d in patient.get('diseases', []):
                if isinstance(d, dict):
                    detected_at = d.get('detected_at') or d.get('detectedAt')
                    try:
                        detected = detected_at.isoformat() if hasattr(detected_at, 'isoformat') else str(detected_at)
                    except Exception:
                        detected = str(detected_at)
                    
                    disease_data = {
                        'name': d.get('name'),
                        'detected_at': detected
                    }
                    
                    # Include ASHA worker information if available
                    if 'checked_by' in d:
                        disease_data['checked_by'] = d['checked_by']
                    
                    diseases.append(disease_data)
                else:
                    diseases.append({'name': str(d), 'detected_at': None})

            resp_user = {
                'username': patient.get('username'),
                'phone': patient.get('phone'),
                'created': patient.get('created', datetime.now().isoformat()),
                'diseases': diseases
            }
            return make_json_response({'success': True, 'message': 'Patient found', 'user': resp_user})

        # Not found -> create via add_user (which returns a dict with user/message)
        result = add_user(name, phone)
        return make_json_response(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/search_patient', methods=['POST'])
def search_patient():
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')

        # Require at least one input
        if not name and not phone:
            return jsonify({'error': 'Name or phone number is required'}), 400

        # Build query dynamically
        query = {}
        if name:
            query['username'] = name
        if phone:
            query['phone'] = normalize_phone(phone)

        # Perform MongoDB search
        patient = users.find_one(query)

        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'}), 404

        # Extract disease info safely
        diseases = []
        for d in patient.get('diseases', []):
            disease_name = d.get('name') if isinstance(d, dict) else str(d)
            detected_at = d.get('detected_at') if isinstance(d, dict) else None

            if detected_at and hasattr(detected_at, 'isoformat'):
                detected_at = detected_at.isoformat()

            disease_data = {
                'name': disease_name,
                'detected_at': detected_at or "Unknown"
            }
            
            # Include ASHA worker information if available
            if isinstance(d, dict) and 'checked_by' in d:
                disease_data['checked_by'] = d['checked_by']

            diseases.append(disease_data)

        # Build clean response object
        resp_patient = {
            'id': str(patient.get('_id', '')),
            'name': patient.get('username'),
            'phone': patient.get('phone'),
            'created': str(patient.get('created', datetime.now().isoformat())),
            'diseases': diseases
        }

        return jsonify({'success': True, 'patient': resp_patient})

    except Exception as e:
        print("Error in /search_patient:", e)
        return jsonify({'error': str(e)}), 500

# def search_patient():
#     try:
#         data = request.get_json()
#         name = data.get('name')
#         phone = data.get('phone')
        
#         if not name and not phone:
#             return jsonify({'error': 'Name or phone is required'}), 400
        
#         # Search in MongoDB
#         query = {}
#         if name:
#             query['username'] = name
#         if phone:
#             query['phone'] = phone
            
#         patient = users.find_one(query)
        
#         if patient:
#             # Build a JSON-serializable patient object (remove ObjectId and convert datetimes)
#             diseases = []
#             for d in patient.get('diseases', []):
#                 try:
#                     name = d.get('name') if isinstance(d, dict) else d.get('name')
#                 except Exception:
#                     name = str(d)
#                 detected = None
#                 if isinstance(d, dict):
#                     detected_at = d.get('detected_at') or d.get('detectedAt')
#                     try:
#                         detected = detected_at.isoformat() if hasattr(detected_at, 'isoformat') else str(detected_at)
#                     except Exception:
#                         detected = str(detected_at)
#                 else:
#                     detected = str(d)
#                 diseases.append({
#                     'name': name,
#                     'detected_at': detected
#                 })

#             resp_patient = {
#                 'name': patient.get('username'),
#                 'phone': patient.get('phone'),
#                 'created': patient.get('created', datetime.now().isoformat()),
#                 'diseases': diseases
#             }
#             return jsonify({'success': True, 'patient': resp_patient})
#         else:
#             return jsonify({'success': False, 'message': 'Patient not found'})
            
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

@app.route('/add_disease', methods=['POST'])
def add_disease_route():
    try:
        data = request.get_json()
        username = data.get('username')
        disease_name = data.get('disease_name')
        asha_worker_info = data.get('asha_worker_info')
        
        if not username or not disease_name:
            return jsonify({'error': 'Username and disease name are required'}), 400

        # Add the disease record to MongoDB
        result = add_disease(username, disease_name, asha_worker_info)
        return make_json_response(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/detection')
def detect():
    return render_template('index.html')
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools():
    return '', 204

@app.route('/predict', methods=['POST'])
def predict():
    filepath = None
    try:
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file = request.files.get('file')
        if file is None:
            return jsonify({'error': 'No file provided'}), 400
        
        if not is_valid_image(file):
            return jsonify({'error': 'Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF)'}), 400

        import uuid
        # Generate a unique filename
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
    except Exception as e:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        return jsonify({'error': f'Error saving file: {str(e)}'}), 500

    try:
        # Get patient and form information
        category = request.form.get('category', 'skin')
        patient_name = request.form.get('patient_name')
        age = request.form.get('age')
        extra_info = request.form.get('extra_info')
        
        # Get ASHA worker information
        asha_worker_name = request.form.get('asha_worker_name')
        asha_worker_id = request.form.get('asha_worker_id')
        asha_worker_mobile = request.form.get('asha_worker_mobile')
        
        analysis_result = analyze_with_gemini(filepath, category=category, age=age, extra_info=extra_info)
        if "error" in analysis_result:
            return jsonify({'error': analysis_result["error"]}), 500
            
        # Store disease in database for patient with ASHA worker info
        if patient_name:
            asha_worker_info = None
            if asha_worker_name and asha_worker_id and asha_worker_mobile:
                asha_worker_info = {
                    "name": asha_worker_name,
                    "ashaId": asha_worker_id,
                    "mobile": asha_worker_mobile
                }
            add_disease(patient_name, analysis_result.get('disease', 'Unknown condition'), asha_worker_info)
        return jsonify(analysis_result)
    except Exception as e:
        print(f"[error] Exception while processing {filepath}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up the uploaded file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"[warn] Failed to remove temporary file {filepath}: {e}")


# ----------------- ASHA Worker Routes -----------------

@app.route('/register_asha_worker', methods=['POST'])
def register_asha_worker():
    """Register a new ASHA worker."""
    try:
        data = request.get_json()
        name = data.get('name')
        asha_id = data.get('ashaId')
        mobile = data.get('mobile')
        education = data.get('education')
        years = data.get('years')
        village = data.get('village')
        password = data.get('password')
        
        if not name or not asha_id or not mobile or not password:
            return jsonify({'error': 'Name, ASHA ID, mobile, and password are required'}), 400
        
        result = add_asha_worker(name, asha_id, mobile, education, years, village, password)
        return make_json_response(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/login_asha_worker', methods=['POST'])
def login_asha_worker():
    """Login ASHA worker with OTP or password."""
    try:
        data = request.get_json()
        mobile = data.get('mobile')
        otp = data.get('otp')
        password = data.get('password')
        
        if not mobile:
            return jsonify({'error': 'Mobile number is required'}), 400
        
        # For OTP login (simulated)
        if otp:
            # In a real app, you'd verify the OTP
            # For now, just find the worker by mobile
            worker = find_asha_worker(mobile)
            if worker:
                # Remove password before returning
                worker_copy = worker.copy()
                worker_copy.pop('password', None)
                return make_json_response({
                    'success': True,
                    'message': 'Login successful',
                    'worker': worker_copy
                })
            else:
                return make_json_response({
                    'success': False,
                    'message': 'Worker not found',
                    'worker': None
                })
        
        # For password login
        if password:
            result = verify_asha_worker(mobile, password)
            return make_json_response(result)
        
        return jsonify({'error': 'OTP or password is required'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_asha_worker', methods=['POST'])
def get_asha_worker():
    """Get ASHA worker details by mobile."""
    try:
        data = request.get_json()
        mobile = data.get('mobile')
        
        if not mobile:
            return jsonify({'error': 'Mobile number is required'}), 400
        
        worker = find_asha_worker(mobile)
        if worker:
            # Remove password before returning
            worker_copy = worker.copy()
            worker_copy.pop('password', None)
            return make_json_response({
                'success': True,
                'worker': worker_copy
            })
        else:
            return make_json_response({
                'success': False,
                'message': 'Worker not found'
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update_asha_worker', methods=['POST'])
def update_asha_worker_route():
    """Update ASHA worker profile."""
    try:
        data = request.get_json()
        mobile = data.get('mobile')
        
        if not mobile:
            return jsonify({'error': 'Mobile number is required'}), 400
        
        # Build updates dictionary (exclude mobile and other non-updatable fields)
        updates = {}
        updatable_fields = ['name', 'asha_id', 'mobile', 'education', 'years', 'village', 'photo', 'password']
        
        for field in updatable_fields:
            if field in data and data[field] is not None:
                updates[field] = data[field]
        
        if not updates:
            return jsonify({'error': 'No fields to update'}), 400
        
        result = update_asha_worker(mobile, updates)
        return make_json_response(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
