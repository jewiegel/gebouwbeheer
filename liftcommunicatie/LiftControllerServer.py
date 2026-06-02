import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.callback_groups import ReentrantCallbackGroup

from .Communication.Protocols.TestLiftProtocol import TestLiftProtocol
from .Communication.Protocols.ICommunicationProtocol import ICommunicationProtocol

from .States.WaitingForDoorsState import WaitingForDoorsState
from .States.IRobotLiftState import IRobotLiftStateState
from .States.InElevatorState import InElevatorState
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

        self.current_state: IRobotLiftStateState = None
        self.current_floor = 0
        self.desired_floor = 0

        self.protocol.connect()
        if not self.protocol.wait_until_connected(timeout=5.0):
            raise RuntimeError("Could not connect to the websocket API before starting the action server")

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Mi bomboclat cancel request")
        return CancelResponse.ACCEPT


    def goal_callback(self, goal_request):
        if not self.protocol.is_connected():
            self.get_logger().warning("Rejecting goal because the websocket API is disconnected")
            return GoalResponse.REJECT

        self.get_logger().info(f"sukablyatt: deez: {goal_request.lift_id} en floor: {goal_request.target_floor}")
        return GoalResponse.ACCEPT


    async def execute_callback(self, goal_handle: ServerGoalHandle):
        self.get_logger().info("Execute callback gestart")
        result = LiftControl.Result()

        if not self.protocol.is_connected():
            goal_handle.abort()
            result.success = False
            result.message = "Websocket API disconnected"
            return result

        try:
            self.protocol.send_message(request_payload)
        except Exception as exc:
            self.get_logger().error(f"Failed to forward action goal to websocket API: {exc}")
            goal_handle.abort()
            result.success = False
            result.message = str(exc)
            return result

        goal_handle.succeed()
        result.success = True
        result.message = "Goal forwarded to websocket API"
        return result
    
    def transition_to_state(self, new_state):
        if self.current_state is not None:
            self.current_state.on_exit()

        self.current_state = new_state
        self.current_state.on_enter()

   
def main(args=None):
    rclpy.init(args=args)
    lift_controller_node = LiftControllerServer(TestLiftProtocol("ws://localhost:8765"))
    rclpy.spin(lift_controller_node)
    lift_controller_node.destroy_node()
    rclpy.shutdown()