import cv2
import numpy as np

# Initialize camera
cap = cv2.VideoCapture(0)
print("Camera Connected")

# Try different dictionaries
DICTIONARIES = [
    cv2.aruco.DICT_4X4_50,
    cv2.aruco.DICT_4X4_100,
    cv2.aruco.DICT_4X4_250,
    cv2.aruco.DICT_4X4_1000,
    cv2.aruco.DICT_5X5_50,
    cv2.aruco.DICT_5X5_100,
    cv2.aruco.DICT_5X5_250,
    cv2.aruco.DICT_5X5_1000,
    cv2.aruco.DICT_6X6_50,
    cv2.aruco.DICT_6X6_100,
    cv2.aruco.DICT_6X6_250,
    cv2.aruco.DICT_6X6_1000,
    cv2.aruco.DICT_7X7_50,
    cv2.aruco.DICT_7X7_100,
    cv2.aruco.DICT_7X7_250,
    cv2.aruco.DICT_7X7_1000
]

current_dict_idx = 0
aruco_dict = cv2.aruco.getPredefinedDictionary(DICTIONARIES[current_dict_idx])
parameters = cv2.aruco.DetectorParameters()

# Modify parameters to be more lenient
parameters.adaptiveThreshWinSizeMin = 3
parameters.adaptiveThreshWinSizeMax = 23
parameters.adaptiveThreshWinSizeStep = 10
parameters.adaptiveThreshConstant = 7
parameters.minMarkerPerimeterRate = 0.03
parameters.maxMarkerPerimeterRate = 4.0
parameters.polygonalApproxAccuracyRate = 0.03
parameters.minCornerDistanceRate = 0.05
parameters.minDistanceToBorder = 3

detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

print("Press 'n' to cycle through different ArUco dictionaries")
print("Press 'q' to quit")

try:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Failed to capture frame")
            continue

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Optional: Apply some preprocessing
        gray = cv2.GaussianBlur(gray, (5,5), 0)
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Detect markers
        corners, ids, rejected = detector.detectMarkers(gray)

        # Draw both accepted and rejected markers
        image = cv2.aruco.drawDetectedMarkers(image.copy(), corners, ids)
        image = cv2.aruco.drawDetectedMarkers(image, rejected, None, (100, 0, 255))

        # Display current dictionary type
        dict_name = f"Dictionary {current_dict_idx}: {DICTIONARIES[current_dict_idx]}"
        cv2.putText(image, dict_name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # If markers detected, print info
        if ids is not None:
            for i in range(len(ids)):
                print(f"\rDetected marker {ids[i]} at corners {corners[i][0]}", end='')

        # Display image
        cv2.imshow('ArUco Detection Debug', image)

        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('n'):
            current_dict_idx = (current_dict_idx + 1) % len(DICTIONARIES)
            aruco_dict = cv2.aruco.getPredefinedDictionary(DICTIONARIES[current_dict_idx])
            detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
            print(f"\nSwitched to dictionary {DICTIONARIES[current_dict_idx]}")

except Exception as e:
    print(f"Error: {e}")
finally:
    print("\nClosing camera")
    cap.release()
    cv2.destroyAllWindows()
