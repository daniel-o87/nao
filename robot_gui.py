# -*- coding: future_fstrings -*-
import Tkinter as tk

class NaoControlGUI:
    def __init__(self, agent):
        self.agent = agent
        self.root = tk.Tk()
        self.root.title("NAO Robot Control")
        self.setup_ui()
        
    def setup_ui(self):
        # Create a frame for movement controls
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.grid(row=0, column=0)
        
        # Movement buttons
        ttk.Button(control_frame, text="Forward", 
                  command=lambda: self.agent.walk(0.5, 0, 0).grid(row=0, column=1)
        ttk.Button(control_frame, text="Left", 
                  command=lambda: self.agent.walk(-0.5, 0, 0).grid(row=1, column=0)
        ttk.Button(control_frame, text="Right", 
                  command=lambda: self.agent.walk(0, 0.5, 0).grid(row=1, column=2)
        ttk.Button(control_frame, text="Backward", 
                  command=lambda: self.agent.walk(0, -0.5, 0).grid(row=2, column=1)
        
        # Status display
        self.status_var = tk.StringVar(value="Status: Ready")
        ttk.Label(self.root, textvariable=self.status_var).grid(row=1, column=0)
        
        # Keyboard bindings
        self.root.bind("<Up>", lambda e: self.agent.process_command("forward"))
        self.root.bind("<Down>", lambda e: self.agent.process_command("backward"))
        self.root.bind("<Left>", lambda e: self.agent.process_command("left"))
        self.root.bind("<Right>", lambda e: self.agent.process_command("right"))
        self.root.bind("<space>", lambda e: self.agent.process_command("stop"))
        
    def update_status(self):
        """Update status display with current robot state"""
        state = self.agent.get_robot_state()
        self.status_var.set(f"Position: {state['position']} | Battery: {state['battery']}%")
        self.root.after(1000, self.update_status)  # 
        
    def run(self):
        """Start the GUI event loop"""
        self.update_status()
        self.root.mainloop()
