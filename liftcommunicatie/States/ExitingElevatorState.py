import time
from .IRobotLiftState import IRobotLiftState


class ExitingElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Exiting elevator")
        self.context.get_logger().info("Exiting elevator")

    def execute(self):
        # TODO: replace with threading.Event wait for exit-confirmed signal from lift API
        time.sleep(1.0)
        self.context.transition_to_state(None)
        self.context._machine_done.set()

    def on_exit(self):
        self.context.get_logger().info("Successfully exited elevator")
