import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportRelative


class RatonNode(Node):

    def __init__(self):
        super().__init__('raton_node')  # Nombre del nodo

        self.declare_parameter('timer_period', 2.0)
        self.declare_parameter('jump_linear', 2.0)
        self.declare_parameter('jump_angular', 1.0)

        self.timer_period = self.get_parameter('timer_period').value
        self.jump_linear = self.get_parameter('jump_linear').value
        self.jump_angular = self.get_parameter('jump_angular').value

        self.teleport_client = self.create_client(TeleportRelative, 'turtle1/teleport_relative')

        while not self.teleport_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando al servicio teleport_relative...')


        self.timer = self.create_timer(
            self.timer_period,
            self.timer_callback
        )

    def timer_callback(self):
        request = TeleportRelative.Request()
        request.linear = self.jump_linear
        request.angular = self.jump_angular

        self.teleport_client.call_async(request)

        self.get_logger().info(
            f'Salto: linear={self.jump_linear}, angular={self.jump_angular}'
        )



def main(args=None):
    rclpy.init(args=args)

    node = RatonNode()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()
