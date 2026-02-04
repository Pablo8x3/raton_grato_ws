import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportRelative
from std_msgs.msg import Bool
from turtlesim.msg import Pose
import math



class RatonNode(Node):

    def __init__(self):
        super().__init__('raton')  # Nombre del nodo

        self.game_over = False
        self.gato_pose = None
        self.raton_pose = None
        self.wall_margin = 0.5  # Margen para detectar proximidad a pared
        self.world_max = 11.0  # Límite del mundo en turtlesim

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
            self.control_loop
        )
    

        self.create_subscription(
            Bool,
            '/game_over',
            self.game_over_callback,
            10
        )

        self.create_subscription(
            Pose,
            '/turtle2/pose',
            self.gato_callback,
            10
        )

        self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.raton_callback,
            10
        )

    def gato_callback(self, msg):
        self.gato_pose = msg

    def raton_callback(self, msg):
        self.raton_pose = msg

    


    def game_over_callback(self, msg):
        if msg.data:
            self.game_over = True
            self.get_logger().info('🐭 Juego terminado, el ratón se detiene')

    def is_near_wall(self):
        """Detecta si el ratón está cerca de alguna pared"""
        if self.raton_pose is None:
            return False, None
        
        x = self.raton_pose.x
        y = self.raton_pose.y
        
        # Detectar proximidad a paredes
        if x < self.wall_margin:
            return True, "izquierda"
        elif x > self.world_max - self.wall_margin:
            return True, "derecha"
        elif y < self.wall_margin:
            return True, "abajo"
        elif y > self.world_max - self.wall_margin:
            return True, "arriba"
        
        return False, None
    
    def get_tangential_direction(self, wall_side):
        """Calcula dirección tangencial para moverse alrededor de la pared"""
        if self.gato_pose is None or self.raton_pose is None:
            return 0
        
        dx = self.gato_pose.x - self.raton_pose.x
        dy = self.gato_pose.y - self.raton_pose.y
        direction_to_cat = math.atan2(dy, dx)
        
        # Añadir rotación tangencial según el lado de la pared
        if wall_side == "izquierda":
            tangential = direction_to_cat + math.pi/2  # Girar 90° a favor del reloj
        elif wall_side == "derecha":
            tangential = direction_to_cat - math.pi/2  # Girar 90° en contra
        elif wall_side == "abajo":
            tangential = direction_to_cat + math.pi/2
        elif wall_side == "arriba":
            tangential = direction_to_cat - math.pi/2
        else:
            tangential = direction_to_cat
        
        # Normalizar el ángulo a [-π, π]
        tangential = math.atan2(math.sin(tangential), math.cos(tangential))
        return tangential


    def control_loop(self):
        if self.game_over:
            return
        
        if self.gato_pose is None or self.raton_pose is None:
            return
            
        request = TeleportRelative.Request()

        # Detectar si está cerca de una pared
        near_wall, wall_side = self.is_near_wall()
        
        if near_wall:
            # Moverse tangencialmente alrededor de la pared
            tangential_direction = self.get_tangential_direction(wall_side)
            current_theta = self.raton_pose.theta
            angle_diff = tangential_direction - current_theta
            angle_diff = math.atan2(math.sin(angle_diff), math.cos(angle_diff))
            
            request.linear = self.jump_linear
            request.angular = angle_diff
            
            self.get_logger().info(
                f'⚠️ PARED DETECTADA ({wall_side}) | Girando tangencialmente'
            )
        else:
            # Calcular dirección hacia el gato
            dx = self.gato_pose.x - self.raton_pose.x
            dy = self.gato_pose.y - self.raton_pose.y
            
            direction_to_cat = math.atan2(dy, dx)
            
            # Dirección opuesta al gato (sumar π)
            opposite_direction = direction_to_cat + math.pi
            
            # Normalizar el ángulo a [-π, π]
            opposite_direction = math.atan2(math.sin(opposite_direction), math.cos(opposite_direction))
            
            # Calcular la diferencia angular con la orientación actual del ratón
            current_theta = self.raton_pose.theta
            angle_diff = opposite_direction - current_theta
            
            # Normalizar la diferencia angular a [-π, π]
            angle_diff = math.atan2(math.sin(angle_diff), math.cos(angle_diff))

            # Usar la diferencia angular para girar hacia la dirección opuesta
            request.linear = self.jump_linear
            request.angular = angle_diff

            distance = math.sqrt(dx**2 + dy**2)
            self.get_logger().info(
                f'Distancia al gato: {distance:.2f} | '
                f'Ángulo opuesto: {math.degrees(opposite_direction):.1f}° | '
                f'Salto: linear={self.jump_linear}, angular={angle_diff:.2f}'
            )

        self.teleport_client.call_async(request)



def main(args=None):
    rclpy.init(args=args)

    node = RatonNode()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()
