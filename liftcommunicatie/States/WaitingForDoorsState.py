from .IRobotLiftState import IRobotLiftState


class WaitingForDoorsState(IRobotLiftState):
    def on_enter(self):
        self.context.get_logger().info("Waiting for elevator doors to open")

    def on_exit(self):
        self.context.get_logger().info("Doors are open, entering elevator")
