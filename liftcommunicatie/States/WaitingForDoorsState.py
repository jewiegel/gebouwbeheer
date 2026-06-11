import threading
from .IRobotLiftState import IRobotLiftState

DOOR_OPEN_DELAY = 1.0


class WaitingForDoorsState(IRobotLiftState):
    def __init__(self, context, next_state):
        super().__init__(context)
        self._next_state = next_state

    def on_enter(self):
        self.context.publish_feedback("Waiting for doors to open", new_floor=self.context._target_floor)
        self.context.get_logger().info("Waiting for elevator doors to open")

    def execute(self):
        # TODO: wait for a DoorsStatusResponse from the lift API instead of a fixed delay.
        # The never-set event makes this a cancellable sleep.
        self.context.wait_for_event(threading.Event(), timeout=DOOR_OPEN_DELAY)
        return self._next_state

    def on_exit(self):
        self.context.get_logger().info("Doors are open, proceeding")
