from .IRobotLiftState import IRobotLiftState
from .InElevatorState import InElevatorState


class DrivingInElevatorState(IRobotLiftState):
    def on_enter(self):
        self._distance = self.context.get_drive_distance(self.context._current_floor)
        self.context.publish_feedback("Driving into elevator")
        self.context.get_logger().info(
            f"Driving {self._distance} meter {self.context.drive_direction_label} into elevator"
        )

    def execute(self):
        self.context.drive(self._distance)
        return InElevatorState(self.context)

    def on_exit(self):
        self.context.get_logger().info("Finished driving into elevator")
