# -*- coding: future_fstrings -*-
# robot_environment.py 
# File responsible for taking in various inputs and sending them to the NAO bot
import qi
import time

class ConnectionError(Exception):
    pass

class NaoEnvironment:
    def __init__(self, ip, port):
        self.ip = str(ip)
        self.port = str(port)
        self.session = None
        self.services = {}
        
    def init_robot(self):
        for attempt in range(3):
            try:
                self.session = qi.Session()
                url = f"tcp://{self.ip}:{self.port}"
                print(f"Attempting to connect to: {url}")

                self.session.connect(url)
                print("Successfully connected to the robot!")

                self._init_services()

                return True

            except RuntimeError as e:
                print(f"ERROR: Connection attempt #{attempt+1} failed: {e}")
                if attempt < 2:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("Max connection attempts reached. Unable to connect.")
                    self.session = None
                    return False
    
    def _init_services(self):
        ### Initialize commonly used services after connection
        self.services["tts"] = self.session.service("ALTextToSpeech")
        self.services["motion"] = self.session.service("ALMotion")
        self.services["posture"] = self.session.service("ALRobotPosture")
    
    def get_service(self, service_name):
        ### Get a service, creating it if not already cached
        if service_name not in self.services:
            self.services[service_name] = self.session.service(service_name)
        return self.services[service_name]
    
    def tts_endpoint(self, message):
        ### Send text to speech
        if self.session is None:
            raise ConnectionError("Not connected to robot")
        
        tts = self.services.get("tts")
        #if tts is None:
        #    tts = self.get_service("ALTextToSpeech")
        
        tts.say(message)


    def motion_endpoint(self, x, y, theta):
        if self.session is None:
            raise ConnectionError("Not connected to robot")

        motion = self.services.get("motion")
        motion.moveToward(x, y, theta)

    def posture_endpoint(self, name, speed):
        ### http://doc.aldebaran.com/2-1/naoqi/motion/alrobotposture-api.html#ALRobotPostureProxy::getPostureList
        ### Change Posture of NAO
        ### Methods are the following
        #ALRobotPostureProxy::getPostureList()
        #ALRobotPostureProxy::getPosture()
        #ALRobotPostureProxy::goToPosture()
        #ALRobotPostureProxy::applyPosture()
        #ALRobotPostureProxy::stopMove()
        #ALRobotPostureProxy::getPostureFamily()
        #ALRobotPostureProxy::getPostureFamilyList()
        #ALRobotPostureProxy::setMaxTryNumber()

        if self.session is None:
            raise ConnectionError("Not connected to robot")
        
        posture = self.services.get("posture")
        print(posture)
        posture.goToPosture(name, speed)







