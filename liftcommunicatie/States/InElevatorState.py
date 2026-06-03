import time
from .IRobotLiftState import IRobotLiftState
from .DrivingInElevatorState import DrivingInElevatorState
from ..Communication.Requests.ChooseFloorRequest import ChooseFloorRequest


class InElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Inside elevator, selecting floor")
        request = ChooseFloorRequest(
            lift_id=self.context._lift_id,
            target_floor=self.context._target_floor
        )
        self.context.protocol.send_message(request.__dict__)
        self.context.get_logger().info(
            f"Inside elevator, selected floor {self.context._target_floor}"
        )

    def execute(self):
        # TODO: replace with threading.Event wait for floor-selected confirmation from lift API
        time.sleep(1.0)
        self.context.transition_to_state(DrivingInElevatorState(self.context))

    def on_exit(self):
        self.context.get_logger().info("Elevator doors closing")
