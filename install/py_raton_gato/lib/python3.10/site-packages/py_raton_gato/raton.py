import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportRelative
from std_msgs.msg import Bool



class RatonNode(Node):

    def __init__(self):
        super().__init__('raton')  # Nombre del nodo

        self.game_over = False

        # Obtener parámetros del YAML sin valores por defecto
        self.declare_parameter('timer_period')
        self.declare_parameter('jump_linear')
        self.declare_parameter('jump_angular')

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
    

        self.create_subscription(
            Bool,
            '/game_over',
            self.game_over_callback,
            10
        )

    def game_over_callback(self, msg):
        if msg.data:
            self.game_over = True
            self.get_logger().info('🐭 Juego terminado, el ratón se detiene')


    def timer_callback(self):
        if self.game_over:
            return
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
