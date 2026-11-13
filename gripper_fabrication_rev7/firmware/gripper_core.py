# Gripper logic for the ROS 2 firmware: the serial protocol and the motion state machine.
#
# There is no hardware code in this file. Everything that touches a pin, the TMC2209 driver or the AS5600 encoder
# goes through a `hal` object (hardware abstraction layer):
#   - on the Pico, hal_pico.py talks to the real parts;
#   - on the laptop, hal_sim.py simulates the motor, the screw, the encoder and an object between the jaws.
# So the exact same logic is tested on the laptop and then runs on the Pico. It must run on MicroPython and on
# normal Python: no f-strings, no dataclasses, no typing.
#
# How it is used (ros_main.py on the Pico, fake_pico on the laptop):
#     core = GripperCore(hal, cfg)
#     reply = core.handle_line('G 40 30')   # one command line in, one reply line out
#     core.poll()                            # call as often as possible: does one small, non-blocking piece of work
#
# Positions: `pos` counts microsteps from the open hard stop, bigger = more closed (same as bench.py).
# Gaps on the serial line are always the linkage gap in mm, which equals the narrow-tip pad gap (0 to 60 mm).
# With the wide tips fitted, the real pad gap is 20 mm more; ROS works in the linkage gap either way.

import math

PROTOCOL = 1

# ---- drive: Tr8x8 screw, 1/16 microstep (numbers copied from bench.py) ----
STEPS_PER_MM = 400                       # microsteps per mm of carriage travel
ENC_PER_MM = 4096 / 8                    # AS5600 counts per mm of carriage travel (one screw turn = 8 mm)
I_FULL = 0.70                            # A RMS: the VREF ceiling; software can only go lower
I_MIN = 0.15                             # lowest current the force rule will ask for
V_MIN = 7.0                              # below this the 9 V supply is gone: driver off
MAX_MM_S = 40                            # 300 rpm, the most the 9 V supply drives at full current
MOVE_MM_S = 20                           # opening moves
GRIP_MM_S = 10                           # closing moves: slow, because an object may stop the jaws at any point
HOME_MM_S, HOME_A = 10, 0.30             # homing: close slowly at low current until the jaws stop
START_MM_S = 2                           # every move starts and ends at this speed
ACCEL = 300                              # mm/s^2
CHUNK = 100                              # microsteps per motion segment (0.25 mm)
STALL_FRACTION = 0.3                     # a segment that moved less than 30% of its steps means the jaws are stopped
HOME_MAX_MM = 40                         # give up homing after this much travel without a stop
CLOSE_MARGIN = STEPS_PER_MM // 2         # moves end 0.5 mm before the closed point; only an object or homing stops them
GAP_MAX = 60.0                           # firmware cap on the opening (mm); the open hard stop is at 60.5
FORCE_REF = 30.0                         # N per jaw that CURRENT_TABLE is computed for
CHECK_MS = 100                           # how often to check motor power and the driver
SETTLE_STEPS = 20                        # a move is done within 0.05 mm of its target

# Jaw gap (mm) <-> steps from the open stop (DESIGN_REPORT.md section 3)
GAP_TABLE = [(0, 10619), (6, 9773), (12, 8900), (18, 8004), (24, 7085), (30, 6138),
             (36, 5153), (42, 4114), (48, 2989), (54, 1716), (60, 153), (60.5, 0)]
POS_TABLE = sorted((s, g) for g, s in GAP_TABLE)
# Where homing stops: narrow tips when the pads meet, wide tips when the carriage reaches the motor wall
HOME_POS = {'narrow': 10619, 'wide': 10619 + STEPS_PER_MM}
# Run current against gap for about 30 N per jaw (DESIGN_REPORT.md section 4a; predicted, never measured)
CURRENT_TABLE = [(0, 0.70), (20, 0.70), (30, 0.69), (40, 0.64), (50, 0.54), (60, 0.37)]

# Status flags in the `S` reply (added together)
F_HOMED, F_MOVING, F_STALLED, F_NO_POWER, F_DRIVER, F_ENCODER, F_HOMING = 1, 2, 4, 8, 16, 32, 64
MAX_LINE = 64


