import queue
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse, ActionClient
from rclpy.action.server import ServerGoalHandle
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from nav2_msgs.action import NavigateToPose, DriveOnHeading, BackUp

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

        self.protocol.set_message_callback(self._on_lift_message)
        self.protocol.connect()
        if not self.protocol.wait_until_connected(timeout=5.0):
            raise RuntimeError("Could not connect to the elevator API before starting the action server")

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
        self._response_queues = {}

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
    lift_controller_node = LiftControllerServer(TestLiftProtocol("ws://10.103.103.110:80/ws"), TestLiftProtocolTransformer())
    executor.add_node(lift_controller_node)
    executor.spin()
    lift_controller_node.destroy_node()
    rclpy.shutdown()
