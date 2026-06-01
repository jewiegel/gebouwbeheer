from .ICommunicationProtocol import ICommunicationProtocol


class TestLiftProtocol(ICommunicationProtocol):
    def __init__(self):
        self.a = 1

    
    def connect(self, address: str):
        print("bruh")

    def setup(self):
        print("Zowkski")

    def disconnect(self):
        pass

    def send_message(self, message):
        pass
    
