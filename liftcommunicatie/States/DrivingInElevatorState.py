import threading
from nav2_msgs.action import DriveOnHeading
from action_msgs.msg import GoalStatus
from .IRobotLiftState import IRobotLiftState
from .InElevatorState import InElevatorState
from ..Exceptions import GoalCancelledError

NAV_TIMEOUT = 60.0


class DrivingInElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context.publish_feedback("Driving into elevator")
        self.context.get_logger().info("Driving 1 meter forward into elevator")
        self._nav_done = threading.Event()
        self._nav_succeeded = False
        self._nav_goal_handle = None

    def execute(self):
        goal = DriveOnHeading.Goal()
        goal.target.x = 0.7
        goal.speed = 0.2
        goal.time_allowance.sec = 30

        if not self.context._drive_on_heading_client.wait_for_server(timeout_sec=5.0):
            raise RuntimeError("drive_on_heading action server not available")
        future = self.context._drive_on_heading_client.send_goal_async(goal)
        future.add_done_callback(self._goal_response_callback)

        try:
            finished = self.context.wait_for_event(self._nav_done, timeout=NAV_TIMEOUT)
        except GoalCancelledError:
            if self._nav_goal_handle is not None:
                self._nav_goal_handle.cancel_goal_async()
            raise
        if not finished:
            raise RuntimeError("DriveOnHeading timed out")
        if not self._nav_succeeded:
            raise RuntimeError("DriveOnHeading failed: could not drive 1 meter forward")
        return InElevatorState(self.context)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.context.get_logger().error("DriveOnHeading goal rejected")
            self._nav_done.set()
            return
        self._nav_goal_handle = goal_handle
        goal_handle.get_result_async().add_done_callback(self._result_callback)

    def _result_callback(self, future):
        status = future.result().status
        self._nav_succeeded = (status == GoalStatus.STATUS_SUCCEEDED)
        if not self._nav_succeeded:
            self.context.get_logger().error(f"DriveOnHeading failed with status {status}")
        self._nav_done.set()

    def on_exit(self):
        self.context.get_logger().info("Finished driving 1 meter forward into elevator")
