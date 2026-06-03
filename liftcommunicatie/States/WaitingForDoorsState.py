import time
from .IRobotLiftState import IRobotLiftState
from .InElevatorState import InElevatorState


class WaitingForDoorsState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Waiting for doors to open")
        self.context.get_logger().info("Waiting for elevator doors to open")

    def execute(self):
        # TODO: replace with threading.Event wait for door-open signal from lift API
        time.sleep(1.0)
        self.context.transition_to_state(InElevatorState(self.context))

    def on_exit(self):
        self.context.get_logger().info("Doors are open, entering elevator")
