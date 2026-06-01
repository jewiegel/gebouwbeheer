from abc import ABC, abstractmethod

class ICommunicationProtocol(ABC):

    @abstractmethod
    def connect(address: str):
        pass

    @abstractmethod
    def disconnect():
        pass

    @abstractmethod
    def setup():
        pass

    @abstractmethod
    def send_message(message):
        pass