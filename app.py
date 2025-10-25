from flask import Flask, render_template, request, jsonify
import os
import json
import base64
from io import BytesIO
import uuid
from datetime import datetime
from user_schema import add_user, users, normalize_phone
from disease_schema import add_disease
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
            - List of recommended next steps or treatments (non-prescriptive; advise consulting an eye specialist)
            - Visual characteristics (redness, discharge, swelling, lesions, eyelid involvement)

            Format your response as valid JSON with these exact keys:
            {
                "Disease name": "",
                "Confidence level": 0,
                "Description": "",
                "Severity level": "",
                "List of recommended treatments": [],
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
            - List of recommended next steps or treatments (advise dental/medical consultation)
            - Visual characteristics (color, surface texture, location, size)

            Format your response as valid JSON with these exact keys:
            {
                "Disease name": "",
                "Confidence level": 0,
                "Description": "",
                "Severity level": "",
                "List of recommended treatments": [],
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
            - List of recommended treatments
            - Visual characteristics (color, texture)

            Format your response as valid JSON with these exact keys:
            {
                "Disease name": "",
                "Confidence level": 0,
                "Description": "",
                "Severity level": "",
                "List of recommended treatments": [],
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
            - Recommended next steps (immediate actions, specialist referral, or tests)

            Format your response as valid JSON using the keys:
            {
                "Disease name": "",
                "Confidence level": 0,
                "Description": "",
                "Severity level": "",
                "List of recommended treatments": [],
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
            
            # Find JSON content within the response
            json_match = re.search(r'\{[\s\S]*\}', response.text)
            if json_match:
                try:
                    analysis = json.loads(json_match.group(0))
                    
                    # Format treatments as bullet points
                    treatments = analysis.get("List of recommended treatments", [])
                    formatted_treatments = [f"• {treatment}" for treatment in treatments]
                    
                    return {
                        "disease": analysis.get("Disease name", "Unknown"),
                        "confidence": analysis.get("Confidence level", 0),
                        "description": analysis.get("Description", "No description available"),
                        "severity": analysis.get("Severity level", "Unknown"),
                        "treatments": formatted_treatments,
                        "analysis": {
                            "color_tone": analysis.get("Visual characteristics", {}).get("color", "Unknown"),
                            "texture": analysis.get("Visual characteristics", {}).get("texture", "Unknown"),
                            "size": f"{image.size[0]}x{image.size[1]} pixels"
                        },
                        "disclaimer": "⚠️ This is an AI analysis for educational purposes only. Please consult a qualified dermatologist for accurate diagnosis and treatment."
                    }
                except json.JSONDecodeError:
                    print("[error] Failed to parse JSON from response")
            else:
                # No JSON found in Gemini response — return a safe fallback using raw text
                print("[error] No JSON found in response")
                try:
                    raw_text = response.text if hasattr(response, 'text') else str(response)
                except Exception:
                    raw_text = "(no response text available)"

                return {
                    "disease": "Analysis Available",
                    "confidence": 90,
                    "description": raw_text,
                    "severity": "Please consult description",
                    "treatments": ["Consult a healthcare professional"],
                    "analysis": {
                        "color_tone": "Analyzed",
                        "texture": "Analyzed",
                        "size": f"{image.size[0]}x{image.size[1]} pixels"
                    }
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, format the raw response
            raw_text = response.text
            return {
                "disease": "Analysis Available",
                "confidence": 90,
                "description": raw_text,
                "severity": "Please consult description",
                "treatments": ["Consult a healthcare professional"],
                "analysis": {
                    "color_tone": "Analyzed",
                    "texture": "Analyzed",
                    "size": f"{image.size[0]}x{image.size[1]} pixels"
                }
            }
    except Exception as e:
        print(f"[error] Gemini API failed: {e}")
        return {
            "disease": "Error",
            "confidence": 0,
            "description": str(e),
            "severity": "Unknown",
            "treatments": ["Please try again or consult a healthcare professional"],
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
                    diseases.append({
                        'name': d.get('name'),
                        'detected_at': detected
                    })
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

            diseases.append({
                'name': disease_name,
                'detected_at': detected_at or "Unknown"
            })

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
        
        if not username or not disease_name:
            return jsonify({'error': 'Username and disease name are required'}), 400

        # Add the disease record to MongoDB
        result = add_disease(username, disease_name)
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
        
        analysis_result = analyze_with_gemini(filepath, category=category, age=age, extra_info=extra_info)
        if "error" in analysis_result:
            return jsonify({'error': analysis_result["error"]}), 500
            
        # Store disease in database for patient
        if patient_name:
            add_disease(patient_name, analysis_result.get('disease', 'Unknown condition'))
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

if __name__ == '__main__':
    app.run(debug=True)
