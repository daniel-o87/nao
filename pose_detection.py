#!/usr/bin/env python3

import cv2
import mediapipe as mp
import numpy as np
import socket
import json
import time
import os
import signal

class HeadDetectionServer:
    def __init__(self, host='127.0.0.1', port=12345):
        # Initialize MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Initialize socket server with reuse address option
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((host, port))
            self.server.listen(1)
            print(f"Server listening on {host}:{port}")
        except Exception as e:
            print(f"Error binding to port: {e}")
            self.cleanup()
            raise

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.server.close()
            self.pose.close()
        except:
            pass
    
    def calculate_head_angles(self, landmarks):
        """Calculate head angles from nose and eyes position"""
        if not landmarks:
            return None
        
        # Get head landmarks
        nose = landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
        left_eye = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_EYE]
        right_eye = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_EYE]

        #print(f"Nose {nose}\nLeft Eye {left_eye}\nRight Eye {right_eye}\n================================")
        
        # Calculate head angles
        yaw = np.arctan2(nose.x - (left_eye.x + right_eye.x)/2, 0.3)
        pitch = np.arctan2(nose.y - (left_eye.y + right_eye.y)/2, 0.3)

        print(f"Pitch {pitch}\nYaw {yaw}\n\n")
        
        return {
            'yaw': float(yaw),
            'pitch': float(pitch)
        }
        
    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera")
            self.cleanup()
            return

        print("Waiting for client connection...")
        try:
            client, addr = self.server.accept()
            print(f"Connected to client: {addr}")
        except Exception as e:
            print(f"Error accepting connection: {e}")
            self.cleanup()
            return
        
        try:
            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    continue
                
                # Process image
                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                results = self.pose.process(image)
                
                # Calculate and send head angles
                angles = self.calculate_head_angles(results.pose_landmarks)
                if angles:
                    try:
                        message = json.dumps(angles) + '\n'
                        client.send(message.encode())
                    except:
                        break
                
                # Display debug view
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                if results.pose_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(
                        image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                cv2.imshow('Head Detection', image)
                
                if cv2.waitKey(5) & 0xFF == 27:
                    break
                    
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            client.close()
            self.cleanup()

def find_and_kill_existing_process(port):
    """Find and kill any process using the specified port"""
    try:
        # Using lsof to find process using the port
        cmd = f"lsof -ti:{port}"
        pid = os.popen(cmd).read().strip()
        if pid:
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(1)  # Wait for process to terminate
            print(f"Killed existing process on port {port}")
    except:
        pass

if __name__ == "__main__":
    PORT = 12345
    find_and_kill_existing_process(PORT)
    server = HeadDetectionServer(port=PORT)
    server.run()
