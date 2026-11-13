"""Scripted grasp test for Gazebo: open, close on the box, lift it, hold, set it down, open."""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float64, Float64MultiArray

RATE = 50.0         # Hz
LIFT_SPEED = 0.05   # m/s
LIFT_HEIGHT = 0.05  # m

# (what happens, jaw gap target in m, lift target in m, seconds to wait afterwards)
STEPS = [
    ('Opening the jaws', 0.050, 0.0, 2.0),
    ('Closing on the 30 mm box (target 20 mm, so the jaws squeeze)', 0.020, 0.0, 2.5),
    ('Lifting 50 mm', 0.020, LIFT_HEIGHT, 3.0),
    ('Holding', 0.020, LIFT_HEIGHT, 3.0),
    ('Setting the box down', 0.020, 0.0, 2.0),
    ('Opening the jaws', 0.050, 0.0, 2.0),
]


class GraspDemo(Node):

    def __init__(self):
        super().__init__('grasp_demo')
        self.declare_parameter('start_delay', 3.0)  # s of sim time for the controllers to start
        self.gap_pub = self.create_publisher(Float64, 'jaw_gap_command', 10)
        self.lift_pub = self.create_publisher(Float64MultiArray, 'lift_controller/commands', 10)
        self.lift = 0.0
        self.step = -1
        self.next_time = self.now() + self.get_parameter('start_delay').value
        self.create_timer(1.0 / RATE, self.update)

    def now(self):
        return self.get_clock().now().nanoseconds / 1e9

    def update(self):
        if self.step >= len(STEPS):
            return
        if self.step >= 0:
            # Ramp the lift toward its target at LIFT_SPEED, and keep sending the jaw target
            _, gap, lift_target, _ = STEPS[self.step]
            limit = LIFT_SPEED / RATE
            self.lift += max(-limit, min(limit, lift_target - self.lift))
            self.lift_pub.publish(Float64MultiArray(data=[self.lift]))
            self.gap_pub.publish(Float64(data=gap))
        if self.now() >= self.next_time:
            self.step += 1
            if self.step < len(STEPS):
                text, gap, lift_target, wait = STEPS[self.step]
                self.get_logger().info(f'{text}: jaw gap {gap * 1000:.0f} mm, lift {lift_target * 1000:.0f} mm')
                self.next_time = self.now() + wait
            else:
                self.get_logger().info('Grasp demo finished')


def main():
    rclpy.init()
    node = GraspDemo()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # Ctrl+C or the launch shutting down
    except Exception:
        # Ctrl+C can also land while ROS is mid-cycle, which raises a low-level error once
        # ROS has shut down. That is a normal exit too; any other error is a real one.
        if rclpy.ok():
            raise
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
