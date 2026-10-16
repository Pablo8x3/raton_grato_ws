import rclpy
from rclpy.node import Node

from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
from std_msgs.msg import Empty
from std_msgs.msg import Bool


import math


class GatoNode(Node):

    def __init__(self):
        super().__init__('gato')

        # Parámetros - obtener del YAML sin valores por defecto
        self.declare_parameter('max_linear_speed')
        self.declare_parameter('linear_gain')
        self.declare_parameter('angular_gain')
        self.declare_parameter('speed_increment')

        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.linear_gain = self.get_parameter('linear_gain').value
        self.angular_gain = self.get_parameter('angular_gain').value
        self.speed_increment = self.get_parameter('speed_increment').value

        # Estado
        self.gato_pose = None
        self.raton_pose = None
        self.game_over = False

        # Suscriptores
        self.create_subscription(
            Pose,
            '/turtle2/pose',
            self.gato_callback,
            10
        )

        self.create_subscription(
            Bool,
            '/game_over',
            self.game_over_callback,
            10
        )


        self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.raton_callback,
            10
        )

        self.create_subscription(
            Empty,
            '/raton_jump',
            self.jump_callback,
            10
        )

        # Publisher
        self.cmd_pub = self.create_publisher(
            Twist,
            '/turtle2/cmd_vel',
            10
        )

        # Timer
        self.timer = self.create_timer(0.05, self.control_loop)

    def gato_callback(self, msg):
        self.gato_pose = msg

    def raton_callback(self, msg):
        self.raton_pose = msg

    def jump_callback(self, msg):
        self.max_linear_speed += self.speed_increment
        self.get_logger().info(
            f'🐱 Velocidad máxima aumentada a {self.max_linear_speed:.2f}'
        )

    def control_loop(self):
        if self.game_over:
            return

        if self.gato_pose is None or self.raton_pose is None:
            return

        dx = self.raton_pose.x - self.gato_pose.x
        dy = self.raton_pose.y - self.gato_pose.y

        desired_theta = math.atan2(dy, dx)
        error_theta = desired_theta - self.gato_pose.theta
        error_theta = math.atan2(math.sin(error_theta), math.cos(error_theta))

        angular_z = self.angular_gain * error_theta

        linear_x = self.linear_gain * math.sqrt(dx**2 + dy**2)
        if linear_x > self.max_linear_speed:
            linear_x = self.max_linear_speed

        cmd = Twist()
        cmd.linear.x = linear_x
        cmd.angular.z = angular_z

        self.cmd_pub.publish(cmd)

    def game_over_callback(self, msg):
        if msg.data:
            self.game_over = True

            stop = Twist()
            self.cmd_pub.publish(stop)

            self.get_logger().info('🐱 Juego terminado, el gato se detiene')



def main():
    rclpy.init()
    node = GatoNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
