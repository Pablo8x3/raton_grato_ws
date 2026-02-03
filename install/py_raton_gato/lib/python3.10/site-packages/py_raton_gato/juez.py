import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
import math


class JuezNode(Node):

    def __init__(self):
        super().__init__('juez_node')

        self.raton_pose = None
        self.gato_pose = None
        self.game_over = False

        self.capture_distance = 1.0

        self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.raton_callback,
            10
        )

        self.create_subscription(
            Pose,
            '/turtle2/pose',
            self.gato_callback,
            10
        )

        self.timer = self.create_timer(0.1, self.check_capture)

    def raton_callback(self, msg):
        self.raton_pose = msg

    def gato_callback(self, msg):
        self.gato_pose = msg

    def check_capture(self):
        if self.game_over:
            return

        if self.raton_pose is None or self.gato_pose is None:
            return

        dx = self.raton_pose.x - self.gato_pose.x
        dy = self.raton_pose.y - self.gato_pose.y
        distancia = math.sqrt(dx**2 + dy**2)

        if distancia < self.capture_distance:
            self.game_over = True
            self.get_logger().info('🐱 El gato ha capturado al ratón. FIN DEL JUEGO')


def main():
    rclpy.init()
    node = JuezNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
