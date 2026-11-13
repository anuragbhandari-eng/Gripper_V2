"""End-to-end test with no hardware: action goal -> parallel-gripper controller -> hardware interface ->
serial (pseudo-terminal) -> the real firmware logic on a fake Pico -> state back -> /joint_states.

Run with:  colcon test --packages-select lead_screw_gripper_bringup --event-handlers console_direct+
"""
import os
import signal
import sys
import time
import unittest

import launch
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import psutil
import pytest
import rclpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hw_test_utils import Client, SUCCEEDED, gripper_launch, temp_link  # noqa: E402

LINK = temp_link()


@pytest.mark.launch_test
def generate_test_description():
    return launch.LaunchDescription([
        gripper_launch(fake='true', fake_link=LINK, object_mm='30'),
        launch_testing.actions.ReadyToTest(),
    ])


class TestFakePico(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.client = Client()
        assert cls.client.wait_for_server(60.0), 'gripper action server never appeared'

    @classmethod
    def tearDownClass(cls):
        cls.client.destroy()
        rclpy.shutdown()

    def test_1_open_reaches_goal(self):
        status, result = self.client.send(0.045)
        self.assertEqual(status, SUCCEEDED)
        self.assertTrue(result.reached_goal)
        self.assertFalse(result.stalled)
        # The controller stops waiting within its 1 mm tolerance; the firmware finishes the last part
        self.client.spin_until(lambda: abs(self.client.joint_states.get('jaw_gap', 0) - 0.045) < 1e-4, 5.0)
        self.assertAlmostEqual(self.client.joint_states['jaw_gap'], 0.045, delta=1e-4)

    def test_2_close_on_object_stalls(self):
        # The fake Pico placed a 30 mm object once the jaws opened past 31 mm
        status, result = self.client.send(0.0, effort=25.0)
        self.assertEqual(status, SUCCEEDED)       # allow_stalling: a held object is a success
        self.assertTrue(result.stalled)
        self.assertFalse(result.reached_goal)
        self.assertAlmostEqual(result.state.position[0], 0.030, delta=0.0005)

    def test_3_linkage_joints_published(self):
        names = ('bell_crank_U', 'front_crank_U', 'finger_U', 'conrod_U',
                 'bell_crank_L', 'front_crank_L', 'finger_L', 'conrod_L', 'carriage')
        self.client.joint_states.clear()
        self.assertTrue(self.client.spin_until(
            lambda: all(n in self.client.joint_states for n in names + ('jaw_gap',)), 5.0))

    def test_4_losing_the_pico_is_an_error_not_a_crash(self):
        fakes = [p for p in psutil.process_iter(['cmdline'])
                 if p.info['cmdline'] and any('fake_pico' in a for a in p.info['cmdline'])
                 and LINK in p.info['cmdline']]
        self.assertEqual(len(fakes), 1)
        fakes[0].send_signal(signal.SIGKILL)       # like pulling the USB cable
        time.sleep(2.0)
        self.assertNotEqual(self.client.hardware_state(), 'active')
        cms = [p for p in psutil.process_iter(['cmdline'])
               if p.info['cmdline'] and any('ros2_control_node' in a for a in p.info['cmdline'])]
        self.assertTrue(cms and all(p.is_running() and p.status() != psutil.STATUS_ZOMBIE for p in cms))


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_processes_exit(self, proc_info):
        # fake_pico was killed on purpose in test 4; the others must shut down by themselves
        for info in proc_info:
            if 'fake_pico' not in info.process_name:
                self.assertIn(info.returncode, (0, -2, -15, 130), info.process_name)