def lerp(x, pts):
    """Straight-line interpolation in a sorted (x, y) table; extends the end segments past the table."""
    i = 1
    while i < len(pts) - 1 and x > pts[i][0]:
        i += 1
    (x0, y0), (x1, y1) = pts[i - 1], pts[i]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def gap_from_pos(pos):
    return lerp(pos, POS_TABLE)


def pos_from_gap(gap):
    return lerp(gap, GAP_TABLE)


def current_for(gap, force):
    """Motor current for a grip force (N per jaw) at a gap, from the 30 N table, kept between I_MIN and I_FULL."""
    g = max(0.0, min(60.0, gap))
    return max(I_MIN, min(I_FULL, lerp(g, CURRENT_TABLE) * force / FORCE_REF))


def _finite(x):
    return x == x and x not in (float('inf'), float('-inf'))


class GripperCore:

    def __init__(self, hal, cfg):
        self.hal = hal
        self.cfg = cfg                   # dir_close, enc_sign, tips, checked (bench_cfg.json)
        self.pos = None                  # microsteps from the open stop; None until homed
        self.state = 'idle'              # idle, homing, moving, holding
        self.faults = 0                  # F_NO_POWER, F_DRIVER, F_ENCODER while they last
        self.stalled = False
        self.amps = 0.0
        self.target = None               # target position (microsteps) of the current move
        self.force = FORCE_REF
        self.dir = 0                     # +1 closing, -1 opening, 0 not moving
        self.v_last = 0.0                # speed of the last segment sent (mm/s)
        self.pending = []                # sizes of the segments sent to the step generator, oldest first
        self.home_left = 0               # homing: microsteps still allowed before giving up
        self.enc_total = 0               # encoder counts including whole turns
        self.enc_last = None
        self.enc_seg = 0                 # encoder count when the last segment finished
        self.enc_ref = 0                 # encoder count that matches self.pos_ref
        self.pos_ref = None
        self.vel = 0.0                   # gap speed (mm/s), smoothed
        self.vel_t = hal.ticks_ms()
        self.vel_gap = None
        self.check_t = hal.ticks_ms() - CHECK_MS
        self.driver_ready = False
        self.last_error = ''

    # ---------- position from the encoder ----------
    def _read_encoder(self):
        """Update enc_total from the 12-bit angle. Must be called at least every half screw turn (4 mm)."""
        a = self.hal.encoder_raw()       # raises OSError if the encoder does not answer
        if self.enc_last is not None:
            d = (a - self.enc_last) & 0x0FFF
            self.enc_total += d - 4096 if d >= 2048 else d
        self.enc_last = a
        return self.enc_total

    def _pos_now(self):
        """Carriage position in microsteps, from the encoder (None until homed)."""
        if self.pos_ref is None:
            return None
        moved = self.cfg['enc_sign'] * (self.enc_total - self.enc_ref)
        return self.pos_ref + moved * STEPS_PER_MM / ENC_PER_MM

    def gap(self):
        p = self._pos_now()
        return None if p is None else gap_from_pos(p)

    def _set_pos(self, pos):
        self.pos_ref, self.enc_ref = pos, self.enc_total

    def _unhome(self):
        self.pos_ref = None
        self.vel_gap = None

    # ---------- the serial protocol ----------
    def flags(self):
        f = self.faults
        if self.pos_ref is not None:
            f |= F_HOMED
        if self.state == 'moving':
            f |= F_MOVING
        if self.state == 'homing':
            f |= F_HOMING | F_MOVING
        if self.stalled:
            f |= F_STALLED
        return f

    def status_line(self):
        g = self.gap()
        gs = 'nan' if g is None else '%.3f' % g
        vs = '0.000' if g is None else '%.3f' % self.vel
        return 'S %s %s %.2f %d' % (gs, vs, self.amps, self.flags())

    def handle_line(self, line):
        """One command line in, one reply line out (no newline)."""
        if len(line) > MAX_LINE:
            return 'ERR line_too_long'
        parts = line.strip().split()
        if not parts:
            return 'ERR bad_command'
        cmd, args = parts[0], parts[1:]
        if cmd == '?' and not args:
            return 'ID lsg %d' % PROTOCOL
        if cmd == 'R' and not args:
            return self.status_line()
        if cmd == 'X' and not args:
            self._stop()
            return 'OK'
        if cmd == 'O' and not args:
            self._stop()
            self._driver_off()
            self.state = 'idle'
            self.stalled = False
            return 'OK'
        if cmd == 'H' and not args:
            return self._start_homing()
        if cmd == 'G' and len(args) == 2:
            try:
                gap, force = float(args[0]), float(args[1])
            except ValueError:
                return 'ERR bad_value'
            if not (_finite(gap) and _finite(force)) or force <= 0:
                return 'ERR bad_value'
            return self._start_move(gap, force)
        return 'ERR bad_command'

    # ---------- starting and stopping moves ----------
    def _can_move(self):
        if not self.cfg.get('checked'):
            return 'ERR not_checked'     # bench tests t1-t6 have not passed on this Pico
        if self.faults:
            return 'ERR fault'
        if not self._ensure_driver():
            return 'ERR fault'
        return None

    def _start_homing(self):
        err = self._can_move()
        if err:
            return err
        self._stop()
        self._unhome()
        self.stalled = False
        self.state = 'homing'
        self.home_left = HOME_MAX_MM * STEPS_PER_MM
        self._set_current(HOME_A)
        self.hal.enable(True)
        self._begin_motion(+1)
        return 'OK'

    def _start_move(self, gap, force):
        if self.pos_ref is None:
            return 'ERR not_homed'
        err = self._can_move()
        if err:
            return err
        if self.state == 'homing':
            return 'ERR busy'
        gap = max(0.0, min(GAP_MAX, gap))
        # Never drive into the closed stop: a move ends 0.5 mm before it unless an object stops the jaws first.
        self.target = min(pos_from_gap(gap), HOME_POS[self.cfg['tips']] - CLOSE_MARGIN)
        self.force = force
        self.stalled = False
        self.hal.enable(True)
        self._set_current(current_for(self.gap(), force))
        self.state = 'moving'
        return 'OK'

    def _stop(self):
        """Stop the step pulses now. The driver stays on, so the jaws keep their grip."""
        self.hal.stop()
        self.pending = []
        self.dir = 0
        self.v_last = 0.0
        if self.state in ('moving', 'homing'):
            self.state = 'idle'

    def _driver_off(self):
        self.hal.enable(False)
        self.amps = 0.0

    def _set_current(self, amps):
        amps = min(I_FULL, amps)
        if abs(amps - self.amps) > 0.005:
            self.hal.set_current(amps)
            self.amps = amps

    def _ensure_driver(self):
        if not self.driver_ready:
            self.driver_ready = self.hal.configure_driver(self.amps or HOME_A)
            if self.driver_ready:
                self.amps = self.amps or HOME_A
        return self.driver_ready

    def _begin_motion(self, direction):
        self.dir = direction
        self.v_last = 0.0
        self.enc_seg = self.enc_total

    # ---------- the main loop ----------
    def poll(self):
        """One short slice of work. Never waits."""
        now = self.hal.ticks_ms()
        if self.hal.ticks_diff(now, self.check_t) >= CHECK_MS:
            self.check_t = now
            self._check_health()
        try:
            self._read_encoder()
        except OSError:
            self._fault(F_ENCODER)
            return
        self.faults &= ~F_ENCODER
        self._update_speed(now)
        self._collect_finished_segments()
        if self.state == 'homing':
            self._step_homing()
        elif self.state == 'moving':
            self._step_moving()

    def _check_health(self):
        if self.hal.supply_volts() < V_MIN:
            self._fault(F_NO_POWER)
            return
        self.faults &= ~F_NO_POWER
        status = self.hal.driver_status()   # 'ok', 'reset' (it restarted: settings lost) or 'silent'
        if status == 'silent':
            self._fault(F_DRIVER)
            return
        self.faults &= ~F_DRIVER
        if status == 'reset':
            # The driver lost its settings, so it may have let go or slipped: position is no longer trusted.
            self.driver_ready = False
            self._stop()
            self._unhome()
            self._ensure_driver()

    def _fault(self, flag):
        """Something is wrong: stop, switch the driver off, and forget the position (home again later)."""
        if not self.faults & flag:
            self._stop()
            self._driver_off()
            self._unhome()
            self.driver_ready = False
            self.stalled = False
            self.state = 'idle'
        self.faults |= flag

    def _update_speed(self, now):
        dt = self.hal.ticks_diff(now, self.vel_t)
        if dt < 20:
            return
        g = self.gap()
        if g is None or self.vel_gap is None:
            self.vel = 0.0
        else:
            raw = (g - self.vel_gap) * 1000.0 / dt
            self.vel += 0.5 * (raw - self.vel)         # light smoothing
            if self.dir == 0 and abs(self.vel) < 0.05:
                self.vel = 0.0
        self.vel_gap, self.vel_t = g, now

    def _collect_finished_segments(self):
        """Check each finished segment against the encoder: did the carriage really move?"""
        for _ in range(self.hal.segments_done()):
            if not self.pending:
                break
            k = self.pending.pop(0)
            moved = self.cfg['enc_sign'] * (self.enc_total - self.enc_seg) * self.dir
            self.enc_seg = self.enc_total
            if moved < STALL_FRACTION * k * ENC_PER_MM / STEPS_PER_MM:
                self._on_stall()
                return

    def _on_stall(self):
        was = self.state
        self._stop()
        if was == 'homing':
            self._set_pos(HOME_POS[self.cfg['tips']])
            self.state = 'idle'
        else:
            self.stalled = True         # an object (or the closed stop) is stopping the jaws: keep the current on
            self.state = 'holding'

    def _send_segment(self, k, v_mm_s):
        self.hal.queue_segment(k, self.dir > 0, v_mm_s * STEPS_PER_MM)
        self.pending.append(k)
        self.v_last = v_mm_s

    def _next_speed(self, k, remaining, vmax):
        """Speed for the next segment: speed up from the last one, and leave room to slow down before the end."""
        d = k / STEPS_PER_MM
        v_up = math.sqrt(self.v_last ** 2 + 2 * ACCEL * d) if self.v_last else START_MM_S
        v_down = math.sqrt(START_MM_S ** 2 + 2 * ACCEL * max(0.0, remaining / STEPS_PER_MM - d / 2))
        return max(START_MM_S, min(vmax, v_up, v_down))

    def _step_homing(self):
        # Only one segment at a time, so the stall check can tell exactly which segment did not move.
        if self.pending:
            return
        if self.home_left <= 0:
            self._stop()
            self.last_error = 'home_failed'
            return
        k = min(CHUNK, self.home_left)
        self.home_left -= k
        self._send_segment(k, HOME_MM_S)

    def _step_moving(self):
        pos = self._pos_now()
        if pos is None:
            self._stop()
            return
        # Planned position = where the carriage will be when the segments already sent have finished.
        planned = pos + self.dir * sum(self.pending)
        delta = self.target - planned
        want = 1 if delta > 0 else -1
        if self.dir == 0:
            if abs(delta) < SETTLE_STEPS:
                self.state = 'idle'
                return
            self._begin_motion(want)
        elif want != self.dir or abs(delta) < 1:
            # Target reached, or it is now behind us: let the sent segments finish, then stop or turn around.
            if not self.pending:
                self.dir = 0
                self.v_last = 0.0
                if abs(self.target - pos) < SETTLE_STEPS:
                    self.state = 'idle'
            return
        # Closing segments go one at a time (exact stall check, slow speed); opening keeps up to 2 queued.
        closing = self.dir > 0
        if len(self.pending) >= (1 if closing else 2) or not self.hal.segment_room():
            return
        remaining = abs(delta)
        k = int(min(CHUNK, remaining))
        if k < 1:
            return
        vmax = GRIP_MM_S if closing else MOVE_MM_S
        self._set_current(current_for(gap_from_pos(planned), self.force))
        self._send_segment(k, self._next_speed(k, remaining, vmax))
