import Tkinter as tk
import numpy as np
import tkMessageBox as messagebox
import threading
from PIL import Image, ImageTk
import cv2
import time
import requests
import base64
from robot import NaoRobot
from utils import capture_frame, save_image, send_image_to_server

def load_class_names(filename):
    with open(filename, "r") as f:
        class_names = f.read().splitlines()
    return class_names

class_names = load_class_names('./../models/coco.names')

class NaoControlGUI:
    def __init__(self, root, robot, mode):
        self.root = root
        self.robot = robot
        self.mode = mode
        # Initialize services from the robot instance
        self.motion_service = self.robot.motion_service
        self.posture_service = self.robot.posture_service
        self.video_service = self.robot.video_service
        self.video_client = self.robot.video_client
        self.battery_service = self.robot.battery_service
        self.tts = self.robot.tts
        self.tts.setParameter("defaultVoiceSpeed", 100)
        self.last_state_covered = False

        self.motion_service.wakeUp()
        self.posture_service.goToPosture('StandInit', 0.50)

        self.root.title("NAO Robot Control")
        self.root.geometry("600x600")

        instructions = tk.Label(
            root,
            text="Use WASD to move, Q/E to rotate.\nUse arrow keys to move the head.\nPress 'c' to save as covered, 'u' to save as uncovered.\nPress Esc to exit.",
            font=("Helvetica", 12),
        )

        instructions.grid(row=0, column=0, columnspan=4, pady=20, sticky="nsew")

        # Add posture buttons using grid
        sit_button = tk.Button(root, text="Sit", command=self.robot.make_robot_sit, font=("Helvetica", 12))
        sit_button.grid(row=1, column=0, padx=10, pady=10)

        stand_button = tk.Button(root, text="Stand", command=self.robot.make_robot_stand, font=("Helvetica", 12))
        stand_button.grid(row=1, column=1, padx=10, pady=10)

        superman_button = tk.Button(root, text="Superman", command=self.robot.superman, font=("Helvetica", 12))
        superman_button.grid(row=1, column=2, padx=10, pady=10)

        crouch_button = tk.Button(root, text="Crouch", command=self.robot.make_robot_crouch, font=("Helvetica", 12))
        crouch_button.grid(row=1, column=3, padx=10, pady=10)

        # Text input for TTS with focus handling
        self.text_entry = tk.Entry(root, width=50, font=("Helvetica", 12))
        self.text_entry.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        self.robot.assign_value(self.text_entry)

        speak_button = tk.Button(root, text="Speak", command=self.speak_text, font=("Helvetica", 12))
        speak_button.grid(row=2, column=3, padx=10, pady=10)

        # Video feed label
        self.video_label = tk.Label(root)
        self.video_label.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Create a canvas to display the battery status
        self.battery_label = tk.Label(root, text="Battery Level: 0%", font=("Helvetica", 12))
        self.battery_label.grid(row=4, column=0, columnspan=4, padx=10, pady=10)

        self.canvas = tk.Canvas(root, width=200, height=50, bg="white")
        self.canvas.grid(row=5, column=0, columnspan=4, padx=10, pady=10)
        self.battery_bar = self.canvas.create_rectangle(10, 10, 10, 40, fill="green")

        # Add click handler to root window to unfocus text entry
        root.bind('<Button-1>', self.unfocus_text_entry)
        # Add handler for text entry to stop propagation when clicked
        self.text_entry.bind('<Button-1>', lambda e: e.widget.focus_set() or 'break')
        # Add handler for video label to unfocus text entry
        self.video_label.bind('<Button-1>', self.unfocus_text_entry)

        # Bind key events
        self.root.bind('<KeyPress>', self.robot.on_key_press)
        self.root.bind('<KeyRelease>', self.robot.on_key_release)
        self.root.bind('<Escape>', self.handle_escape_event)

        # Add cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)

        self.tts.say("Hello RAIR LAB! I've gained consciousness.")

        self.update_battery_status()  # Start battery updates
        self.root.after(50, self.update_video_stream)  # Start video stream with slight delay
        self.root.after(50, self.initialize_robot_movement)  # Start robot movement updates

    def update_video_stream(self):
        """Update the video stream with error handling."""
        try:
            # Capture a frame from the NAO bot
            image = capture_frame(self.video_service, self.video_client)
            
            if image is None:
                self.root.after(100, self.update_video_stream)
                return
                

            image_rgb = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2RGB)
            # Get prediction if image capture was successful
            prediction = send_image_to_server(image, self.mode)
            
            if prediction:
                if self.mode == 'yolo':
                    try:
                        image = self.annotate_image(image_rgb, prediction, self.mode)  # Pass self.mode here
                    except Exception as e:
                        print("Error annotating image: {}".format(e))
                        
                elif self.mode == 'tflite':
                    try:
                        ans = prediction['tflite_prediction'][0][0]
                        if ans < 0.5:
                            self.last_state_covered = True
                        elif self.last_state_covered and ans >= 0.5:
                            self.tts.say("Peekaboo!")
                            self.last_state_covered = False
                    except Exception as e:
                        print("Error processing TFLite prediction: {}".format(e))
                elif self.mode == "face":
                    try:
                        image = self.annotate_image(image_rgb, prediction, self.mode)  # Pass self.mode here
                    except Exception as e:
                        print("Error annotating image: {}".format(e))
            
            # Convert and display image
            try:
                img = Image.fromarray(image)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            except Exception as e:
                print("Error updating display: {}".format(e))
                
            # Schedule next update
            self.root.after(50, self.update_video_stream)
            
        except Exception as e:
            print("Error in video stream update: {}".format(e))
            self.root.after(100, self.update_video_stream)
    """
    def annotate_image(self, image, yolo_results):
        try:
            # Cell phone class ID in COCO dataset is 67
            CELL_PHONE_CLASS = 67
            # Minimum confidence threshold
            CONFIDENCE_THRESHOLD = 0.4
            
            # Check if yolo_results is a dictionary and get the predictions list
            if isinstance(yolo_results, dict) and 'yolo_prediction' in yolo_results:
                predictions = yolo_results['yolo_prediction']
            else:
                return image
                
            # Iterate through the list of predictions
            for result in predictions:
                try:
                    confidence = float(result['confidence'])
                    class_id = int(result['class'])
                    
                    # Skip if not a cell phone or confidence too low
                    if class_id != CELL_PHONE_CLASS or confidence < CONFIDENCE_THRESHOLD:
                        continue
                        
                    bbox = result['bounding_box']
                    if not bbox or len(bbox) != 4:
                        continue
                    
                    # Extract coordinates and ensure they're integers
                    x1, y1, x2, y2 = map(int, bbox)
                    
                    # Color based on confidence (green gets brighter with confidence)
                    color_intensity = int(255 * min(confidence + 0.2, 1.0))
                    box_color = (0, color_intensity, 0)
                    
                    cv2.rectangle(image, (x1, y1), (x2, y2), box_color, 3)
                    
                    label = "Phone: {}%" % confidence
                    
                    # Get label size for background rectangle
                    (label_width, label_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                    
                    # Draw background rectangle for label
                    cv2.rectangle(
                        image,
                        (x1, y1 - label_height - 10),
                        (x1 + label_width + 10, y1),
                        box_color,
                        cv2.FILLED
                    )
                    
                    # Draw white text for better visibility
                    cv2.putText(
                        image,
                        label,
                        (x1 + 5, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,    # Larger font scale
                        (255, 255, 255),  # White text
                        2      # Thicker text
                    )
                    
                    # Debug print for successful detection
                    print("Detected phone with confidence: {}%" % confidence)
                    
                except Exception as e:
                    print("Error processing individual result: {}" % e)
                    continue
                    
        except Exception as e:
            print("Error in main annotation process: {}" % e)
            
        return image
    """
    def annotate_image(self, image, server_results, mode):
        """Annotate image based on detection results."""
        try:
            if mode == 'yolo' and 'yolo_prediction' in server_results:
                predictions = server_results['yolo_prediction']
                
                for result in predictions:
                    try:
                        confidence = float(result['confidence'])
                        class_id = int(result['class'])
                        bbox = result['bounding_box']
                        
                        if not bbox or len(bbox) != 4:
                            print("Invalid bounding box:", bbox)
                            continue
                        
                        top_left = (int(bbox[0]), int(bbox[1]))
                        bottom_right = (int(bbox[2]), int(bbox[3]))
                        
                        class_name = class_names[class_id] if class_id < len(class_names) else "Unknown"
                        
                        cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
                        
                        label = "{0}: {1:.2f}".format(class_name, confidence)
                        cv2.putText(image, label, (top_left[0], top_left[1] - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                    except Exception as e:
                        print("Error processing YOLO result: {}".format(e))
                        continue
                        
            elif mode == 'face':
                if mode == 'face':
                    #print('Processing face annotation')
                    try:
                        face_locations = server_results['face_locations']
                        #print("Received face locations: {}".format(face_locations))
                        
                        if not face_locations:
                            print("No faces detected")
                            return image
                            
                        for face_loc in face_locations:
                            try:
                                top, right, bottom, left = face_loc
                                
                                cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
                                
                                cv2.putText(image, "Face", (left, top - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                                #print("Drew face at: ({}, {}, {}, {})".format(left, top, right, bottom))
                            except Exception as e:
                                print("Error drawing individual face: {}".format(str(e)))
                                continue
                            
                    except Exception as e:
                        print("Error processing face results: {}".format(str(e)))
                        import traceback
                        traceback.print_exc()
                              
        except Exception as e:
            print("Error in image annotation: {}".format(str(e)))
            import traceback
            traceback.print_exc()
            
        return image

    def update_battery_status(self):
        battery_charge = self.battery_service.getBatteryCharge()
        self.battery_label.config(text="Battery Level: {}%".format(battery_charge))
        battery_width = 10 + (battery_charge * 1.8)
        self.canvas.coords(self.battery_bar, 10, 10, battery_width, 40)
        self.root.after(10000, self.update_battery_status)

    def initialize_robot_movement(self):
        """Update robot movement and schedule next update."""
        try:
            self.robot.update_robot_movement()
            self.root.after(10, self.initialize_robot_movement)
        except Exception as e:
            print("Error in robot movement: {}".format(e))
            # Try again after error
            self.root.after(10, self.initialize_robot_movement)

    def initialize_image_prediction(self):
        self.update_video_stream()
        self.root.after(1000, self.update_video_stream)

    def speak_text(self):
        text = self.text_entry.get()
        if text.strip() == "":
            messagebox.showwarning("Input Error", "Please enter text to speak.")
            return
        
        volume_control = "\\vol=100\\"
        text_with_volume = "{0}{1}".format(volume_control, text)
        
        # Use a separate thread to prevent blocking the GUI
        threading.Thread(target=self.robot.tts.say, args=(text_with_volume,)).start()

    def handle_escape_event(self, event):
        self.root.quit()
        self.robot.shutdown()

    def cleanup(self):
        try:
            if hasattr(self, 'video_client'):
                self.video_service.unsubscribe(self.video_client)
            if hasattr(self, 'root'):
                for after_id in self.root.tk.call('after', 'info'):
                    self.root.after_cancel(after_id)
            self.robot.shutdown()
            self.root.quit()
        except Exception as e:
            print("Error during cleanup: {}".format(e))

    def unfocus_text_entry(self, event=None):
        # Only unfocus if we didn't click the text entry itself
        if event and event.widget != self.text_entry:
            # Move focus to the main window
            self.root.focus_set()
            return 'break'  # Prevent event propagation
