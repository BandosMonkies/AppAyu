from flask import Flask, render_template, request, jsonify
import os
import json
import base64
from io import BytesIO
import uuid

# --- Gemini Setup ---
try:
    import google.generativeai as genai
    from PIL import Image
    GEMINI_API_KEY = os.environ.get(
        "GEMINI_API_KEY", 
        "AIzaSyBM_PdYP9U-rTT5K6GDkATzna9iCsWNDZs"  # replace with your actual API key
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

def analyze_with_gemini(image_path):
    if not GEMINI_ENABLED:
        return {"error": "Gemini AI not enabled"}

    try:
        # Load and prepare the image
        image = Image.open(image_path)
        
        # Convert image to RGB mode (required by Gemini)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
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
                print("[error] No JSON found in response")
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

# ----------------- Flask Routes -----------------

@app.route('/')
def home():
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
        analysis_result = analyze_with_gemini(filepath)
        if "error" in analysis_result:
            return jsonify({'error': analysis_result["error"]}), 500
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
