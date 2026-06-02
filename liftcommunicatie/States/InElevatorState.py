from .IRobotLiftState import IRobotLiftState
from ..Communication.Requests.ChooseFloorRequest import ChooseFloorRequest


class InElevatorState(IRobotLiftState):
    def on_enter(self):
        request = ChooseFloorRequest(
            lift_id=self.context._lift_id,
            target_floor=self.context._target_floor
        )
        self.context.protocol.send_message(request.__dict__)
        self.context.get_logger().info(
            f"Inside elevator, selected floor {self.context._target_floor}"
        )

    def on_exit(self):
        self.context.get_logger().info("Elevator doors closing")
