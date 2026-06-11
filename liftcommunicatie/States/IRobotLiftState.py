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
        """Do the state's work; blocking is allowed (runs on the action executor thread).

        Returns the next state, or None when the state machine is finished.
        Raise GoalCancelledError (via the context wait helpers) to handle cancellation.
        """
        return None
