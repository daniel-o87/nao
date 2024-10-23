import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import logging
import base64
from flask import Flask, request, jsonify
import numpy as np
import cv2
import time
from ultralytics import YOLO

# Load both models at startup
interpreter = tf.lite.Interpreter(model_path="./../models/v4.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

yolo_model = YOLO("./../models/yolo11n.pt")

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)

def preprocess_image(image):
    """Preprocess the image to fit the TensorFlow Lite model's input size."""
    image_resized = cv2.resize(image, (224, 224))
    image_normalized = image_resized.astype('float32') / 255.0
    image_reshaped = np.expand_dims(image_normalized, axis=0)
    return image_reshaped

def predict_tflite(image):
    """Run inference using the TensorFlow Lite model."""
    interpreter.set_tensor(input_details[0]['index'], image)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

def predict_yolo(image):
    """Run YOLO object detection."""
    results = yolo_model(image)
    predictions = []
    for r in results:
        for obj in r.boxes.data.tolist():
            predictions.append({
                "confidence": obj[4],
                "class": int(obj[5]),
                "bounding_box": [int(obj[0]), int(obj[1]), int(obj[2]), int(obj[3])]
            })
    return predictions

@app.route("/predict/<model_type>", methods=["POST"])
def predict_endpoint(model_type):
    """
    Endpoint that takes model type as part of the URL.
    Usage: 
    - /predict/tflite for TFLite model
    - /predict/yolo for YOLO model
    - /predict/both for both models
    """
    if model_type not in ['tflite', 'yolo', 'both']:
        return jsonify({'error': 'Invalid model type. Use tflite, yolo, or both'}), 400
    
    data = request.json
    image_base64 = data['image']
    
    # Decode the base64 image
    image_bytes = base64.b64decode(image_base64)
    image_np = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    
    response = {}
    
    # Run predictions based on requested model
    if model_type in ['tflite', 'both']:
        preprocessed_image = preprocess_image(image)
        tflite_result = predict_tflite(preprocessed_image)
        response['tflite_prediction'] = tflite_result.tolist()
        
    if model_type in ['yolo', 'both']:
        yolo_result = predict_yolo(image)
        response['yolo_prediction'] = yolo_result
        print(f"WE ARE RETURNING {yolo_result}")
    
    return jsonify(response)

# Add an endpoint to check server status and available models
@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        'status': 'running',
        'available_models': {
            'tflite': interpreter is not None,
            'yolo': yolo_model is not None
        }
    })

if __name__ == "__main__":
    print("Server starting with both models loaded")
    print("Available endpoints:")
    print("- POST /predict/tflite : Use TFLite model")
    print("- POST /predict/yolo   : Use YOLO model")
    print("- POST /predict/both   : Use both models")
    print("- GET  /status        : Check server status")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
