# Simulated gripper hardware, for testing gripper_core.py on a laptop (normal Python only, never on the Pico).
#
# It has the same functions as hal_pico.py, but instead of pins it keeps a pretend carriage:
#   - step segments are "played" over simulated time at the requested speed;
#   - the carriage cannot pass the open stop, the closed point (pads meet, or the motor wall with wide tips),
#     or an object of a chosen width between the jaws. When it is blocked, steps still go out but the carriage
#     does not move, which is exactly what the real encoder would show;
#   - the AS5600 angle is computed from the true carriage position;
#   - faults can be switched on: no motor power, driver not answering, driver reset, encoder not answering.
#
# Time only moves when advance(ms) is called, so tests are exact and fast. The fake Pico calls advance()
# with the real elapsed time instead.
#
# Simplifications (it is a test tool, not a physics model): the carriage follows the step pulses exactly
# when it is free; no inertia, no missed steps, no current-dependent force.

import gripper_core as core


class SimHal:

    def __init__(self, start_gap=30.0, tips='narrow', object_mm=None, enc_sign=1, dir_close=1):
        self.t = 0.0                                   # simulated time, ms
        self.true_pos = core.pos_from_gap(start_gap)   # microsteps from the open stop, bigger = more closed
        self.closed_pos = core.HOME_POS[tips]
        self.object_mm = object_mm                     # width of an object between the jaws (linkage gap), or None
        self.enc_sign = enc_sign                       # +1: encoder counts up while closing
        self.dir_close = dir_close
        self.enc_offset = 1234                         # the magnet's angle at the open stop: any value works
        self.queue = []                                # segments waiting: [steps left, closing?, steps per s]
        self.frac = 0.0                                # part-step carried between time slices
        self.done = 0                                  # segments finished since the last segments_done()
        self.enabled = False
        self.amps = 0.0
        self.max_amps = 0.0                            # highest current ever set (tests check the 0.7 A ceiling)
        self.volts = 9.0
        self.driver = 'ok'                             # 'ok', 'silent' or 'reset' (reported once)
        self.encoder_ok = True
        self.configured = False
        self.steps_sent = 0

    # ---- simulated world ----
    def blocked_at(self, closing):
        """Position the carriage cannot pass in this direction."""
        if not closing:
            return 0.0
        limit = self.closed_pos
        if self.object_mm is not None:
            limit = min(limit, core.pos_from_gap(self.object_mm))
        return limit

    def advance(self, ms):
        """Move simulated time forward by `ms`, playing step segments."""
        end = self.t + ms
        while self.t < end:
            dt = min(1.0, end - self.t)
            self.t += dt
            if not self.queue or not self.enabled:
                continue
            seg = self.queue[0]
            steps = seg[2] * dt / 1000.0 + self.frac
            n = min(int(steps), seg[0])
            self.frac = steps - n if n < seg[0] else 0.0
            seg[0] -= n
            self.steps_sent += n
            if seg[1]:
                self.true_pos = min(self.true_pos + n, max(self.true_pos, self.blocked_at(True)))
            else:
                self.true_pos = max(self.true_pos - n, min(self.true_pos, self.blocked_at(False)))
            if seg[0] <= 0:
                self.queue.pop(0)
                self.done += 1

    def gap(self):
        return core.gap_from_pos(self.true_pos)

    # ---- the HAL functions gripper_core.py uses (same names as hal_pico.py) ----
    def ticks_ms(self):
        return int(self.t)

    def ticks_diff(self, a, b):
        return a - b

    def supply_volts(self):
        return self.volts

    def driver_status(self):
        if self.driver == 'reset':
            self.driver = 'ok'
            self.configured = False
            return 'reset'
        return self.driver

    def configure_driver(self, amps):
        if self.driver == 'silent' or self.volts < core.V_MIN:
            return False
        self.configured = True
        self.set_current(amps)
        return True

    def set_current(self, amps):
        self.amps = amps
        self.max_amps = max(self.max_amps, amps)

    def enable(self, on):
        self.enabled = on

    def encoder_raw(self):
        if not self.encoder_ok:
            raise OSError('encoder not answering')
        counts = self.enc_sign * self.true_pos * core.ENC_PER_MM / core.STEPS_PER_MM
        return int(round(counts + self.enc_offset)) & 0x0FFF

    def queue_segment(self, steps, closing, steps_per_s):
        self.queue.append([steps, closing, steps_per_s])

    def segment_room(self):
        return len(self.queue) < 3

    def segments_done(self):
        n, self.done = self.done, 0
        return n

    def stop(self):
        self.queue = []
        self.frac = 0.0
        self.done = 0
