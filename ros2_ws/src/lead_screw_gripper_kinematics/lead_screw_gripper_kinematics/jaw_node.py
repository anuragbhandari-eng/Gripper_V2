"""ROS node: turns a jaw-gap setting into positions for all nine gripper joints."""
import rclpy
from rclpy.executors import ExternalShutdownException
from rcl_interfaces.msg import FloatingPointRange, ParameterDescriptor, SetParametersResult
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64, Float64MultiArray

from lead_screw_gripper_kinematics.linkage import (
    GAP_MAX, GAP_MIN, JOINT_NAMES, THETA_EXPORT, crank_angle_from_joint, gap_from_crank_angle,
    joint_positions, joint_positions_from_crank)

RATE = 50.0  # Hz


class JawKinematics(Node):

    def __init__(self):
        super().__init__('jaw_kinematics')

        # Target jaw gap in metres (also settable with ros2 param set, range-checked)
        gap_range = FloatingPointRange(from_value=GAP_MIN, to_value=GAP_MAX, step=0.0005)
        self.declare_parameter(
            'jaw_gap', 0.030,
            ParameterDescriptor(description='Target jaw gap (m)', floating_point_range=[gap_range]))
        # Fastest the jaw gap may change. Default: the full 60.5 mm stroke in the predicted 0.7 s (Tr8x8 screw).
        self.declare_parameter('max_gap_speed', 0.0605 / 0.7)
        # False: publish /joint_states for RViz. True: command the Gazebo position controller.
        self.declare_parameter('use_controller', False)

        self.target = self.get_parameter('jaw_gap').value
        self.gap = gap_from_crank_angle(THETA_EXPORT)  # the robot starts in the export pose
        self.max_step = self.get_parameter('max_gap_speed').value / RATE
        self.add_on_set_parameters_callback(self.on_parameters)
        self.create_subscription(Float64, 'jaw_gap_command', self.on_command, 10)

        self.use_controller = self.get_parameter('use_controller').value
        self.measured = None
        if self.use_controller:
            self.publisher = self.create_publisher(
                Float64MultiArray, 'gripper_controller/commands', 10)
            self.create_subscription(JointState, 'joint_states', self.on_joint_states, 10)
        else:
            self.publisher = self.create_publisher(JointState, 'joint_states', 10)
        self.timer = self.create_timer(1.0 / RATE, self.update)

    def on_parameters(self, params):
        for p in params:
            if p.name == 'jaw_gap':
                self.target = p.value
        return SetParametersResult(successful=True)

    def on_command(self, msg):
        if not GAP_MIN <= msg.data <= GAP_MAX:
            self.get_logger().warn(
                f'Jaw gap {msg.data:.4f} m is outside {GAP_MIN}-{GAP_MAX} m, clamping it')
        self.target = min(max(msg.data, GAP_MIN), GAP_MAX)

    def on_joint_states(self, msg):
        self.measured = dict(zip(msg.name, msg.position))

    def update(self):
        # Move the gap toward the target, no faster than max_gap_speed
        step = max(-self.max_step, min(self.max_step, self.target - self.gap))
        self.gap += step
        joints = joint_positions(self.gap)

        if self.use_controller and self.measured:
            # In Gazebo only the upper bell crank is driven toward the target; its torque
            # limit sets the grip force. Every other joint follows the measured upper crank
            # angle, the way the real gripper ties them together: the parallelogram keeps
            # the fingers parallel, and the shared carriage mirrors the lower side.
            # Without this, the joints would act like nine separate motors: a blocked jaw
            # would let its finger twist, and the box could drift sideways between the jaws.
            follow = joint_positions_from_crank(
                crank_angle_from_joint('U', self.measured['bell_crank_U']))
            for name in JOINT_NAMES:
                if name != 'bell_crank_U':
                    joints[name] = follow[name]

        if self.use_controller:
            msg = Float64MultiArray()
            msg.data = [joints[name] for name in JOINT_NAMES]
        else:
            msg = JointState()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.name = list(JOINT_NAMES)
            msg.position = [joints[name] for name in JOINT_NAMES]
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = JawKinematics()
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
