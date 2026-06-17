from .IRobotLiftState import IRobotLiftState
from ..Communication.Requests.RobotReadyRequest import RobotReadyRequest


class ExitingElevatorState(IRobotLiftState):
    def on_enter(self):
        self._distance = self.context.get_drive_distance(self.context._target_floor)
        self.context.publish_feedback("Exiting elevator")
        self.context.get_logger().info(
            f"Driving {self._distance} meter {self.context.drive_direction_label} out of elevator"
        )

    def execute(self):
        self.context.drive(self._distance)

        # Robot is clear of the lift: signal ready so the lift may move on
        self.context.protocol.send_message(self.context.transformer.from_request(RobotReadyRequest()))
        self.context.get_logger().info("Sent robot ready; lift is free to move")
        return None

    def on_exit(self):
        self.context.get_logger().info("Successfully exited elevator")
