from .IRobotLiftState import IRobotLiftState
from .WaitingForDoorsState import WaitingForDoorsState
from .InElevatorState import InElevatorState
from ..Communication.Requests.RequestLiftRequest import RequestLiftRequest
from ..Communication.Responses.ElevatorArrivedResponse import ElevatorArrivedResponse


class WaitingForElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Waiting for elevator")
        request = RequestLiftRequest(self.context._current_floor)
        translated_request = self.context.transformer.from_request(request)
        self.context.protocol.send_message(translated_request)
        self.context.get_logger().info(f"Requested elevator going to floor: {self.context._current_floor}")

    def execute(self):
        self.context.wait_for_response(ElevatorArrivedResponse, callback=self._on_elevator_arrived)

    def _on_elevator_arrived(self, response: ElevatorArrivedResponse):
        if response.floor != self.context._current_floor:
            self.context.get_logger().warning(
                f"Wrong elevator floor: got {response.floor}, expected {self.context._current_floor}"
            )
            return
        self.context.transition_to_state(WaitingForDoorsState(self.context, InElevatorState(self.context)))

    def on_exit(self):
        self.context.get_logger().info("Elevator arrived, proceeding")
