import time
from .IRobotLiftState import IRobotLiftState
from .WaitingForDoorsState import WaitingForDoorsState
from .ExitingElevatorState import ExitingElevatorState
from ..Communication.Requests.ChooseFloorRequest import ChooseFloorRequest
from ..Communication.Responses.FloorStatusResponse import FloorStatusResponse

FLOOR_REACHED_TIMEOUT = 300.0


class InElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Inside elevator, selecting floor", new_floor=self.context._target_floor)
        self.context.get_logger().info(f"Inside elevator, selecting floor {self.context._target_floor}")

    def execute(self):
        # Create the inbox before sending, so a fast response can't slip past us
        self.context.prepare_for_response(FloorStatusResponse)
        request = ChooseFloorRequest(self.context._target_floor)
        self.context.protocol.send_message(self.context.transformer.from_request(request))

        deadline = time.monotonic() + FLOOR_REACHED_TIMEOUT
        while True:
            response = self.context.wait_for_response(
                FloorStatusResponse, timeout=deadline - time.monotonic()
            )
            if response is None:
                raise RuntimeError(
                    f"Timed out waiting for the elevator to reach floor {self.context._target_floor}"
                )
            if response.floor == self.context._target_floor:
                return WaitingForDoorsState(self.context, ExitingElevatorState(self.context))
            self.context.get_logger().warning(
                f"Wrong elevator floor: got {response.floor}, expected: {self.context._target_floor}"
            )

    def on_exit(self):
        self.context.get_logger().info("Reached target floor, elevator doors opening")
