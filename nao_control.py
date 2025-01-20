#!/usr/bin/env python2

from __future__ import print_function
import socket
import json
from naoqi import ALProxy
import argparse

class NaoHeadController(object):
    def __init__(self, nao_ip, nao_port=9559, server_ip='127.0.0.1', server_port=12345):
        # Connect to NAO
        try:
            self.motion_proxy = ALProxy("ALMotion", nao_ip, nao_port)
            print("Connected to NAO")
        except Exception as e:
            print("Failed to connect to NAO: {}".format(e))
            raise
            
        # Initialize NAO head
        self.motion_proxy.wakeUp()
        
        # Connect to pose detection server
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((server_ip, server_port))
            print("Connected to pose detection server")
        except Exception as e:
            print("Failed to connect to server: {}".format(e))
            raise
    
    def move_head(self, angles):
        """Move NAO's head based on detected angles"""
        try:
            # Apply limits to angles
            yaw = max(-2.0, min(2.0, angles['yaw']))
            pitch = max(-0.6, min(0.5, angles['pitch']))
            
            # Set head angles
            self.motion_proxy.setAngles(["HeadYaw", "HeadPitch"], [yaw, pitch], 0.1)
            
        except Exception as e:
            print("Error moving head: {}".format(e))
    
    def run(self):
        print("Starting NAO head controller. Press Ctrl+C to exit.")
        buffer = ""
        
        try:
            while True:
                data = self.client.recv(1024).decode()
                if not data:
                    print("Server disconnected")
                    break
                
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    try:
                        angles = json.loads(line)
                        self.move_head(angles)
                    except ValueError as e:
                        continue
                        
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.client.close()
            self.motion_proxy.rest()

def main():
    parser = argparse.ArgumentParser(description='NAO Head Controller')
    parser.add_argument('--nao-ip', required=True, help='NAO robot IP address')
    args = parser.parse_args()
    
    controller = NaoHeadController(args.nao_ip)
    controller.run()

if __name__ == "__main__":
    main()
