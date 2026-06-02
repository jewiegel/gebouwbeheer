from .IRobotLiftState import IRobotLiftState


class ExitingElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.get_logger().info("Exiting elevator")

    def on_exit(self):
        self.context.get_logger().info("Successfully exited elevator")
