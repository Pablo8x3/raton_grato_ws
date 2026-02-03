import rclpy
from rclpy.node import Node
from turtlesim.srv import Spawn
import time

class SpawnerNode(Node):
    def __init__(self):
        super().__init__('spawner')
        self.client = self.create_client(Spawn, '/turtlesim/spawn')
        self.future = None
        self.spawned = False
        
        # Wait for service - more robust waiting
        max_wait_time = 10.0
        start_time = time.time()
        while not self.client.wait_for_service(timeout_sec=1.0):
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                self.get_logger().error(f'Service not available after {max_wait_time}s - giving up!')
                rclpy.shutdown()
                return
            self.get_logger().info(f'Waiting for /turtlesim/spawn service... ({elapsed:.1f}s/{max_wait_time}s)')
        
        self.get_logger().info('✓ Service /turtlesim/spawn is available!')
        self.spawn_turtle()

    def spawn_turtle(self):
        # Call service
        request = Spawn.Request()
        request.x = 1.0
        request.y = 2.0
        request.theta = 0.0
        request.name = 'turtle2'
        
        self.get_logger().info('Calling /turtlesim/spawn service...')
        self.future = self.client.call_async(request)
        self.future.add_done_callback(self.callback)

    def callback(self, future):
        try:
            response = future.result()
            self.get_logger().info(f'✓ Turtle spawned successfully: {response.name}')
            self.spawned = True
        except Exception as e:
            self.get_logger().error(f'✗ Service call failed: {e}')
        finally:
            # Shutdown after callback completes
            self.get_logger().info('Spawner done - shutting down')
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = SpawnerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()