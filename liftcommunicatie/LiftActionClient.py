import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from building_management_interfaces.action import LiftControl


class LiftActionClient(Node):

    def __init__(self):
        super().__init__('lift_action_client')
        self._client = ActionClient(self, LiftControl, 'lift_control')

    def send_goal(self, lift_id: str, target_floor: int):
        self.get_logger().info('Wachten op server...')
        self._client.wait_for_server()

        goal = LiftControl.Goal()
        goal.lift_id = lift_id
        goal.target_floor = target_floor

        self.get_logger().info(f'Goal versturen: lift={lift_id} verdieping={target_floor}')
        future = self._client.send_goal_async(
            goal,
            feedback_callback=self.feedback_callback
        )
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal geweigerd!')
            return
        self.get_logger().info('Goal geaccepteerd')
        future = goal_handle.get_result_async()
        future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(f'Feedback: status={fb.status} | verdieping={fb.current_floor}')

    def result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Resultaat: success={result.success} | {result.message}')
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    client = LiftActionClient()
    client.send_goal(lift_id='lift_A', target_floor=3)
    rclpy.spin(client)