import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import logging
import base64
from flask import Flask, request, jsonify
import numpy as np
import cv2
import time
import torch

# Configure logging
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

def load_yolo_model(model_path):
    """Load YOLO model using torch hub."""
    try:
        model = torch.hub.load('WongKinYiu/yolov7', 'custom', model_path, trust_repo=True)
        model.eval()
        if torch.cuda.is_available():
            model.cuda()
        return model
    except Exception as e:
        print(f"Error loading YOLO model: {str(e)}")
        return None

# Load both models at startup
try:
    interpreter = tf.lite.Interpreter(model_path="./../models/peekaboo_model.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print("TFLite model loaded successfully")
except Exception as e:
    print(f"Error loading TFLite model: {str(e)}")
    interpreter = None

try:
    yolo_model = load_yolo_model("./../models/yolov7.pt")
    print("YOLO model loaded successfully")
except Exception as e:
    print(f"Error loading YOLO model: {str(e)}")
    yolo_model = None

def preprocess_image(image, target_size=(224, 224)):
    """Preprocess the image to fit the TensorFlow Lite model's input size."""
    image_resized = cv2.resize(image, target_size)
    image_normalized = image_resized.astype('float32') / 255.0
    image_reshaped = np.expand_dims(image_normalized, axis=0)
    return image_reshaped

def predict_tflite(image):
    """Run inference using the TensorFlow Lite model."""
    try:
        interpreter.set_tensor(input_details[0]['index'], image)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])
        return output_data
    except Exception as e:
        print(f"Error in TFLite prediction: {str(e)}")
        return None

def predict_yolo(image):
    """Run YOLO object detection."""
    try:
        results = yolo_model(image)
        predictions = []
        
        # Convert detections to the desired format
        for det in results.xyxy[0]:  # Get detections for first image
            if len(det) >= 6:  # Ensure detection has all required values
                x1, y1, x2, y2, conf, cls = det[:6]
                predictions.append({
                    "confidence": float(conf),
                    "class": int(cls),
                    "bounding_box": [
                        float(x1), float(y1), float(x2), float(y2)
                    ]
                })
        return predictions
    except Exception as e:
        print(f"Error in YOLO prediction: {str(e)}")
        return None

@app.route("/predict/<model_type>", methods=["POST"])
def predict_endpoint(model_type):
    """
    Endpoint that takes model type as part of the URL.
    """
    print(f"\nReceived prediction request for model: {model_type}")  # Debug print
    
    if model_type not in ['tflite', 'yolo', 'both']:
        print(f"Invalid model type: {model_type}")  # Debug print
        return jsonify({'error': 'Invalid model type. Use tflite, yolo, or both'}), 400
    
    try:
        data = request.json
        if not data or 'image' not in data:
            print("No image data in request")  # Debug print
            return jsonify({'error': 'No image data provided'}), 400
            
        image_base64 = data['image']
        
        # Decode the base64 image
        print("Decoding image...")  # Debug print
        image_bytes = base64.b64decode(image_base64)
        image_np = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        
        if image is None:
            print("Failed to decode image")  # Debug print
            return jsonify({'error': 'Failed to decode image'}), 400
            
        print(f"Image shape: {image.shape}")  # Debug print
        
        response = {}
        
        # Run predictions based on requested model
        if model_type in ['yolo', 'both']:
            if yolo_model is not None:
                print("Running YOLO prediction...")  # Debug print
                yolo_result = predict_yolo(image)
                print(f"YOLO result: {yolo_result}")  # Debug print
                if yolo_result is not None:
                    response['yolo_prediction'] = yolo_result
                else:
                    response['yolo_error'] = 'YOLO prediction failed'
            else:
                print("YOLO model not loaded")  # Debug print
                response['yolo_error'] = 'YOLO model not loaded'
        
        print(f"Sending response: {response}")  # Debug print
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in predict_endpoint: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """Check server status and available models."""
    return jsonify({
        'status': 'running',
        'available_models': {
            'tflite': interpreter is not None,
            'yolo': yolo_model is not None
        },
        'gpu_available': torch.cuda.is_available()
    })

if __name__ == "__main__":
    print("\nServer starting...")
    print("\nModel Status:")
    print(f"- TFLite model: {'Loaded' if interpreter is not None else 'Not loaded'}")
    print(f"- YOLO model: {'Loaded' if yolo_model is not None else 'Not loaded'}")
    print(f"- GPU available: {torch.cuda.is_available()}")
    print("\nAvailable endpoints:")
    print("- POST /predict/tflite : Use TFLite model")
    print("- POST /predict/yolo   : Use YOLO model")
    print("- POST /predict/both   : Use both models")
    print("- GET  /status        : Check server status")
    
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
