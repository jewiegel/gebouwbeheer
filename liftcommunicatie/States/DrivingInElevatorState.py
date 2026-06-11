import threading
from nav2_msgs.action import DriveOnHeading
from action_msgs.msg import GoalStatus
from .IRobotLiftState import IRobotLiftState
from .ExitingElevatorState import ExitingElevatorState


class DrivingInElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Driving into elevator")
        self.context.get_logger().info("Driving 1 meter forward into elevator")
        self._nav_done = threading.Event()
        self._nav_succeeded = False

    def execute(self):
        goal = DriveOnHeading.Goal()
        goal.target.x = 1.0
        goal.speed = 0.2
        goal.time_allowance.sec = 30

        self.context._drive_on_heading_client.wait_for_server()
        future = self.context._drive_on_heading_client.send_goal_async(goal)
        future.add_done_callback(self._goal_response_callback)
        self._nav_done.wait()

        if not self._nav_succeeded:
            raise RuntimeError("DriveOnHeading failed: could not drive 1 meter forward")
        self.context.transition_to_state(ExitingElevatorState(self.context))

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.context.get_logger().error("DriveOnHeading goal rejected")
            self._nav_done.set()
            return
        goal_handle.get_result_async().add_done_callback(self._result_callback)

    def _result_callback(self, future):
        status = future.result().status
        self._nav_succeeded = (status == GoalStatus.STATUS_SUCCEEDED)
        if not self._nav_succeeded:
            self.context.get_logger().error(f"DriveOnHeading failed with status {status}")
        self._nav_done.set()

    def on_exit(self):
        self.context.get_logger().info("Finished driving 1 meter forward into elevator")
