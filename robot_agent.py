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
    def walk(self, x, y, theta):
        self.nao.motion_endpoint(x, y, theta)

    def add_more_comman_actions_here(self):
        pass
