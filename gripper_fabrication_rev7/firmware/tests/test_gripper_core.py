"""Tests for gripper_core.py against the simulated hardware in hal_sim.py. No ROS, no Pico needed.

Run from the firmware folder:
    python3 -m pytest -q tests
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import gripper_core as core  # noqa: E402
from hal_sim import SimHal  # noqa: E402

CFG = {'dir_close': 1, 'enc_sign': 1, 'tips': 'narrow', 'checked': True}


def make(start_gap=30.0, object_mm=None, tips='narrow', enc_sign=1, checked=True):
    hal = SimHal(start_gap=start_gap, tips=tips, object_mm=object_mm, enc_sign=enc_sign)
    cfg = dict(CFG, tips=tips, enc_sign=enc_sign, checked=checked)
    c = core.GripperCore(hal, cfg)
    return hal, c


def run(hal, c, ms, until=None):
    """Advance simulated time in 2 ms slices, calling poll() each slice, like the real main loop."""
    for _ in range(int(ms / 2)):
        hal.advance(2)
        c.poll()
        if until is not None and until():
            return True
    return until is None


def status(c):
    _, gap, vel, amps, flags = c.status_line().split()
    return (None if gap == 'nan' else float(gap)), float(vel), float(amps), int(flags)


def home(hal, c):
    assert c.handle_line('H') == 'OK'
    assert run(hal, c, 10000, until=lambda: c.flags() & core.F_HOMED)


# ---------- protocol ----------

def test_identify():
    _, c = make()
    assert c.handle_line('?') == 'ID lsg 1'


def test_status_before_homing_has_no_gap():
    hal, c = make()
    run(hal, c, 200)
    gap, vel, _, flags = status(c)
    assert gap is None and vel == 0.0
    assert not flags & core.F_HOMED


@pytest.mark.parametrize('line, reply', [
    ('', 'ERR bad_command'),
    ('Q', 'ERR bad_command'),
    ('R 1', 'ERR bad_command'),
    ('G 10', 'ERR bad_command'),
    ('G ten 30', 'ERR bad_value'),
    ('G nan 30', 'ERR bad_value'),
    ('G 10 inf', 'ERR bad_value'),
    ('G 10 0', 'ERR bad_value'),
    ('G 10 -5', 'ERR bad_value'),
    ('G ' + '1' * 70 + ' 30', 'ERR line_too_long'),
])
def test_bad_lines(line, reply):
    _, c = make()
    assert c.handle_line(line) == reply


def test_move_before_homing_is_refused():
    _, c = make()
    assert c.handle_line('G 40 30') == 'ERR not_homed'


def test_refuses_to_move_until_bench_tests_pass():
    _, c = make(checked=False)
    assert c.handle_line('H') == 'ERR not_checked'


# ---------- homing ----------

def test_homing_stops_at_closed_point():
    hal, c = make(start_gap=35.0)
    home(hal, c)
    gap, _, amps, flags = status(c)
    assert gap == pytest.approx(0.0, abs=0.05)
    assert hal.gap() == pytest.approx(0.0, abs=0.01)
    assert amps == pytest.approx(core.HOME_A)
    assert flags & core.F_HOMED and not flags & core.F_MOVING


def test_homing_with_wide_tips_stops_at_motor_wall():
    hal, c = make(start_gap=35.0, tips='wide')
    home(hal, c)
    assert hal.true_pos == pytest.approx(core.HOME_POS['wide'])
    assert c._pos_now() == pytest.approx(core.HOME_POS['wide'], abs=1)


def test_homing_works_with_reversed_encoder():
    hal, c = make(start_gap=20.0, enc_sign=-1)
    home(hal, c)
    assert c.handle_line('G 40 30') == 'OK'
    run(hal, c, 8000, until=lambda: c.state == 'idle')
    assert hal.gap() == pytest.approx(40.0, abs=0.1)


def test_command_during_homing_is_refused():
    hal, c = make()
    c.handle_line('H')
    run(hal, c, 50)
    # Not homed yet, so the move is refused
    assert c.handle_line('G 40 30') == 'ERR not_homed'


# ---------- moves ----------

def test_move_reaches_target():
    hal, c = make()
    home(hal, c)
    assert c.handle_line('G 40 30') == 'OK'
    assert run(hal, c, 10000, until=lambda: c.state == 'idle')
    gap, vel, _, flags = status(c)
    assert gap == pytest.approx(40.0, abs=0.1)
    assert hal.gap() == pytest.approx(40.0, abs=0.1)
    assert not flags & core.F_MOVING and not flags & core.F_STALLED
    run(hal, c, 200)
    assert status(c)[1] == 0.0          # stopped means zero speed


def test_speed_is_reported_while_moving_and_respects_limits():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 55 30')
    speeds = []
    for _ in range(1000):
        hal.advance(2)
        c.poll()
        speeds.append(status(c)[1])
    # The gap moves faster than the carriage: up to ~2.8 mm of gap per mm of carriage near closed
    t = core.GAP_TABLE
    ratio = max((t[i + 1][0] - t[i][0]) / ((t[i][1] - t[i + 1][1]) / core.STEPS_PER_MM) for i in range(len(t) - 1))
    assert max(speeds) > 15                         # opening, gap rising
    assert max(speeds) <= core.MOVE_MM_S * ratio * 1.05


def test_closing_is_slow():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 50 30')
    run(hal, c, 10000, until=lambda: c.state == 'idle')
    c.handle_line('G 10 30')
    p0 = hal.true_pos
    run(hal, c, 1000)
    mm_per_s = (hal.true_pos - p0) / core.STEPS_PER_MM
    assert 0 < mm_per_s <= core.GRIP_MM_S + 0.5


def test_retarget_mid_move_same_direction():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 50 30')
    run(hal, c, 300)
    assert c.state == 'moving'
    assert c.handle_line('G 30 30') == 'OK'
    assert run(hal, c, 10000, until=lambda: c.state == 'idle')
    assert hal.gap() == pytest.approx(30.0, abs=0.1)


def test_retarget_mid_move_reverses():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 20 30')
    run(hal, c, 10000, until=lambda: c.state == 'idle')
    c.handle_line('G 50 30')
    run(hal, c, 400)
    assert 20 < hal.gap() < 50
    assert c.handle_line('G 10 30') == 'OK'
    assert run(hal, c, 15000, until=lambda: c.state == 'idle')
    assert hal.gap() == pytest.approx(10.0, abs=0.1)


def test_gap_is_clamped_to_firmware_limits():
    hal, c = make()
    home(hal, c)
    assert c.handle_line('G 75 30') == 'OK'
    run(hal, c, 10000, until=lambda: c.state == 'idle')
    assert hal.gap() == pytest.approx(core.GAP_MAX, abs=0.1)


def test_close_to_zero_stops_short_of_closed_stop():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 30 30')
    run(hal, c, 10000, until=lambda: c.state == 'idle')
    c.handle_line('G 0 30')
    run(hal, c, 15000, until=lambda: c.state != 'moving')
    assert c.state == 'idle'
    assert hal.true_pos == pytest.approx(core.HOME_POS['narrow'] - core.CLOSE_MARGIN, abs=2)
    assert not c.stalled


def test_stop_command_stops_and_keeps_holding():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 50 30')
    run(hal, c, 300)
    assert c.handle_line('X') == 'OK'
    p = hal.true_pos
    run(hal, c, 500)
    assert hal.true_pos == p
    assert hal.enabled
    assert not c.flags() & core.F_MOVING


def test_driver_off_command():
    hal, c = make()
    home(hal, c)
    assert c.handle_line('O') == 'OK'
    assert not hal.enabled
    assert status(c)[2] == 0.0


# ---------- gripping an object ----------

def test_closing_on_object_stalls_and_holds():
    hal, c = make(object_mm=30.0)
    hal.object_mm = None                 # home with nothing in the way
    home(hal, c)
    c.handle_line('G 50 30')
    run(hal, c, 10000, until=lambda: c.state == 'idle')
    hal.object_mm = 30.0                 # now put a 30 mm object between the jaws
    assert c.handle_line('G 0 30') == 'OK'
    assert run(hal, c, 15000, until=lambda: c.state == 'holding')
    gap, vel, amps, flags = status(c)
    assert gap == pytest.approx(30.0, abs=0.5)
    assert flags & core.F_STALLED and not flags & core.F_MOVING
    assert hal.enabled                   # current stays on: the screw back-drives without it
    assert amps == pytest.approx(core.current_for(30.0, 30.0), abs=0.01)
    run(hal, c, 500)
    assert status(c)[1] == 0.0


def test_new_open_command_releases_a_held_object():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 50 30')
    run(hal, c, 10000, until=lambda: c.state == 'idle')
    hal.object_mm = 25.0
    c.handle_line('G 0 30')
    run(hal, c, 15000, until=lambda: c.state == 'holding')
    hal.object_mm = None
    assert c.handle_line('G 45 30') == 'OK'
    assert not c.flags() & core.F_STALLED
    run(hal, c, 10000, until=lambda: c.state == 'idle')
    assert hal.gap() == pytest.approx(45.0, abs=0.1)


# ---------- current (force) ----------

@pytest.mark.parametrize('gap, force', [(0, 30), (30, 30), (60, 30), (10, 5), (50, 100), (0, 1000)])
def test_current_rule(gap, force):
    a = core.current_for(gap, force)
    assert core.I_MIN <= a <= core.I_FULL
    expected = core.lerp(gap, core.CURRENT_TABLE) * force / core.FORCE_REF
    assert a == pytest.approx(max(core.I_MIN, min(core.I_FULL, expected)))


def test_current_never_exceeds_ceiling_in_use():
    hal, c = make()
    home(hal, c)
    for line in ('G 55 500', 'G 5 500', 'G 30 1', 'G 60 30'):
        c.handle_line(line)
        run(hal, c, 15000, until=lambda: c.state != 'moving')
    assert hal.max_amps <= core.I_FULL + 1e-9


def test_lower_force_gives_lower_current():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 50 30')
    run(hal, c, 10000, until=lambda: c.state == 'idle')
    hal.object_mm = 30.0
    c.handle_line('G 0 10')
    run(hal, c, 15000, until=lambda: c.state == 'holding')
    assert status(c)[2] == pytest.approx(core.current_for(30.0, 10.0), abs=0.01)


# ---------- faults ----------

def test_power_loss_stops_and_forgets_position():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 50 30')
    run(hal, c, 300)
    hal.volts = 0.0
    run(hal, c, 300)
    _, _, amps, flags = status(c)
    assert flags & core.F_NO_POWER
    assert not flags & core.F_HOMED and not flags & core.F_MOVING
    assert not hal.enabled and amps == 0.0
    assert c.handle_line('G 40 30') == 'ERR not_homed'
    assert c.handle_line('H') == 'ERR fault'
    hal.volts = 9.0
    run(hal, c, 300)
    assert not c.flags() & core.F_NO_POWER
    home(hal, c)                          # works again once power is back


def test_silent_driver_is_a_fault():
    hal, c = make()
    home(hal, c)
    hal.driver = 'silent'
    run(hal, c, 300)
    assert c.flags() & core.F_DRIVER
    assert not c.flags() & core.F_HOMED


def test_driver_reset_forgets_position():
    hal, c = make()
    home(hal, c)
    hal.driver = 'reset'
    run(hal, c, 300)
    flags = c.flags()
    assert not flags & core.F_HOMED
    assert not flags & core.F_DRIVER       # it answers again; it only needs homing
    home(hal, c)


def test_encoder_not_answering_is_a_fault():
    hal, c = make()
    home(hal, c)
    c.handle_line('G 50 30')
    run(hal, c, 200)
    hal.encoder_ok = False
    run(hal, c, 100)
    flags = c.flags()
    assert flags & core.F_ENCODER and not flags & core.F_HOMED
    assert not hal.enabled
    hal.encoder_ok = True
    run(hal, c, 100)
    assert not c.flags() & core.F_ENCODER


def test_homing_gives_up_if_jaws_never_stop():
    hal, c = make()
    hal.closed_pos = 10 ** 9             # pretend nothing ever stops the carriage
    c.handle_line('H')
    run(hal, c, 20000, until=lambda: c.state == 'idle')
    assert c.state == 'idle'
    assert not c.flags() & core.F_HOMED
    assert c.last_error == 'home_failed'
