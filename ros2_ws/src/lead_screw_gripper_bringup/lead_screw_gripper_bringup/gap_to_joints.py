"""ROS node: turns the jaw_gap joint state into positions for the nine linkage joints, for RViz.

ros2_control only knows one joint, jaw_gap. The real linkage has nine joints whose angles are nonlinear
functions of the gap, so URDF "mimic" joints cannot describe them. This node listens to /joint_states and,
whenever a message contains jaw_gap, publishes the nine joint positions with the same time stamp
(using the same linkage.py as the RViz and Gazebo work). robot_state_publisher then moves every part.
"""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import JointState

from lead_screw_gripper_kinematics.linkage import GAP_MAX, GAP_MIN, JOINT_NAMES, joint_positions


class GapToJoints(Node):

    def __init__(self):
        super().__init__('gap_to_joints')
        self.pub = self.create_publisher(JointState, 'joint_states', 10)
        self.create_subscription(JointState, 'joint_states', self.on_joint_states, 10)

    def on_joint_states(self, msg):
        if 'jaw_gap' not in msg.name:
            return                        # includes our own messages, so this node never reacts to itself
        gap = msg.position[msg.name.index('jaw_gap')]
        if gap != gap:                    # NaN: no position yet
            return
        joints = joint_positions(min(max(gap, GAP_MIN), GAP_MAX))
        out = JointState()
        out.header.stamp = msg.header.stamp
        out.name = list(JOINT_NAMES)
        out.position = [joints[n] for n in JOINT_NAMES]
        self.pub.publish(out)


def main():
    rclpy.init()
    node = GapToJoints()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
