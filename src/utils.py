import cv2
import numpy as np
import base64
import requests
import os
import time

def capture_frame(video_service, video_client):
        image = video_service.getImageRemote(video_client)
        if image is None:
            print("Failed to retrieve image, restarting video client...")
            # Restart video client if image retrieval fails
            return None

        image_width = image[0]
        image_height = image[1]
        image_array = np.frombuffer(image[6], dtype=np.uint8).reshape((image_height, image_width, 3))
        return image_array

# Python2 doesnt work with tensorflow, or it does but i am too lazy to make it work. call python3 tflite_server.py prior to this and enter IP
def send_image_to_server(image):
    """Send captured image to the Flask server and receive a prediction."""
    _, image_encoded = cv2.imencode('.jpg', image)
    image_base64 = base64.b64encode(image_encoded).decode('utf-8')  # Encode as base64

    try:
        response = requests.post(
            "http://127.0.0.1:5000/predict",  
            json={"image": image_base64}
        )
        if response.status_code == 200:
            return response.json()['yolo_prediction']
        else:
            prediction = response.json().get('prediction', [0])
            return prediction[0]

    except Exception as e:
        print("Error sending image to server:", e)
        return None

def save_image(image, directory, prefix="image"):
    if not os.path.exists(directory):
        os.makedirs(directory)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, "{0}_{1}.jpg".format(prefix, timestamp))
    cv2.imwrite(filename, image)
    num_files = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    print("Saved: {0}, Total: {1}".format(filename, num_files))
    return filename, num_files
