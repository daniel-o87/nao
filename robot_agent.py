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

    def add_more_comman_actions_here(self):
        pass
