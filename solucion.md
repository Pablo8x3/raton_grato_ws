# Solución de la práctica: una tortuga te sigue

Consulta este archivo después de intentar los pasos del PDF. Incluye la solución del juego mínimo y de la primera mejora recomendada: el launch. Los demás retos del PDF quedan como ejercicios.

El ejemplo usa **funciones y variables**, sin definir clases ni utilizar herencia. Se apoya en un nodo que crea la propia biblioteca ROS. Está pensado para Ubuntu 24.04, ROS 2 Jazzy y Python 3.

## 1. Preparar el paquete

Si ya creaste el paquete, no repitas su creación. Estos comandos usan un workspace separado en `~/pilla_pilla_ws`. Si trabajas en otro, sustituye esa ruta por la tuya en todos los pasos.

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p ~/pilla_pilla_ws/src
cd ~/pilla_pilla_ws/src
ros2 pkg create pilla_pilla --build-type ament_python \
  --license Apache-2.0 \
  --dependencies rclpy turtlesim geometry_msgs
```

La estructura final, incluyendo el launch opcional, será:

```text
~/pilla_pilla_ws/src/pilla_pilla/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/pilla_pilla
├── pilla_pilla/
│   ├── __init__.py
│   └── seguidor.py
└── launch/
    └── juego.launch.py
```

Conserva los archivos generados por `ros2 pkg create`. Los siguientes pasos indican qué añadir o editar.

## 2. Programa completo: `pilla_pilla/seguidor.py`

Guarda este bloque en `~/pilla_pilla_ws/src/pilla_pilla/pilla_pilla/seguidor.py`:

```python
import math

import rclpy
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose


# Datos compartidos por las funciones de este pequeño programa.
posicion_jugador = None
posicion_seguidor = None
publicador = None


def recibir_jugador(mensaje):
    global posicion_jugador
    posicion_jugador = mensaje


def recibir_seguidor(mensaje):
    global posicion_seguidor
    posicion_seguidor = mensaje


def seguir():
    # No calculamos hasta tener las dos posiciones.
    if posicion_jugador is None or posicion_seguidor is None:
        return

    dx = posicion_jugador.x - posicion_seguidor.x
    dy = posicion_jugador.y - posicion_seguidor.y
    distancia = math.hypot(dx, dy)

    direccion = math.atan2(dy, dx)
    error = direccion - posicion_seguidor.theta
    # Elegir el giro corto, con un ángulo entre -pi y pi.
    error = math.atan2(math.sin(error), math.cos(error))

    velocidad = Twist()
    velocidad.linear.x = min(1.0, distancia)
    velocidad.angular.z = 4.0 * error
    publicador.publish(velocidad)


def main(args=None):
    global publicador

    rclpy.init(args=args)
    nodo = rclpy.create_node('seguidor')

    publicador = nodo.create_publisher(
        Twist, '/turtle2/cmd_vel', 10)

    nodo.create_subscription(
        Pose, '/turtle1/pose', recibir_jugador, 10)
    nodo.create_subscription(
        Pose, '/turtle2/pose', recibir_seguidor, 10)

    nodo.create_timer(0.05, seguir)

    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
```

Qué significa cada parte:

- Las dos funciones `recibir_...` guardan la última posición recibida. ROS las llama cuando llega un mensaje.
- `global` permite que una función sustituya el valor de una variable definida fuera de ella. Aquí simplifica el intercambio de datos entre funciones; no es necesario para leer esas variables.
- `seguir` consulta los datos, calcula la dirección y publica una velocidad. ROS la llama cada 0,05 segundos.
- El punto en `posicion_jugador.x` permite leer un campo del mensaje. No necesitas definir una clase para usarlo. ROS proporciona los mensajes y sus campos.
- `main` prepara las conexiones. `rclpy.spin` mantiene el nodo atendiendo mensajes y temporizadores hasta que lo cierras.
- La velocidad de avance está limitada a 1,0 y disminuye al acercarse. No hay captura: si el jugador se aleja otra vez, la persecución continúa.

## 3. Registrar el ejecutable

En `~/pilla_pilla_ws/src/pilla_pilla/setup.py`, sustituye el bloque `entry_points` generado por este. Conserva el resto del archivo:

```python
entry_points={
    'console_scripts': [
        'seguidor = pilla_pilla.seguidor:main',
    ],
},
```

La entrada relaciona el nombre que usas en la terminal, `seguidor`, con la función `main` del archivo `seguidor.py`.

Construye desde la raíz del workspace:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/pilla_pilla_ws
colcon build --symlink-install --packages-select pilla_pilla
source install/setup.bash
ros2 pkg executables pilla_pilla
```

Debes ver `pilla_pilla seguidor`. Si modificas `setup.py`, vuelve a construir. Reinicia el programa después de modificar el código Python.

## 4. Ejecutar la primera parte manualmente

