# main.py

import sys
import subprocess
import Tkinter as tk
from robot import NaoRobot
from gui import NaoControlGUI
import config
import atexit

if __name__ == "__main__":
    mode = sys.argv[1].strip()

    # Start robots config
    robot = NaoRobot(config.ROBOT_IP, config.ROBOT_PORT, mode)

    # Initialize GUI
    root = tk.Tk()
    app = NaoControlGUI(root, robot, mode)

    root.mainloop()
