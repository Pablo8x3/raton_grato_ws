import rclpy
from rclpy.node import Node

from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
import math

class NodoSeguidor (Node):

    def __init__(self):
        super().__init__('NodoSeguidor')

        # Prámetros - 1. los declaramos
        self.declare_parameter('linear_speed', 1.0)
        self.declare_parameter('angular_speed', 1.0)
        self.declare_parameter('k_linear', 1.0)
        self.declare_parameter('k_angular', 1.0)
        self.declare_parameter('cl_period', 0.05)


        # Parámetros - 2. Pillamos los valores de un archivo de parámetros
        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.k_linear = self.get_parameter('k_linear').value
        self.k_angular = self.get_parameter('k_angular').value
        self.cl_period = self.get_parameter('cl_period').value

        # Estados
        self.seguidor_pose = None
        self.controlado_pose = None

        # Suscriptores
        self.create_subscription(Pose,'/turtle2/pose', self.seguidor_callback, 10)
        self.create_subscription(Pose, '/turtle1/pose', self.controlado_callback, 10)

        # Publicadores
        self.seguidor_cmd = self.create_publisher(Twist, '/turtle2/cmd_vel', 10)

        # Timers 
        self.timer = self.create_timer(self.cl_period, self.control_loop)

    def seguidor_callback(self, msg):
        self.seguidor_pose = msg

    def controlado_callback(self, msg):
        self.controlado_pose = msg

    def control_loop(self):
        if self.controlado_pose is None or self.seguidor_pose is None:
            return

        dx = self.controlado_pose.x - self.seguidor_pose.x
        dy = self.controlado_pose.y - self.seguidor_pose.y

        desired_theta = math.atan2(dy,dx)
        error_theta = desired_theta - self.seguidor_pose.theta
        error_theta = math.atan2(math.sin(error_theta), math.cos(error_theta))

        angular_z = self.k_angular * error_theta

        linear_x = self.k_linear * math.sqrt(dx**2 + dy**2)
        if linear_x > self.linear_speed:
            linear_x = self.linear_speed

        cmd = Twist()
        cmd.linear.x = linear_x
        cmd.angular.z = angular_z

        self.seguidor_cmd.publish(cmd)


def main():
    rclpy.init()
    node = NodoSeguidor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()