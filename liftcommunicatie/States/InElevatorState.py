import time
from .IRobotLiftState import IRobotLiftState
from .DrivingInElevatorState import DrivingInElevatorState
from ..Communication.Requests.ChooseFloorRequest import ChooseFloorRequest
from ..Communication.Responses.FloorStatusResponse import FloorStatusResponse


class InElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Inside elevator, selecting floor", new_floor=self.context._target_floor)
        request = ChooseFloorRequest(self.context._target_floor)
        
        translated_request = self.context.transformer.from_request(request)
        self.context.protocol.send_message(translated_request)
        self.context.get_logger().info(
            f"Inside elevator, selected floor {self.context._target_floor}"
        )

    def execute(self):
        self.context.wait_for_response(FloorStatusResponse, callback=self._on_elevator_arrived)

    def _on_elevator_arrived(self, response: FloorStatusResponse):
        if response.floor != self.context._target_floor:
            self.context.get_logger().warning(
                f"Wrong elevator floor: got {response.floor}, expected: {self.context._target_floor}"
            )
            self.context.wait_for_response(FloorStatusResponse, callback=self._on_elevator_arrived)
        else:
            from .WaitingForDoorsState import WaitingForDoorsState
            from .ExitingElevatorState import ExitingElevatorState
            self.context.transition_to_state(WaitingForDoorsState(self.context, ExitingElevatorState(self.context)))
        

    def on_exit(self):
        self.context.get_logger().info("Elevator doors closing")
