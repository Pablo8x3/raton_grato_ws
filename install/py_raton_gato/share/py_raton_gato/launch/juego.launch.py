from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():

    config_file = PathJoinSubstitution([
        FindPackageShare('py_raton_gato'),
        'config',
        'juego.yaml'
    ])


    turtlesim_node = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim'
    )

    spawn_gato = ExecuteProcess(
        cmd=[
            'ros2', 'service', 'call',
            '/spawn',
            'turtlesim/srv/Spawn',
            "{x: 1, y: 2, theta: 0.0, name: 'turtle2'}"
        ],
        output='screen'
    )

    raton_node = Node(
        package='py_raton_gato',
        executable='raton',
        name='raton',
        parameters=[config_file]
    )

    gato_node = Node(
        package='py_raton_gato',
        executable='gato',
        name='gato',
        parameters=[config_file]
    )

    juez_node = Node(
        package='py_raton_gato',
        executable='juez',
        name='juez',
        parameters=[config_file]
    )

    return LaunchDescription([
        turtlesim_node,
        spawn_gato,
        raton_node,
        gato_node,
        juez_node
    ])
