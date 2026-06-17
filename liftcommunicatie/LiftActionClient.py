import argparse
import sys
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.utilities import remove_ros_args
from building_management_interfaces.action import LiftControl


class LiftActionClient(Node):

    def __init__(self):
        super().__init__('lift_action_client')
        self._client = ActionClient(self, LiftControl, 'lift_control')

    def send_goal(self, current_floor: int, target_floor: int, drive_reversed: bool):
        self.get_logger().info('Wachten op server...')
        self._client.wait_for_server()

        goal = LiftControl.Goal()
        goal.current_floor = current_floor
        goal.target_floor = target_floor
        goal.drive_reversed = drive_reversed

        direction = 'achteruit' if drive_reversed else 'vooruit'
        self.get_logger().info(
            f'Goal versturen: huidig={current_floor} doel={target_floor} richting={direction}'
        )
        future = self._client.send_goal_async(
            goal,
            feedback_callback=self.feedback_callback
        )
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal geweigerd!')
            rclpy.shutdown()
            return
        self.get_logger().info('Goal geaccepteerd')
        future = goal_handle.get_result_async()
        future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(f'Feedback: status={fb.status} | verdieping={fb.new_floor}')

    def result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Resultaat: success={result.success} | {result.message}')
        rclpy.shutdown()


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog='lift_action_client',
        description='Stuur een liftrit-goal: van welke verdieping, naar welke verdieping, '
                    'en of de robot vooruit of achteruit de lift in/uit rijdt.'
    )
    parser.add_argument('-c', '--current', type=int, required=True,
                        help='Huidige verdieping (0 = begane grond)')
    parser.add_argument('-t', '--target', type=int, required=True,
                        help='Doelverdieping (0 = begane grond)')
    parser.add_argument('-d', '--direction', choices=['forward', 'backward'], default='forward',
                        help='Rijrichting de lift in/uit (standaard: forward)')
    return parser.parse_args(argv)


def main(args=None):
    rclpy.init(args=args)
    argv = args if args is not None else sys.argv
    parsed = parse_args(remove_ros_args(argv)[1:])

    client = LiftActionClient()
    client.send_goal(
        current_floor=parsed.current,
        target_floor=parsed.target,
        drive_reversed=(parsed.direction == 'backward'),
    )
    rclpy.spin(client)
