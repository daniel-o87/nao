import Tkinter as tk
import tkMessageBox as messagebox
import threading
import Queue as queue
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
        
        # Initialize services
        self.motion_service = self.robot.motion_service
        self.posture_service = self.robot.posture_service
        self.video_service = self.robot.video_service
        self.video_client = self.robot.video_client
        self.battery_service = self.robot.battery_service
        self.tts = self.robot.tts
        self.tts.setParameter("defaultVoiceSpeed", 100)
        self.last_state_covered = False

        # Add queues for thread communication
        self.frame_queue = queue.Queue(maxsize=2)
        self.prediction_queue = queue.Queue(maxsize=2)

        # Add flags for thread control
        self.is_running = True
        self.movement_lock = threading.Lock()

        # Initialize robot position
        self.motion_service.wakeUp()
        self.posture_service.goToPosture('StandInit', 0.50)

        # Setup GUI
        self.setup_gui()
        
        # Welcome message
        self.tts.say("Hello RAIR LAB! I've gained consciousness.")

        # Start all update processes
        self.start_worker_threads()
        self.update_battery_status()
        self.root.after(50, self.update_video_stream)

    def setup_gui(self):
        self.root.title("NAO Robot Control")
        self.root.geometry("600x600")

        # Instructions
        instructions = tk.Label(
            self.root,
            text="Use WASD to move, Q/E to rotate.\nUse arrow keys to move the head.\nPress 'c' to save as covered, 'u' to save as uncovered.\nPress Esc to exit.",
            font=("Helvetica", 12),
        )
        instructions.grid(row=0, column=0, columnspan=4, pady=20, sticky="nsew")

        # Posture buttons
        sit_button = tk.Button(self.root, text="Sit", command=self.robot.make_robot_sit, font=("Helvetica", 12))
        sit_button.grid(row=1, column=0, padx=10, pady=10)

        stand_button = tk.Button(self.root, text="Stand", command=self.robot.make_robot_stand, font=("Helvetica", 12))
        stand_button.grid(row=1, column=1, padx=10, pady=10)

        superman_button = tk.Button(self.root, text="Superman", command=self.robot.superman, font=("Helvetica", 12))
        superman_button.grid(row=1, column=2, padx=10, pady=10)

        crouch_button = tk.Button(self.root, text="Crouch", command=self.robot.make_robot_crouch, font=("Helvetica", 12))
        crouch_button.grid(row=1, column=3, padx=10, pady=10)

        # Text input for TTS
        self.text_entry = tk.Entry(self.root, width=50, font=("Helvetica", 12))
        self.text_entry.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        self.robot.assign_value(self.text_entry)

        speak_button = tk.Button(self.root, text="Speak", command=self.speak_text, font=("Helvetica", 12))
        speak_button.grid(row=2, column=3, padx=10, pady=10)

        # Video feed
        self.video_label = tk.Label(self.root)
        self.video_label.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Battery status
        self.battery_label = tk.Label(self.root, text="Battery Level: 0%", font=("Helvetica", 12))
        self.battery_label.grid(row=4, column=0, columnspan=4, padx=10, pady=10)

        self.canvas = tk.Canvas(self.root, width=200, height=50, bg="white")
        self.canvas.grid(row=5, column=0, columnspan=4, padx=10, pady=10)
        self.battery_bar = self.canvas.create_rectangle(10, 10, 10, 40, fill="green")

        # Bind events
        self.root.bind('<Button-1>', self.unfocus_text_entry)
        self.text_entry.bind('<Button-1>', lambda e: e.widget.focus_set() or 'break')
        self.video_label.bind('<Button-1>', self.unfocus_text_entry)
        self.root.bind('<KeyPress>', self.robot.on_key_press)
        self.root.bind('<KeyRelease>', self.robot.on_key_release)
        self.root.bind('<Escape>', self.handle_escape_event)
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)

    def start_worker_threads(self):
        """Initialize and start worker threads"""
        threads = [
            (self.video_capture_loop, "Video Capture"),
            (self.prediction_processing_loop, "Prediction Processing"),
            (self.movement_update_loop, "Movement Update")
        ]

        for thread_func, name in threads:
            thread = threading.Thread(target=thread_func, name=name)
            thread.daemon = True
            thread.start()

    def video_capture_loop(self):
        """Continuous loop for capturing video frames"""
        last_capture_time = 0
        frame_interval = 1.0 / 30  # Target 30 FPS

        while self.is_running:
            current_time = time.time()
            if current_time - last_capture_time >= frame_interval:
                try:
                    image = capture_frame(self.video_service, self.video_client)
                    if image is not None and not self.frame_queue.full():
                        self.frame_queue.put(image, block=False)
                    last_capture_time = current_time
                except queue.Full:
                    pass  # Skip frame if queue is full
                except Exception as e:
                    print("Error capturing frame: {}".format(e))
            time.sleep(0.001)  # Prevent CPU hogging

    def prediction_processing_loop(self):
        """Continuous loop for processing predictions"""
        while self.is_running:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(block=False)
                    prediction = send_image_to_server(frame, self.mode)
                    if prediction and not self.prediction_queue.full():
                        self.prediction_queue.put((frame, prediction), block=False)
            except queue.Empty:
                time.sleep(0.001)
            except Exception as e:
                print("Error processing prediction: {}".format(e))

    def movement_update_loop(self):
        """Continuous loop for updating robot movement"""
        last_update_time = 0
        movement_interval = 1.0 / 60  # 60Hz updates

        while self.is_running:
            current_time = time.time()
            if current_time - last_update_time >= movement_interval:
                with self.movement_lock:
                    try:
                        self.robot.update_robot_movement()
                        last_update_time = current_time
                    except Exception as e:
                        print("Error updating movement: {}".format(e))
            time.sleep(0.001)

    def update_video_stream(self):
        """Update video display from prediction queue"""
        try:
            if not self.prediction_queue.empty():
                frame, prediction = self.prediction_queue.get(block=False)
                
                if self.mode == 'yolo':
                    frame = self.annotate_image(frame, prediction)
                elif self.mode == 'tflite':
                    self.process_tflite_prediction(prediction)

                # Convert and display image
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                
        except queue.Empty:
            pass
        except Exception as e:
            print("Error updating video display: {}".format(e))
        
        # Adaptive timing for next update
        delay = 20 if self.prediction_queue.qsize() > 1 else 10
        self.root.after(delay, self.update_video_stream)

    def annotate_image(self, image, yolo_results):
        """Annotate image with YOLO predictions"""
        try:
            if isinstance(yolo_results, dict) and 'yolo_prediction' in yolo_results:
                predictions = yolo_results['yolo_prediction']
                
                for result in predictions:
                    confidence = float(result['confidence'])
                    class_id = int(result['class'])
                    bbox = result['bounding_box']
                    
                    if not bbox or len(bbox) != 4:
                        continue
                    
                    top_left = (int(bbox[0]), int(bbox[1]))
                    bottom_right = (int(bbox[2]), int(bbox[3]))
                    class_name = class_names[class_id] if class_id < len(class_names) else "Unknown"
                    
                    cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
                    label = "{}: {:.2f}".format(class_name, confidence)
                    cv2.putText(image, label, (top_left[0], top_left[1] - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
        except Exception as e:
            print("Error annotating image: {}".format(e))
            
        return image

    def process_tflite_prediction(self, prediction):
        """Process TFLite predictions"""
        try:
            ans = prediction['tflite_prediction'][0][0]
            if ans < 0.5:
                self.last_state_covered = True
            elif self.last_state_covered and ans >= 0.5:
                threading.Thread(target=self.tts.say, args=("Peekaboo!",)).start()
                self.last_state_covered = False
        except Exception as e:
            print("Error processing TFLite prediction: {}".format(e))

    def update_battery_status(self):
        """Update battery display"""
        try:
            battery_charge = self.battery_service.getBatteryCharge()
            self.battery_label.config(text="Battery Level: {}%".format(battery_charge))
            battery_width = 10 + (battery_charge * 1.8)
            self.canvas.coords(self.battery_bar, 10, 10, battery_width, 40)
        except Exception as e:
            print("Error updating battery: {}".format(e))
        self.root.after(30000, self.update_battery_status)

    def speak_text(self):
        """Handle text-to-speech"""
        text = self.text_entry.get()
        if text.strip() == "":
            messagebox.showwarning("Input Error", "Please enter text to speak.")
            return
        
        volume_control = "\\vol=100\\"
        text_with_volume = "{}{}".format(volume_control, text)
        threading.Thread(target=self.tts.say, args=(text_with_volume,)).start()

    def handle_escape_event(self, event):
        """Handle escape key press"""
        self.root.quit()
        self.robot.shutdown()

    def cleanup(self):
        """Clean shutdown of GUI and resources"""
        self.is_running = False
        time.sleep(0.1)
        
        try:
            # Clear queues
            while not self.frame_queue.empty():
                self.frame_queue.get_nowait()
            while not self.prediction_queue.empty():
                self.prediction_queue.get_nowait()
                
            # Cancel scheduled tasks
            for after_id in self.root.tk.call('after', 'info'):
                self.root.after_cancel(after_id)
                
            # Shutdown robot and GUI
            self.robot.shutdown()
            self.root.quit()
        except Exception as e:
            print("Error during cleanup: {}".format(e))

    def unfocus_text_entry(self, event=None):
        """Handle unfocusing text entry"""
        if event and event.widget != self.text_entry:
            self.root.focus_set()
            return 'break'
