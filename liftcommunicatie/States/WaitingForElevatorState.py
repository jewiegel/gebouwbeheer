from .IRobotLiftState import IRobotLiftState
from ..Communication.Requests.RequestLiftRequest import RequestLiftRequest


class WaitingForElevatorState(IRobotLiftState):
    def on_enter(self):
        request = RequestLiftRequest(lift_id=self.context._lift_id)
        self.context.protocol.send_message(request.__dict__)
        self.context.get_logger().info(f"Requested elevator {self.context._lift_id}")

    def on_exit(self):
        self.context.get_logger().info("Elevator arrived, proceeding")
