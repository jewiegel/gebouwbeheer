from abc import ABC, abstractmethod

class ICommunicationProtocol(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def wait_until_connected(self, timeout=None):
        pass

    @abstractmethod
    def is_connected(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def send_message(self, message):
        pass

    @abstractmethod
    def set_message_callback(self, callback):
        pass