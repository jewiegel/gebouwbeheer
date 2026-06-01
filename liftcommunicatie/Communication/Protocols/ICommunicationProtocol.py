from abc import ABC, abstractmethod

class ICommunicationProtocol(ABC):

    @abstractmethod
    def connect(self, address: str):
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