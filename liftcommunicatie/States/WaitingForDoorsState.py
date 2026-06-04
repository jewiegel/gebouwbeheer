import time
from .IRobotLiftState import IRobotLiftState


class WaitingForDoorsState(IRobotLiftState):
    def __init__(self, context, next_state):
        super().__init__(context)
        self._next_state = next_state

    def on_enter(self):
        self.context.publish_feedback("Waiting for doors to open", new_floor=self.context._target_floor)
        self.context.get_logger().info("Waiting for elevator doors to open")

    def execute(self):
        # TODO: replace with threading.Event wait for door-open signal from lift API
        time.sleep(1.0)
        self.context.transition_to_state(self._next_state)

    def on_exit(self):
        self.context.get_logger().info("Doors are open, entering elevator")
