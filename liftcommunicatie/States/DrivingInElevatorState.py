from .IRobotLiftState import IRobotLiftState


class DrivingInElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.get_logger().info(
            f"Elevator driving to floor {self.context._target_floor}"
        )

    def on_exit(self):
        self.context.get_logger().info(
            f"Arrived at floor {self.context._target_floor}"
        )
