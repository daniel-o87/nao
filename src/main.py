# main.py

import sys
import subprocess
import Tkinter as tk
from robot import NaoRobot
from gui import NaoControlGUI
import config
import atexit

# Global variable to store the server process
tflite_server_process = None

def start_tflite_server():
    """ Start tflite_server.py using Python 3 and return the process. """
    global tflite_server_process
    try:
        tflite_server_process = subprocess.Popen(['python3', 'tflite_server.py'])
        print("STATUS IS", tflite_server_process)
    except Exception as e:
        print("Failed to start tflite_server.py", e)
        sys.exit(1)

def stop_tflite_server():
    """ Ensure the tflite_server.py process is terminated. """
    global tflite_server_process
    if tflite_server_process:
        # Check if the process is still running
        ret_code = tflite_server_process.poll()  # This returns None if the process is still running
        if ret_code is None:
            try:
                print("Shutting down tflite_server.py...")
                tflite_server_process.terminate()  
                tflite_server_process.wait()       # Wait for the process to terminate
            except OSError as e:
                print("Failed to terminate tflite_server process: {0}".format(e))
        else:
            print("tflite_server.py was already stopped.")



def main():
#    start_tflite_server()

#    try:
    # Start robot
    robot = NaoRobot(config.ROBOT_IP, config.ROBOT_PORT)

    # Initialize GUI
    root = tk.Tk()
    app = NaoControlGUI(root, robot)
    root.mainloop()
#        print("Main loop over")
#    except Exception as e:
#        print("An error occurred:", e)
#    finally:
#        stop_tflite_server()
#        print("Exiting the program.")

if __name__ == "__main__":
    main()