Usa tres terminales. No tengas abierto a la vez otro simulador o el launch del juego original.

Terminal A: abre el simulador. Este crea `turtle1` en el centro.

```bash
source /opt/ros/jazzy/setup.bash
ros2 run turtlesim turtlesim_node
```

Terminal B: crea `turtle2` antes de mover al jugador y después abre el teclado.

```bash
source /opt/ros/jazzy/setup.bash
ros2 service call /spawn turtlesim/srv/Spawn \
  "{x: 1.0, y: 1.0, theta: 0.0, name: 'turtle2'}"
ros2 run turtlesim turtle_teleop_key
```

Terminal C: ejecuta tu seguidor.

```bash
source /opt/ros/jazzy/setup.bash
source ~/pilla_pilla_ws/install/setup.bash
ros2 run pilla_pilla seguidor
```

Haz clic en la terminal B para controlar `turtle1` con las flechas. `turtle2` debe seguirla. Cierra los tres procesos con Ctrl+C. Para repetir, empieza con un simulador nuevo y crea de nuevo `turtle2`.

## 5. Primera mejora recomendada: launch completo

El launch inicia el simulador, crea `turtle2` y ejecuta el seguidor. El teclado se mantiene en una terminal aparte para poder leer las teclas.

### Archivo `launch/juego.launch.py`

Crea la carpeta y abre el archivo con tu editor:

```bash
mkdir -p ~/pilla_pilla_ws/src/pilla_pilla/launch
```

Guarda este código en `~/pilla_pilla_ws/src/pilla_pilla/launch/juego.launch.py`:

```python
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    simulador = Node(
        package='turtlesim',
        executable='turtlesim_node',
        output='screen',
    )

    crear_tortuga = ExecuteProcess(
        cmd=[
            'ros2', 'service', 'call',
            '/spawn', 'turtlesim/srv/Spawn',
            "{x: 1.0, y: 1.0, theta: 0.0, name: 'turtle2'}",
        ],
        output='screen',
    )

    seguidor = Node(
        package='pilla_pilla',
        executable='seguidor',
        output='screen',
    )

    return LaunchDescription([
        simulador,
        crear_tortuga,
        seguidor,
    ])
```

Aquí `Node` es una herramienta de `launch_ros` que describe un programa que se va a iniciar. La utilizas tal como la proporciona ROS; no defines clases ni necesitas aprender herencia.

El comando `ros2 service call` espera a que exista `/spawn`. El seguidor no calcula movimiento hasta recibir ambas posiciones. Así no hace falta añadir una espera fija de varios segundos.

### Dependencias de ejecución

En `package.xml`, añade estas dos líneas dentro de `<package>`, antes de `<export>`, si no están ya presentes:

```xml
<exec_depend>launch</exec_depend>
<exec_depend>launch_ros</exec_depend>
```

### Instalar el launch

En la lista `data_files` de `setup.py`, añade esta entrada junto a las que ya existen:

```python
('share/pilla_pilla/launch', ['launch/juego.launch.py']),
```

Por ejemplo, la lista completa quedaría así:

```python
data_files=[
    ('share/ament_index/resource_index/packages',
     ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    ('share/pilla_pilla/launch', ['launch/juego.launch.py']),
],
```

Mantén también la entrada de `seguidor` en `console_scripts`. Reconstruye y carga la instalación:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/pilla_pilla_ws
colcon build --symlink-install --packages-select pilla_pilla
source install/setup.bash
```

### Ejecutar con launch

Cierra primero los tres procesos de la prueba manual. En la terminal A:

```bash
ros2 launch pilla_pilla juego.launch.py
```

En la terminal B:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run turtlesim turtle_teleop_key
```

No ejecutes además el comando manual de creación: el launch ya crea la segunda tortuga. Mantén el foco en B para jugar. Ctrl+C en A cierra los programas iniciados por el launch; cierra también B.

## 6. Comprobar las conexiones

En otra terminal, prepara ROS y consulta:

```bash
source /opt/ros/jazzy/setup.bash
ros2 node info /seguidor
ros2 topic echo /turtle2/pose
```

El nodo debe tener dos suscriptores Pose (`/turtle1/pose` y `/turtle2/pose`) y un publicador Twist (`/turtle2/cmd_vel`), además de las interfaces habituales de ROS. Detén `echo` con Ctrl+C.

Si aparece «Package not found», comprueba el build y el `source` del workspace. Si aparece «No executable found», revisa `console_scripts` y reconstruye. Si no responde el teclado, activa su terminal. Si el seguidor espera sin moverse, confirma que ambas tortugas existen y publican sus posiciones.

## 7. Los demás extras

La captura, el tiempo de supervivencia, los parámetros, un creador Python y un juez separado se proponen como retos en la segunda parte del PDF. No forman parte de este programa mínimo. Añádelos de uno en uno después de comprobar el launch.
