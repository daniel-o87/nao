# -*- coding: future_fstrings -*-
# robot_agent.py
# File responsible for either accepting inputs or acting as the medium of inputs, all sent to robot_environment
from robot_environment import NaoEnvironment

class NaoActions:
    def __init__(self, nao_env_obj):
        self.nao = nao_env_obj

    def speak(self, message):
        self.nao.tts_endpoint(message)

    def change_posture(self, new_pos, speed):
        self.nao.posture_endpoint(new_pos, speed)

        # put update_robot_movement from NAO/src/robot.py here
    def walk(self, x=0, y=0, theta=0):
        self.nao.motion_endpoint(x, y, theta)

    def movehead(self, head_yaw_speed=0, head_pitch_speed=0):
        self.nao.head_endpoint(head_yaw_speed, head_pitch_speed)


    def add_more_comman_actions_here(self):
        pass

    def update_robot_movement(self):
        x = 0.0  # Forward/backward speed
        y = 0.0  # Left/right speed
        theta = 0.0  # Rotation speed
        head_yaw_speed = 0.0
        head_pitch_speed = 0.0
        vertical_speed = 0.05  # Speed for vertical movement

        # Map keys to movements
        if 'w' in self.pressed_keys:
            x += 0.5  # Move forward
        if 's' in self.pressed_keys:
            x -= 0.5  # Move backward
        if 'a' in self.pressed_keys:
            y += 0.5  # Move left
        if 'd' in self.pressed_keys:
            y -= 0.5  # Move right
        if 'q' in self.pressed_keys:
            theta += 0.5  # Rotate left
        if 'e' in self.pressed_keys:
            theta -= 0.5  # Rotate right

        # Handle head movement
        if 'up' in self.pressed_keys:
            head_pitch_speed = 0.1  # Look up
        if 'down' in self.pressed_keys:
            head_pitch_speed = -0.1  # Look down
        if 'left' in self.pressed_keys:
            head_yaw_speed += 0.2  # Turn head left
        if 'right' in self.pressed_keys:
            head_yaw_speed -= 0.2  # Turn head right

        # Apply body movement
        if x != 0.0 or y != 0.0 or theta != 0.0:
            self.motion_service.moveToward(x, y, theta)
        else:
            self.motion_service.stopMove()

        # Apply head movement
        if head_yaw_speed != 0.0 or head_pitch_speed != 0.0:
            current_yaw, current_pitch = self.motion_service.getAngles(["HeadYaw", "HeadPitch"], True)
            new_yaw = current_yaw + head_yaw_speed
            new_pitch = current_pitch + head_pitch_speed
            new_yaw = max(min(new_yaw, 2.0857), -2.0857)
            new_pitch = max(min(new_pitch, 0.5149), -0.6720)
            self.motion_service.setAngles(["HeadYaw", "HeadPitch"], [new_yaw, new_pitch], 0.1)
