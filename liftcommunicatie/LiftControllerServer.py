import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup

from .Communication.Protocols import TestLiftProtocol
from .Communication.Protocols import ICommunicationProtocol

from building_management_interfaces.action import LiftControl

class LiftControllerServer(Node):
    def __init__(self):
        super().__init__('lift_controller_node')
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

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Mi bomboclat cancel request")
        return CancelResponse.ACCEPT


    def goal_callback(self, goal_request):
        self.get_logger().info(f"sukablyatt: deez: {goal_request.lift_id} en floor: {goal_request.target_floor}")
        return GoalResponse.ACCEPT


    async def execute_callback(self, goal_handle: ServerGoalHandle):
        self.get_logger().info("Execute callback gestart")

   
def main(args=None):
    lift_protocol = TestLiftProtocol()
    lift_protocol.setup()


    rclpy.init(args=args)
    lift_controller_node = LiftControllerServer()
    rclpy.spin(lift_controller_node)
    lift_controller_node.destroy_node()
    rclpy.shutdown()