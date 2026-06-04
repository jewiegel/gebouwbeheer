import threading
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
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
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'base_link'
        goal.pose.header.stamp = self.context.get_clock().now().to_msg()
        goal.pose.pose.position.x = 1.0
        goal.pose.pose.orientation.w = 1.0

        self.context._action_client.wait_for_server()
        future = self.context._action_client.send_goal_async(goal)
        future.add_done_callback(self._goal_response_callback)
        self._nav_done.wait()

        if not self._nav_succeeded:
            raise RuntimeError("Navigation failed: could not drive 1 meter forward")
        self.context.transition_to_state(ExitingElevatorState(self.context))

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.context.get_logger().error("Navigation goal rejected")
            self._nav_done.set()
            return
        goal_handle.get_result_async().add_done_callback(self._result_callback)

    def _result_callback(self, future):
        status = future.result().status
        self._nav_succeeded = (status == GoalStatus.STATUS_SUCCEEDED)
        if not self._nav_succeeded:
            self.context.get_logger().error(f"Navigation failed with status {status}")
        self._nav_done.set()

    def on_exit(self):
        self.context.get_logger().info("Finished driving 1 meter forward")
