import asyncio
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.callback_groups import ReentrantCallbackGroup

from .Communication.Protocols.ICommunicationProtocol import ICommunicationProtocol
from .Communication.Protocols.TestLiftProtocol import TestLiftProtocol
from .States.IRobotLiftState import IRobotLiftState
from .States.WaitingForElevatorState import WaitingForElevatorState
from .States.WaitingForDoorsState import WaitingForDoorsState
from .States.InElevatorState import InElevatorState
from .States.DrivingInElevatorState import DrivingInElevatorState
from .States.ExitingElevatorState import ExitingElevatorState

from building_management_interfaces.action import LiftControl


class LiftControllerServer(Node):
    def __init__(self, protocol: ICommunicationProtocol):
        super().__init__('lift_controller_node')
        self.protocol = protocol
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

        self.current_state: IRobotLiftState = None
        self._lift_id = None
        self._target_floor = None

        self.protocol.connect()
        if not self.protocol.wait_until_connected(timeout=5.0):
            raise RuntimeError("Could not connect to the elevator API before starting the action server")

    def transition_to_state(self, new_state: IRobotLiftState):
        if self.current_state is not None:
            self.current_state.on_exit()
        self.current_state = new_state
        self.current_state.on_enter()

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Cancel request received")
        return CancelResponse.ACCEPT

    def goal_callback(self, goal_request):
        if not self.protocol.is_connected():
            self.get_logger().warning("Rejecting goal: elevator API is disconnected")
            return GoalResponse.REJECT

        self.get_logger().info(
            f"Goal received: lift_id={goal_request.lift_id}, target_floor={goal_request.target_floor}"
        )
        return GoalResponse.ACCEPT

    async def execute_callback(self, goal_handle: ServerGoalHandle):
        self.get_logger().info("Executing lift control goal")
        result = LiftControl.Result()

        if not self.protocol.is_connected():
            goal_handle.abort()
            result.success = False
            result.message = "Elevator API disconnected"
            return result

        self._lift_id = goal_handle.request.lift_id
        self._target_floor = goal_handle.request.target_floor

        feedback = LiftControl.Feedback()

        try:
            self.transition_to_state(WaitingForElevatorState(self))
            feedback.status = "Waiting for elevator"
            goal_handle.publish_feedback(feedback)
            await asyncio.sleep(2.0)

            self.transition_to_state(WaitingForDoorsState(self))
            feedback.status = "Waiting for doors to open"
            goal_handle.publish_feedback(feedback)
            await asyncio.sleep(1.0)

            self.transition_to_state(InElevatorState(self))
            feedback.status = "Inside elevator, selecting floor"
            goal_handle.publish_feedback(feedback)
            await asyncio.sleep(1.0)

            self.transition_to_state(DrivingInElevatorState(self))
            feedback.status = "Driving to target floor"
            goal_handle.publish_feedback(feedback)
            await asyncio.sleep(3.0)

            self.transition_to_state(ExitingElevatorState(self))
            feedback.status = "Exiting elevator"
            goal_handle.publish_feedback(feedback)
            await asyncio.sleep(1.0)

            self.current_state.on_exit()
            self.current_state = None

        except Exception as exc:
            self.get_logger().error(f"Error during lift execution: {exc}")
            goal_handle.abort()
            result.success = False
            result.message = str(exc)
            return result

        goal_handle.succeed()
        result.success = True
        result.message = f"Successfully moved to floor {self._target_floor}"
        return result


def main(args=None):
    rclpy.init(args=args)
    lift_controller_node = LiftControllerServer(TestLiftProtocol("ws://localhost:8765"))
    rclpy.spin(lift_controller_node)
    lift_controller_node.destroy_node()
    rclpy.shutdown()
