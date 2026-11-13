"""Shared helpers for the launch tests: start the gripper launch file and talk to it from a test node."""
import os
import tempfile
import time

import rclpy
from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_share_directory
from control_msgs.action import ParallelGripperCommand
from controller_manager_msgs.srv import ListHardwareComponents
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from rclpy.action import ActionClient
from sensor_msgs.msg import JointState


def gripper_launch(**args):
    path = os.path.join(get_package_share_directory('lead_screw_gripper_bringup'), 'launch', 'hardware.launch.py')
    args.setdefault('rviz', 'false')
    return IncludeLaunchDescription(PythonLaunchDescriptionSource(path), launch_arguments=args.items())


def temp_link():
    """A fresh path for the fake serial port, so tests never clash with a running gripper."""
    return os.path.join(tempfile.mkdtemp(prefix='lsg_test_'), 'fake_pico')


class Client:

    def __init__(self):
        self.node = rclpy.create_node('gripper_test_client')
        self.action = ActionClient(self.node, ParallelGripperCommand, '/gripper_controller/gripper_cmd')
        self.joint_states = {}
        self.node.create_subscription(JointState, '/joint_states', self._on_js, 10)

    def _on_js(self, msg):
        for n, p in zip(msg.name, msg.position):
            self.joint_states[n] = p

    def spin_until(self, predicate, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if predicate():
                return True
        return False

    def wait_for_server(self, timeout=60.0):
        return self.spin_until(lambda: self.action.server_is_ready(), timeout)

    def send(self, gap_m, effort=30.0, timeout=30.0):
        """Send one gripper goal. Returns (status, result) or (None, None) on timeout."""
        goal = ParallelGripperCommand.Goal()
        goal.command.name = ['jaw_gap']
        goal.command.position = [gap_m]
        goal.command.effort = [effort]
        fut = self.action.send_goal_async(goal)
        if not self.spin_until(fut.done, 10.0) or not fut.result().accepted:
            return None, None
        res = fut.result().get_result_async()
        if not self.spin_until(res.done, timeout):
            return None, None
        return res.result().status, res.result().result

    def hardware_state(self, timeout=10.0):
        """Lifecycle state label of the gripper's hardware component ('active', 'unconfigured', ...)."""
        cli = self.node.create_client(ListHardwareComponents, '/controller_manager/list_hardware_components')
        if not self.spin_until(cli.service_is_ready, timeout):
            return None
        fut = cli.call_async(ListHardwareComponents.Request())
        if not self.spin_until(fut.done, timeout):
            return None
        for c in fut.result().component:
            if c.name == 'LeadScrewGripper':
                return c.state.label
        return None

    def destroy(self):
        self.node.destroy_node()


SUCCEEDED = GoalStatus.STATUS_SUCCEEDED
