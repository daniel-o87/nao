# gui.py

import Tkinter as tk
import tkMessageBox as messagebox
import threading
from PIL import Image, ImageTk
import cv2
import time
import requests
import base64
from robot import NaoRobot
from utils import capture_frame, save_image, send_image_to_server

class NaoControlGUI:
    def __init__(self, root, robot):

        self.root = root
        self.robot = robot

        # Initialize services from the robot instance
        self.motion_service = self.robot.motion_service
        self.posture_service = self.robot.posture_service
        self.video_service = self.robot.video_service
        self.video_client = self.robot.video_client
        self.battery_service = self.robot.battery_service
        self.tts = self.robot.tts
        self.tts.setParameter("defaultVoiceSpeed", 100)



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

        # Text input for TTS
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
        # Bind key events
        self.root.bind('<KeyPress>', self.robot.on_key_press)
        self.root.bind('<KeyRelease>', self.robot.on_key_release)
        # Bind the function to the event
        self.root.bind('<Escape>', self.handle_escape_event)

        #self.tts.say("Hello RAIR LAB! I've gained conciousness.")


        self.update_battery_status()
        self.update_video_stream()
        self.initialize_timer()




    def update_video_stream(self):
        # Capture a frame from the NAO bot
        image = capture_frame(self.video_service, self.video_client)
        
        if image is None:
            print('Failed to capture frame')
            return

        # Send the image to the Flask server for YOLO inference
        yolo_results = send_image_to_server(image)

        # Annotate the frame with YOLO predictions
        if yolo_results:
            image = self.annotate_image(image, yolo_results)

        # Convert image to format suitable for Tkinter
        img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)

        # Display the annotated image in the GUI
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        # Repeat after 30ms
        self.root.after(30, self.update_video_stream)

    def annotate_image(self, image, yolo_results):
        """Annotate the image with YOLO bounding boxes and object names."""
        for result in yolo_results:
            confidence = result['confidence']
            class_id = result['class']
            bbox = result['bounding_box']
            top_left = (bbox[0], bbox[1])
            bottom_right = (bbox[2], bbox[3])

            # Get the class name from the class_id
            class_name = class_names[class_id] if class_id < len(class_names) else "Unknown"

            # Draw bounding box
            cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

            # Draw label and confidence
            label = "{0}: {1:.2f}".format(class_name, confidence)
            cv2.putText(image, label, (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return image

    def update_battery_status(self):
        battery_charge = self.battery_service.getBatteryCharge()
        self.battery_label.config(text="Battery Level: {}%".format(battery_charge))
        battery_width = 10 + (battery_charge * 1.8)
        self.canvas.coords(self.battery_bar, 10, 10, battery_width, 40)
        self.root.after(10000, self.update_battery_status)


    ### Complications with OOP and timers, calling the functions
    ### using the built in timer of tkinter works the best
    def initialize_timer(self):
        self.initialize_robot_movement()
        self.initialize_image_prediction()

    def initialize_robot_movement(self) :
        self.robot.update_robot_movement()
        self.root.after(50, self.initialize_robot_movement)

    def initialize_image_prediction(self):
        self.robot.update_image_prediction()
        self.root.after(1000, self.initialize_image_prediction)

    def speak_text(self):
        text = self.text_entry.get()
        if text.strip() == "":
            tkMessageBox.showwarning("Input Error", "Please enter text to speak.")
            return

        volume_control = "\\vol=100\\"
        text_with_volume = "{0}{1}".format(volume_control, text)

        # Use a separate thread to prevent blocking the GUI
        threading.Thread(target=self.robot.tts.say, args=(text_with_volume,)).start()

    def handle_escape_event(self, event):
        self.root.quit()
        self.robot.shutdown()



def load_class_names(filename):
    with open(filename, "r") as f:
        class_names = f.read().splitlines()
    return class_names

class_names = load_class_names('./../models/coco.names')
