"""A wrong serial port must fail with a clear message, not hang.

ros2_control's controller manager is built to exit when a hardware component cannot be activated at
start-up ("Failed to set the initial state ... to active"). So the expected behaviour is: our plugin
explains the problem, then ros2_control_node stops.
"""
import os
import sys
import unittest

import launch
import launch_testing
import launch_testing.actions
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hw_test_utils import gripper_launch  # noqa: E402


@pytest.mark.launch_test
def generate_test_description():
    return launch.LaunchDescription([
        gripper_launch(port='/tmp/lsg_no_such_port'),
        launch_testing.actions.ReadyToTest(),
    ])


class TestWrongPort(unittest.TestCase):

    def test_clear_error_then_stop(self, proc_output):
        proc_output.assertWaitFor(
            'cannot open /tmp/lsg_no_such_port: No such file or directory. Is the gripper plugged in', timeout=20)
        proc_output.assertWaitFor('Failed to set the initial state of the component : LeadScrewGripper',
                                  timeout=10)
