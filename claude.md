Traceback (most recent call last):
  File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1550, in __call__
    return self.func(*args)
  File "/home/daniel/rair/nao/robot_gui.py", line 390, in <lambda>
    self.root.bind("<KeyPress-Left>", lambda e: self.head_key_press('Left'))
  File "/home/daniel/rair/nao/robot_gui.py", line 714, in head_key_press
    self.update_status_display()
  File "/home/daniel/rair/nao/robot_gui.py", line 788, in update_status_display
    self.status_var.set(status)
AttributeError: NaoControlGUI instance has no attribute 'status_var'
Exception in Tkinter callback
Traceback (most recent call last):
  File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1550, in __call__
    return self.func(*args)
  File "/home/daniel/rair/nao/robot_gui.py", line 394, in <lambda>
    self.root.bind("<KeyRelease-Left>", lambda e: self.head_key_release('Left'))
  File "/home/daniel/rair/nao/robot_gui.py", line 722, in head_key_release
    self.update_status_display()
  File "/home/daniel/rair/nao/robot_gui.py", line 788, in update_status_display
    self.status_var.set(status)
AttributeError: NaoControlGUI instance has no attribute 'status_var'
Exception in Tkinter callback
Traceback (most recent call last):
  File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1550, in __call__
    return self.func(*args)
  File "/home/daniel/rair/nao/robot_gui.py", line 542, in emergency_stop
    self.stop_movement()
  File "/home/daniel/rair/nao/robot_gui.py", line 749, in stop_movement
    self.update_status_display()
  File "/home/daniel/rair/nao/robot_gui.py", line 788, in update_status_display
    self.status_var.set(status)
AttributeError: NaoControlGUI instance has no attribute 'status_var'
Exception in Tkinter callback
Traceback (most recent call last):
  File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1550, in __call__
    return self.func(*args)
  File "/home/daniel/rair/nao/robot_gui.py", line 542, in emergency_stop
    self.stop_movement()
  File "/home/daniel/rair/nao/robot_gui.py", line 749, in stop_movement
    self.update_status_display()
  File "/home/daniel/rair/nao/robot_gui.py", line 788, in update_status_display
    self.status_var.set(status)
AttributeError: NaoControlGUI instance has no attribute 'status_var'
