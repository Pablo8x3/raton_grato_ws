# COPIA DIDÁCTICA DE seguidor.py: solo se añaden comentarios.
# Las instrucciones ejecutables conservan el comportamiento del original.
#
# IDEA DEL PROGRAMA
# turtle1 es la tortuga objetivo (llamada «controlado» en los atributos).
# turtle2 es la tortuga que debe perseguirla (llamada «seguidor»).
# El nodo recibe sus posiciones, calcula cómo acercarse y publica velocidades.
# Recorrido de los datos:
#   /turtle1/pose -> controlado_callback -> self.controlado_pose
#   /turtle2/pose -> seguidor_callback  -> self.seguidor_pose
#   temporizador -> control_loop -> /turtle2/cmd_vel -> turtlesim
# Publicar una orden y recibir una posición son operaciones diferentes:
# turtlesim mueve la tortuga y publica después su estado en el topic de pose.
#
# VOCABULARIO PARA LEER EL ARCHIVO
# Clase: definición de un tipo de objeto, con sus datos y operaciones.
# Instancia u objeto: un ejemplar concreto creado a partir de una clase.
# Atributo: dato asociado a un objeto; por ejemplo, self.seguidor_pose.
# Método: función definida en una clase; por ejemplo, control_loop.
# self: referencia a la instancia sobre la que se ejecuta un método.
# Variable local: nombre que pertenece a una llamada de función, como dx.
# Callback: función que entregamos para que otra parte del programa la llame
# cuando corresponda; aquí, el ejecutor de ROS 2 procesa mensajes y timers.
# Topic: canal de comunicación con nombre y un tipo de mensaje acordado.
#
# Referencias oficiales para ampliar las explicaciones de ROS 2:
# https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Beginner-Client-Libraries/Using-Parameters-In-A-Class-Python.rst
# https://github.com/ros2/rclpy/blob/jazzy/rclpy/rclpy/node.py
# https://github.com/ros2/rclpy/blob/jazzy/rclpy/rclpy/__init__.py
# https://github.com/ros2/rclpy/blob/jazzy/rclpy/rclpy/executors.py
# https://github.com/ros2/rclpy/blob/jazzy/rclpy/rclpy/qos.py
# https://github.com/ros/ros_tutorials/blob/jazzy/turtlesim/msg/Pose.msg
# https://github.com/ros2/common_interfaces/blob/jazzy/geometry_msgs/msg/Twist.msg

# import carga un módulo y permite acceder a sus nombres con un punto.
# rclpy es la biblioteca cliente de ROS 2 para Python; se apoya en capas
# nativas de ROS 2 para comunicarse mediante el middleware configurado.
import rclpy
# «from ... import ...» trae directamente el nombre Node a este archivo.
# Node será la clase base que aporta las operaciones de un nodo ROS 2.
from rclpy.node import Node

# String es una clase de mensaje de texto. En este programa no se utiliza;
# el import se conserva porque esta copia no corrige ni cambia el original.
from std_msgs.msg import String
# Pose es la clase de mensaje de turtlesim, distinta de geometry_msgs/Pose.
# Contiene x, y, theta, linear_velocity y angular_velocity.
# Aquí se consultan x e y (posición en el plano) y theta (ángulo en radianes).
from turtlesim.msg import Pose
# Twist representa una velocidad mediante dos vectores: linear y angular.
# Cada vector tiene componentes x, y, z. Es el tipo de /turtle2/cmd_vel.
from geometry_msgs.msg import Twist
# math es parte de la biblioteca estándar de Python, no un paquete ROS.
# Proporciona aquí atan2, sin, cos y sqrt para los cálculos geométricos.
import math

