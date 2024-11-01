import cv2
import numpy as np
import base64
import requests
import os
import time

def capture_frame(video_service, video_client):
    """Optimized frame capture from NAO's video service."""
    try:
        image = video_service.getImageRemote(video_client)
        if image is None or len(image) < 7:
            return None
            
        # Get image data directly without intermediate steps
        return np.frombuffer(image[6], dtype=np.uint8).reshape((image[1], image[0], 3))
            
    except Exception as e:
        print("Error capturing frame: {}".format(e))
        return None

def send_image_to_server(image, mode):
    """Optimized image sending to server."""
    try:
        # Resize image before sending to reduce network load
        small_image = cv2.resize(image, (320, 240))
        _, buffer = cv2.imencode('.jpg', small_image, [cv2.IMWRITE_JPEG_QUALITY, 80])
        image_base64 = base64.b64encode(buffer.tostring())
        
        url = "http://127.0.0.1:5000/predict/%s" % mode
        
        response = requests.post(
            url,  
            json={"image": image_base64},
            timeout=0.1  # Add timeout to prevent hanging
        )
        
        if response.status_code == 200:
            return response.json()
        return None
            
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return None
    except Exception as e:
        print("Error sending image to server: {}".format(e))
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
