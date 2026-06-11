import time
from .IRobotLiftState import IRobotLiftState
from .WaitingForDoorsState import WaitingForDoorsState
from .DrivingInElevatorState import DrivingInElevatorState
from ..Communication.Requests.RequestLiftRequest import RequestLiftRequest
from ..Communication.Responses.ElevatorArrivedResponse import ElevatorArrivedResponse

ELEVATOR_ARRIVAL_TIMEOUT = 300.0


class WaitingForElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Waiting for elevator")
        self.context.get_logger().info(f"Requesting elevator to floor: {self.context._current_floor}")

    def execute(self):
        # Create the inbox before sending, so a fast response can't slip past us
        self.context.prepare_for_response(ElevatorArrivedResponse)
        request = RequestLiftRequest(self.context._current_floor)
        self.context.protocol.send_message(self.context.transformer.from_request(request))

        deadline = time.monotonic() + ELEVATOR_ARRIVAL_TIMEOUT
        while True:
            response = self.context.wait_for_response(
                ElevatorArrivedResponse, timeout=deadline - time.monotonic()
            )
            if response is None:
                raise RuntimeError("Timed out waiting for the elevator to arrive")
            if response.floor == self.context._current_floor:
                return WaitingForDoorsState(self.context, DrivingInElevatorState(self.context))
            self.context.get_logger().warning(
                f"Wrong elevator floor: got {response.floor}, expected {self.context._current_floor}"
            )

    def on_exit(self):
        self.context.get_logger().info("Elevator arrived, proceeding")