# «class» define la clase; todavía no crea el nodo que ejecutaremos.
# Los paréntesis indican herencia: NodoSeguidor es una subclase de Node.
# Hereda métodos como create_publisher y añade los métodos de persecución.
# Los dos puntos abren el bloque; la indentación indica qué pertenece a él.
class NodoSeguidor (Node):

    # __init__ inicializa una instancia cuando hacemos NodoSeguidor().
    # Técnicamente Python crea antes el objeto mediante __new__.
    # self recibe automáticamente la referencia a esa instancia:
    # no escribimos NodoSeguidor(self) al crear el objeto.
    def __init__(self):
        # super() permite buscar la implementación de la clase base según
        # el orden de resolución de métodos; aquí llama al __init__ de Node.
        # Esto inicializa la parte ROS del objeto antes de usar sus métodos.
        # 'NodoSeguidor' es el nombre ROS solicitado para el nodo; es distinto
        # del nombre de la clase Python, aunque aquí coincidan.
        super().__init__('NodoSeguidor')

        # Parámetros - 1. los declaramos.
        # Un parámetro ROS es configuración del nodo, accesible por su nombre.
        # declare_parameter registra el nombre y un valor predeterminado.
        # Un valor inicial pasado desde launch, YAML o --ros-args puede
        # sustituir al predeterminado. Los nombres entre comillas son str.
        # 1.0 es un float: sirve también para inferir el tipo del parámetro.
        # linear_speed: máximo de velocidad lineal usado en este controlador.
        self.declare_parameter('linear_speed', 1.0)
        # angular_speed: configuración prevista para la velocidad angular.
        # OJO: el original la declara y lee, pero no la aplica al giro.
        self.declare_parameter('angular_speed', 1.0)
        # k_linear: ganancia que convierte distancia en velocidad de avance.
        self.declare_parameter('k_linear', 1.0)
        # k_angular: ganancia que convierte error de ángulo en velocidad de giro.
        self.declare_parameter('k_angular', 1.0)
        # cl_period: intervalo solicitado para el control, en segundos.
        # 0.05 s corresponde nominalmente a 1 / 0.05 = 20 ejecuciones/s.
        self.declare_parameter('cl_period', 0.05)


        # Parámetros - 2. guardamos sus valores en atributos del objeto.
        # get_parameter devuelve un objeto Parameter; .value extrae el valor.
        # El «=» asigna ese valor al atributo situado a su izquierda.
        # get_parameter NO abre por sí mismo un YAML: consulta el parámetro
        # que ROS ya ha establecido para el nodo, con o sin archivo externo.
        # self.linear_speed es un atributo Python; 'linear_speed' es el nombre
        # de un parámetro ROS. Se llaman igual por comodidad, no por obligación.
        # Estas lecturas ocurren una vez durante la inicialización.
        # Un posterior «ros2 param set» no actualizará automáticamente estos
        # atributos: para eso habría que releer o gestionar los cambios.
        self.linear_speed = self.get_parameter('linear_speed').value
        # Guarda el valor angular, aunque este código no lo utiliza después.
        self.angular_speed = self.get_parameter('angular_speed').value
        # Guarda la ganancia lineal para usarla en cada cálculo de control.
        self.k_linear = self.get_parameter('k_linear').value
        # Guarda la ganancia angular para usarla en cada cálculo de control.
        self.k_angular = self.get_parameter('k_angular').value
        # Guarda el periodo con el que se creará el temporizador.
        self.cl_period = self.get_parameter('cl_period').value

        # Estados: información que debe persistir entre llamadas a métodos.
        # Un atributo con self pertenece a esta instancia y permite compartir
        # los datos entre __init__, los callbacks y control_loop.
        # Una variable local «seguidor_pose = None», sin self, no serviría
        # como este almacén compartido después de terminar __init__.
        #
        # ¿POR QUÉ None?
        # Al arrancar aún no hemos recibido una posición real. None expresa
        # «todavía no hay dato»; no significa posición cero ni mensaje vacío.
        # Creamos explícitamente ambos atributos con ese estado inicial.
        # Si no existieran y el control intentara leerlos antes del callback,
        # Python produciría AttributeError por atributo inexistente.
        # Con None existen, pero aún no tienen los campos .x, .y y .theta.
        # Por eso también es necesaria la comprobación del control_loop.
        # Usar Pose() aquí daría campos numéricos por defecto, que el programa
        # podría confundir con una posición medida que todavía no ha llegado.
        self.seguidor_pose = None
        # La posición del objetivo llega por otra suscripción independiente.
        # Recibir la pose del seguidor no implica tener ya la del objetivo.
        self.controlado_pose = None

        # Suscriptores: conectan cada topic de pose con su callback.
        # Los argumentos son: tipo, nombre del topic, callback y QoS.
        # «self.seguidor_callback», sin (), entrega un método ligado a self;
        # poner () intentaría ejecutarlo ahora, además sin el argumento msg.
        # El 10 configura una profundidad de historial KEEP_LAST de 10
        # mensajes por suscripción. No es frecuencia ni número de callbacks.
        # El nombre empieza por /: es absoluto, aunque admite remapeo ROS.
        # El propio Node conserva las suscripciones creadas; aquí no hace
        # falta asignarlas a atributos para que sigan existiendo.
        self.create_subscription(Pose,'/turtle2/pose', self.seguidor_callback, 10)
        # Este topic proporciona el estado de turtle1, la tortuga objetivo.
        self.create_subscription(Pose, '/turtle1/pose', self.controlado_callback, 10)

        # Publicadores: crean el medio para enviar mensajes a un topic.
        # Guardamos el objeto Publisher en self.seguidor_cmd porque después
        # necesitaremos llamar a su método publish desde control_loop.
        # El tipo debe corresponder al esperado por el receptor: Twist.
        # El 10 vuelve a ser profundidad de historial, ahora del publicador.
        self.seguidor_cmd = self.create_publisher(Twist, '/turtle2/cmd_vel', 10)

        # Timers: solicitan llamadas periódicas a un callback.
        # Pasamos el periodo y el método; no llamamos a control_loop aquí.
        # self.timer guarda el objeto Timer, no el resultado del control.
        # El ejecutor procesará el temporizador cuando hagamos spin.
        # La periodicidad es nominal: puede retrasarse si el ejecutor está
        # ocupado; este programa no establece garantías de tiempo real.
        self.timer = self.create_timer(self.cl_period, self.control_loop)

    # Este método lo llama el ejecutor al procesar un mensaje de turtle2.
    # self se proporciona por ser un método ligado; msg es el mensaje Pose
    # recibido. No tenemos que llamar al callback manualmente desde main.
    def seguidor_callback(self, msg):
        # La asignación sustituye la referencia anterior por el nuevo mensaje.
        # No copia campo a campo: self.seguidor_pose referencia ese objeto.
        # Tras el primer mensaje, deja de ser None; después conserva la
        # última pose procesada, hasta que otro mensaje la sustituya.
        self.seguidor_pose = msg

    # Callback equivalente para la pose de turtle1, el objetivo.
    def controlado_callback(self, msg):
        # Mantiene el último mensaje del objetivo disponible para el control.
        self.controlado_pose = msg

    # Una ejecución de este método calcula y publica una orden de velocidad.
    # Aunque se llame «loop», no contiene un while: la repetición la provoca
    # el temporizador, que vuelve a solicitar el callback periódicamente.
    def control_loop(self):
        # ¿POR QUÉ ESTE if ADEMÁS DE INICIALIZAR CON None?
        # No hay garantía de que ambas poses se hayan recibido y procesado
        # antes de la primera ejecución del temporizador.
        # «is None» comprueba identidad con el objeto único None.
        # «or» da verdadero si falta cualquiera de las dos poses; usa
        # cortocircuito: si la primera condición es verdadera, no evalúa
        # la segunda, porque el resultado ya está decidido.
        if self.controlado_pose is None or self.seguidor_pose is None:
            # return sin expresión termina ESTA llamada y devuelve None.
            # No cierra el nodo, no cancela el timer ni detiene spin.
            # Esta llamada no publica nada. En otra llamada se comprobará
            # de nuevo si los callbacks ya han rellenado ambos atributos.
            # Sin este if, leer None.x provocaría AttributeError.
            return

        # Si llegamos aquí, ambos atributos contienen mensajes de pose.
        # dx y dy son variables locales: desplazamiento objetivo - seguidor.
        # El punto accede a atributos: self.controlado_pose.x es el campo x
        # del mensaje guardado en el atributo controlado_pose del nodo.
        # Ejemplo: objetivo x=5 y seguidor x=2 -> dx=3, hacia la derecha.
        dx = self.controlado_pose.x - self.seguidor_pose.x
        # Hace la misma resta en el eje vertical del plano de turtlesim.
        dy = self.controlado_pose.y - self.seguidor_pose.y

        # atan2(y, x) devuelve el ángulo del vector (x, y), en radianes.
        # Aquí usamos (dy, dx) para apuntar desde el seguidor al objetivo.
        # Considera el cuadrante y permite dx=0 sin dividir entre cero.
        desired_theta = math.atan2(dy,dx)
        # Error = orientación que queremos - orientación actual.
        # theta es el ángulo de la tortuga, no su velocidad angular.
        error_theta = desired_theta - self.seguidor_pose.theta
        # Un ángulo tiene representaciones equivalentes separadas por 2*pi.
        # atan2(sin(error), cos(error)) envuelve el error a [-pi, pi].
        # Así se escoge un giro de magnitud no mayor que pi; justo a pi
        # hay dos sentidos de giro igualmente cortos.
        # Ejemplo: deseado -179° y actual 179° -> resta -358° -> error +2°.
        # La operación real usa radianes; los grados aquí son ilustrativos.
        error_theta = math.atan2(math.sin(error_theta), math.cos(error_theta))

        # Control proporcional angular: cuanto mayor sea el error, mayor giro.
        # k_angular es la ganancia; multiplicar por ella escala la respuesta.
        # Con ganancia positiva, el signo del error decide el sentido de giro.
        # angular_z es velocidad alrededor del eje z, perpendicular al plano.
        # En turtlesim se expresa en rad/s.
        # OJO: aquí no se limita con self.angular_speed. Ese parámetro no
        # impone un máximo angular en la implementación original.
        angular_z = self.k_angular * error_theta

        # Distancia euclídea por Pitágoras: sqrt(dx**2 + dy**2).
        # ** es potencia en Python; no debe confundirse con ^, que es XOR.
        # Multiplicamos la distancia por k_linear para obtener velocidad:
        # con ganancia positiva, lejos avanza más y cerca avanza menos.
        # En turtlesim x e y usan unidades del simulador; no son píxeles.
        # linear_x expresa avance en el eje x local de la propia tortuga,
        # es decir, hacia donde está orientada, no en el eje x del mapa.
        linear_x = self.k_linear * math.sqrt(dx**2 + dy**2)
        # Saturación superior: si la velocidad calculada supera el máximo,
        # la sustituimos por ese máximo. Si no, se conserva el cálculo.
        # Este programa presupone parámetros apropiados: no valida ganancias
        # ni límites negativos, ni aplica una saturación inferior.
        if linear_x > self.linear_speed:
            # Reasigna la variable local; no cambia el parámetro ROS.
            linear_x = self.linear_speed

        # Twist() crea un NUEVO objeto mensaje en cada llamada al control.
        # Sus componentes numéricas no asignadas quedan a cero por defecto.
        # cmd es local; se usa para preparar la orden que se va a publicar.
        cmd = Twist()
        # Acceso encadenado: cmd -> vector linear -> componente x.
        # Asignamos el avance; linear.y y linear.z permanecen a cero.
        cmd.linear.x = linear_x
        # Asignamos el giro en el plano; angular.x e y permanecen a cero.
        cmd.angular.z = angular_z

        # El Publisher envía este mensaje por /turtle2/cmd_vel.
        # turtlesim lo recibe y aplica las velocidades a turtle2.
        # publish no mueve directamente la tortuga ni espera a que llegue
        # al objetivo: futuras poses permiten calcular nuevas órdenes.
        self.seguidor_cmd.publish(cmd)


