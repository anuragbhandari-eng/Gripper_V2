"""The fake Pico module and the firmware tests are importable from the installed package."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def test_fake_pico_runs_the_firmware_logic():
    from lead_screw_gripper_bringup.fake_pico import FakePico
    fake = FakePico(start_gap=20.0, object_mm=None)
    assert fake.handle('?') == 'ID lsg 1'
    assert fake.handle('H') == 'OK'
    for _ in range(3000):
        fake.step(2)
    assert fake.handle('R').split()[-1] == '1'      # homed, idle
    assert fake.handle('G 30 30') == 'OK'
    for _ in range(3000):
        fake.step(2)
    assert abs(float(fake.handle('R').split()[1]) - 30.0) < 0.1
