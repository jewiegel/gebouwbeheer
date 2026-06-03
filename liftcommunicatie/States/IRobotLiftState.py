from abc import ABC, abstractmethod


class IRobotLiftState(ABC):
    def __init__(self, context):
        self.context = context

    @abstractmethod
    def on_enter(self):
        pass

    @abstractmethod
    def on_exit(self):
        pass

    def execute(self):
        pass