# main es una función del módulo, fuera de la clase (sin indentación).
# Por eso no lleva self: no es un método de una instancia.
# Definirla no la ejecuta. En setup.py, el entry point original
# «seguidor = pilla_pilla.seguidor:main» hace que ros2 run invoque main.
# Esta copia no añade otro ejecutable ni modifica dicho entry point.
def main():
    # Inicializa el contexto ROS antes de crear el nodo.
    # Por defecto también procesa los argumentos ROS del proceso.
    rclpy.init()
    # Construye una instancia: se ejecuta su __init__, que configura datos,
    # parámetros y entidades ROS. node guarda una referencia al objeto.
    node = NodoSeguidor()
    # spin mantiene al ejecutor atendiendo callbacks mientras el contexto
    # esté activo. No consiste en llamar continuamente a control_loop.
    # Sin ejecutor procesando trabajo, los callbacks creados aquí no se
    # ejecutan solo por existir las suscripciones y el temporizador.
    # En esta configuración habitual, el ejecutor global es de un hilo:
    # ejecuta un callback cada vez, aunque los mensajes lleguen de forma
    # asíncrona y su orden respecto al timer no esté garantizado.
    rclpy.spin(node)
    # Libera explícitamente los recursos ROS asociados al nodo.
    # No es lo mismo que borrar la variable Python node.
    node.destroy_node()
    # Cierra el contexto ROS, compartido aquí por el nodo y el ejecutor.
    # Estas dos últimas líneas solo se alcanzan si spin retorna normalmente;
    # el original no usa try/finally para garantizar limpieza ante excepciones.
    rclpy.shutdown()

# REPASO DEL ARRANQUE: None + if + callbacks + spin
# 1. __init__ crea las dos poses con None: «aún sin información».
# 2. Se crean las suscripciones y el temporizador.
# 3. spin permite procesar el trabajo que vaya estando disponible.
# 4. Si el timer se procesa antes de tener ambas poses, el if hace return.
# 5. Cada callback de pose reemplaza un None (o una pose anterior) por msg.
# 6. Cuando hay ambas, el siguiente control calcula dx, dy, giro y avance.
#
# ALCANCE DE LA COMPROBACIÓN
# El if garantiza que se haya procesado al menos un mensaje de cada pose.
# No comprueba su antigüedad ni que las dos correspondan al mismo instante.
# Si un emisor deja de publicar después, su último mensaje sigue guardado:
# el atributo no vuelve automáticamente a None.
# El controlador también ordena avanzar aunque aún haya error angular;
# no hay una fase separada de «primero orientar y después avanzar».
# Estos son detalles del comportamiento conservado, no cambios en esta copia.
