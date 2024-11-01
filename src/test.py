# test_yolo_server.py
import requests
import base64
import json

def load_image_as_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_predict_endpoint(image_path, model_type='yolo'):
    url = "http://127.0.0.1:5000/predict/yolo"
    image_base64 = load_image_as_base64(image_path)
    payload = {"image": image_base64}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Prediction Response:")
            print(json.dumps(response.json(), indent=4))
        else:
            print("Error: Received status code {}" % response.status_code)
            print(response.text)
    except Exception as e:
        print("Exception occurred: {}" % e)

if __name__ == "__main__":
    sample_image_path = "img.jpg"  # Replace with your image path
    test_predict_endpoint(sample_image_path, model_type='yolo')  # Change to 'tflite' or 'both' as needed
