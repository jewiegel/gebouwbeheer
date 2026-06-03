import time
from .IRobotLiftState import IRobotLiftState
from .ExitingElevatorState import ExitingElevatorState


class DrivingInElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Driving to target floor")
        self.context.get_logger().info(
            f"Elevator driving to floor {self.context._target_floor}"
        )

    def execute(self):
        # TODO: replace with threading.Event wait for floor-arrived signal from lift API
        time.sleep(3.0)
        self.context.transition_to_state(ExitingElevatorState(self.context))

    def on_exit(self):
        self.context.get_logger().info(
            f"Arrived at floor {self.context._target_floor}"
        )
