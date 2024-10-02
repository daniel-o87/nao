import qi

def connect_to_robot(self, ip, port, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            session = qi.Session()
            session.connect("tcp://{0}:{1}".format(ip, port))
            return session
        except RuntimeError as e:
            print("Connection attempt {0} failed: {1}".format(attempt+1, e))
            time.sleep(5)
        raise ConnectionError("COULDNT CONNECT LOSER! TRY AGAIN")

session = connect_to_robot(ip, port)


tts = session.service("ALTextToSpeech")

tts.say("im such a tweaker")
