import rclpy
from rclpy.node import Node

class LiftControllerNode(Node):
    def __init__(self):
        super().__init__('lift_controller_node')
        self.get_logger().info('Lift Controller Node has been started.')
        
def main(args=None):
    rclpy.init(args=args)
    lift_controller_node = LiftControllerNode()
    rclpy.spin(lift_controller_node)
    lift_controller_node.destroy_node()
    rclpy.shutdown()