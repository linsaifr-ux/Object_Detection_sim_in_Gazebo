import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math
import time


class FlightControllerNode(Node):
    """Flies the drone in a slow circle at fixed altitude for scene coverage."""

    def __init__(self):
        super().__init__('flight_controller')

        self.declare_parameter('altitude', 5.0)
        self.declare_parameter('circle_radius', 4.0)
        self.declare_parameter('angular_speed', 0.3)

        self.altitude = self.get_parameter('altitude').value
        self.radius = self.get_parameter('circle_radius').value
        self.omega = self.get_parameter('angular_speed').value

        self.pub = self.create_publisher(Twist, '/iris/cmd_vel', 10)

        self.start_time = time.time()
        self.armed = False

        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info(
            f'Flight controller: altitude={self.altitude}m, radius={self.radius}m'
        )

    def control_loop(self):
        elapsed = time.time() - self.start_time
        msg = Twist()

        if elapsed < 3.0:
            # Takeoff phase: climb to altitude
            msg.linear.z = min(2.0, self.altitude * 0.5)
        else:
            # Circle phase
            t = elapsed - 3.0
            vx = -self.radius * self.omega * math.sin(self.omega * t)
            vy = self.radius * self.omega * math.cos(self.omega * t)
            msg.linear.x = vx
            msg.linear.y = vy
            msg.linear.z = 0.0
            msg.angular.z = self.omega

        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = FlightControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
