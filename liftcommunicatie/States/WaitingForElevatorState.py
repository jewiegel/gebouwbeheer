from .IRobotLiftState import IRobotLiftState
from .WaitingForDoorsState import WaitingForDoorsState
from ..Communication.Requests.RequestLiftRequest import RequestLiftRequest
from ..Communication.Responses.ElevatorArrivedResponse import ElevatorArrivedResponse


class WaitingForElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.prepare_for_response(ElevatorArrivedResponse)
        self.context.publish_feedback("Waiting for elevator")
        request = RequestLiftRequest(lift_id=self.context._lift_id)
        translated_request = self.context.transformer.from_request(request)
        self.context.protocol.send_message(translated_request)
        self.context.get_logger().info(f"Requested elevator {self.context._lift_id}")

    def execute(self):
        self.context.wait_for_response(ElevatorArrivedResponse)
        self.context.transition_to_state(WaitingForDoorsState(self.context))

    def on_exit(self):
        self.context.get_logger().info("Elevator arrived, proceeding")
