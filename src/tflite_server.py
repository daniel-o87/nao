import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
import logging
import base64
from flask import Flask, request, jsonify
import numpy as np
import cv2
import time
from ultralytics import YOLO  # Import YOLO model

# Load the TensorFlow Lite model
interpreter = tf.lite.Interpreter(model_path="./../models/v4.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load the YOLO model
yolo_model = YOLO("./../models/yolo11n.pt") 

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Preprocess image for the TensorFlow Lite model
def preprocess_image(image):
    """Preprocess the image to fit the TensorFlow Lite model's input size."""
    image_resized = cv2.resize(image, (224, 224))  # Assuming input size is 224x224
    image_normalized = image_resized.astype('float32') / 255.0
    image_reshaped = np.expand_dims(image_normalized, axis=0)  # Add batch dimension
    return image_reshaped

# Run inference with TensorFlow Lite model
def predict_tflite(image):
    """Run inference using the TensorFlow Lite model."""
    interpreter.set_tensor(input_details[0]['index'], image)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

# Run inference with YOLO model
def predict_yolo(image):
    """Run YOLO object detection."""
    results = yolo_model(image)  # YOLO returns results object
    predictions = []
    for r in results:
        # Convert each detected object to a dictionary
        for obj in r.boxes.data.tolist():
            predictions.append({
                "confidence": obj[4],
                "class": int(obj[5]),
                "bounding_box": [int(obj[0]), int(obj[1]), int(obj[2]), int(obj[3])]
            })
    return predictions

@app.route("/predict", methods=["POST"])
def predict_endpoint():
    data = request.json
    image_base64 = data['image']
    
    # Decode the base64 image
    image_bytes = base64.b64decode(image_base64)
    image_np = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    
    # Preprocess for TensorFlow Lite model
    preprocessed_image = preprocess_image(image)
    
    # Run TensorFlow Lite inference
    tflite_result = predict_tflite(preprocessed_image)
    
    # Run YOLO inference
    yolo_result = predict_yolo(image)
    print(f"WE ARE RETURNING {yolo_result}")
    
    # Return the results from both models
    return jsonify({
        'tflite_prediction': tflite_result.tolist(), 
        'yolo_prediction': yolo_result
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
