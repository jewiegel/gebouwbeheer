import queue
import threading
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse, ActionClient
from rclpy.action.server import ServerGoalHandle
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from nav2_msgs.action import NavigateToPose, DriveOnHeading, BackUp
from action_msgs.msg import GoalStatus

from .Exceptions import GoalCancelledError
from .Communication.Protocols.ICommunicationProtocol import ICommunicationProtocol
from .Communication.Protocols.TestLiftProtocol import TestLiftProtocol
from .Communication.Transformers.IResponseTransformer import IResponseTransformer
from .Communication.Transformers.TestLiftProtocolTransformer import TestLiftProtocolTransformer
from .States.IRobotLiftState import IRobotLiftState
from .States.WaitingForElevatorState import WaitingForElevatorState

from building_management_interfaces.action import LiftControl


class LiftControllerServer(Node):
    # How often blocking waits wake up to check for cancellation
    CANCEL_POLL_INTERVAL = 0.5

    # Distance (meters) the robot drives forward into / out of the elevator, per floor.
    # Reflects how far the elevator car sits from the robot's waiting spot at each
    # floor's lobby. Used on current_floor when entering and on target_floor when exiting.
    # Floor numbering: 0 = begane grond, 1 = eerste verdieping, ...
    FLOOR_DRIVE_DISTANCES = {
        0: 1.6,   # begane grond
        1: 0.8,   # eerste verdieping
    }
    DEFAULT_DRIVE_DISTANCE = 1.0

    # Driving parameters shared by the into/out-of elevator moves
    DRIVE_SPEED = 0.2
    DRIVE_TIME_ALLOWANCE_SEC = 30
    NAV_TIMEOUT = 60.0

    def __init__(self, protocol: ICommunicationProtocol, transformer: IResponseTransformer):
        super().__init__('lift_controller_node')
        self.protocol = protocol
        self.transformer = transformer
        self._cb_group = ReentrantCallbackGroup()

        self._action_server = ActionServer(
            self,
            LiftControl,
            'lift_control',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self._cb_group
        )

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose', callback_group=self._cb_group)
        self._drive_on_heading_client = ActionClient(self, DriveOnHeading, 'drive_on_heading', callback_group=self._cb_group)
        self._backup_client = ActionClient(self, BackUp, 'backup', callback_group=self._cb_group)

        self.current_state: IRobotLiftState = None
        self._busy = False
        self._current_floor = None
        self._target_floor = None
        self._goal_handle: ServerGoalHandle = None
        self._response_queues: dict = {}

        # Whether the robot drives backward into/out of the elevator. Set per goal from
        # the request's drive_reversed field (the robot enters and exits the same way).
        self._drive_reversed = False
        self._nav_done: threading.Event = None
        self._nav_succeeded = False
        self._nav_goal_handle = None

        self.protocol.set_message_callback(self._on_lift_message)
        self.protocol.connect()
        if not self.protocol.wait_until_connected(timeout=5.0):
            raise RuntimeError("Could not connect to the elevator API before starting the action server")

    def get_drive_distance(self, floor: int) -> float:
        """Distance the robot should drive forward into/out of the elevator at this floor."""
        distance = self.FLOOR_DRIVE_DISTANCES.get(floor)
        if distance is None:
            self.get_logger().warning(
                f"No drive distance configured for floor {floor}, using default {self.DEFAULT_DRIVE_DISTANCE} m"
            )
            return self.DEFAULT_DRIVE_DISTANCE
        return distance

    @property
    def drive_direction_label(self) -> str:
        return "backward" if self._drive_reversed else "forward"

    def drive(self, distance: float) -> None:
        """Drive `distance` meters into/out of the elevator in the robot's current facing
        direction: DriveOnHeading when going forward, BackUp when reversed. Blocks until done.
        Raises RuntimeError on rejection/timeout/failure and GoalCancelledError on cancel."""
        if self._drive_reversed:
            client = self._backup_client
            goal = BackUp.Goal()
            action_name = 'backup'
        else:
            client = self._drive_on_heading_client
            goal = DriveOnHeading.Goal()
            action_name = 'drive_on_heading'
        goal.target.x = distance
        goal.speed = self.DRIVE_SPEED
        goal.time_allowance.sec = self.DRIVE_TIME_ALLOWANCE_SEC

        self._nav_done = threading.Event()
        self._nav_succeeded = False
        self._nav_goal_handle = None

        if not client.wait_for_server(timeout_sec=5.0):
            raise RuntimeError(f"{action_name} action server not available")
        send_future = client.send_goal_async(goal)
        send_future.add_done_callback(self._drive_goal_response_callback)

        try:
            finished = self.wait_for_event(self._nav_done, timeout=self.NAV_TIMEOUT)
        except GoalCancelledError:
            if self._nav_goal_handle is not None:
                self._nav_goal_handle.cancel_goal_async()
            raise
        if not finished:
            raise RuntimeError(f"{action_name} timed out after {self.NAV_TIMEOUT} s")
        if not self._nav_succeeded:
            raise RuntimeError(f"{action_name} failed: could not drive {distance} m {self.drive_direction_label}")

    def _drive_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Drive goal rejected")
            self._nav_done.set()
            return
        self._nav_goal_handle = goal_handle
        goal_handle.get_result_async().add_done_callback(self._drive_result_callback)

    def _drive_result_callback(self, future):
        status = future.result().status
        self._nav_succeeded = (status == GoalStatus.STATUS_SUCCEEDED)
        if not self._nav_succeeded:
            self.get_logger().error(f"Drive failed with status {status}")
        self._nav_done.set()

    def publish_feedback(self, status: str, new_floor: int = 0):
        feedback = LiftControl.Feedback()
        feedback.status = status
        feedback.new_floor = new_floor
        self._goal_handle.publish_feedback(feedback)

    def prepare_for_response(self, response_type):
        """Create the inbox for a response type. Call this BEFORE sending the request,
        so a fast response can't arrive without a place to land."""
        self._response_queues[response_type] = queue.Queue()

    def wait_for_response(self, response_type, timeout: float):
        """Block until a response of the given type arrives.

        Returns the response, or None on timeout.
        Raises GoalCancelledError when the action client cancels the goal.
        """
        q = self._response_queues[response_type]
        deadline = time.monotonic() + timeout
        while True:
            if self._goal_handle.is_cancel_requested:
                raise GoalCancelledError()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                return q.get(timeout=min(self.CANCEL_POLL_INTERVAL, remaining))
            except queue.Empty:
                continue

    def wait_for_event(self, event, timeout: float) -> bool:
        """Like event.wait(timeout), but raises GoalCancelledError when the
        action client cancels the goal. Returns False on timeout."""
        deadline = time.monotonic() + timeout
        while True:
            if self._goal_handle.is_cancel_requested:
                raise GoalCancelledError()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            if event.wait(timeout=min(self.CANCEL_POLL_INTERVAL, remaining)):
                return True

    def _on_lift_message(self, message: dict):
        response = self.transformer.to_response(message)
        if response is None:
            return
        q = self._response_queues.get(type(response))
        if q is not None:
            q.put(response)

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Cancel request received")
        return CancelResponse.ACCEPT

    def goal_callback(self, goal_request):
        if not self.protocol.is_connected():
            self.get_logger().warning("Rejecting goal: elevator API is disconnected")
            return GoalResponse.REJECT

        if self._busy:
            self.get_logger().warning("Rejecting goal: a lift goal is already being executed")
            return GoalResponse.REJECT

        self.get_logger().info(
            f"Goal received: current_floor={goal_request.current_floor}, target_floor={goal_request.target_floor}"
        )
        return GoalResponse.ACCEPT

    def execute_callback(self, goal_handle: ServerGoalHandle):
        result = LiftControl.Result()

        if not self.protocol.is_connected():
            goal_handle.abort()
            result.success = False
            result.message = "Elevator API disconnected"
            return result

        self._busy = True
        self._goal_handle = goal_handle
        self._current_floor = goal_handle.request.current_floor
        self._target_floor = goal_handle.request.target_floor
        self._drive_reversed = goal_handle.request.drive_reversed
        self._response_queues = {}
        self.get_logger().info(f"Robot will drive {self.drive_direction_label} into/out of the elevator")

        try:
            state = WaitingForElevatorState(self)
            while state is not None:
                self.current_state = state
                state.on_enter()
                next_state = state.execute()
                state.on_exit()
                state = next_state
        except GoalCancelledError:
            self.get_logger().info("Goal cancelled by client")
            goal_handle.canceled()
            result.success = False
            result.message = "Cancelled by client"
            return result
        except Exception as exc:
            self.get_logger().error(f"Error during lift execution: {exc}")
            goal_handle.abort()
            result.success = False
            result.message = str(exc)
            return result
        finally:
            self.current_state = None
            self._busy = False

        goal_handle.succeed()
        result.success = True
        result.message = f"Successfully moved to floor {self._target_floor}"
        return result


def main(args=None):
    rclpy.init(args=args)
    executor = MultiThreadedExecutor()
    lift_controller_node = LiftControllerServer(TestLiftProtocol("ws://10.103.103.123:80/ws"), TestLiftProtocolTransformer())
    executor.add_node(lift_controller_node)
    executor.spin()
    lift_controller_node.destroy_node()
    rclpy.shutdown()
