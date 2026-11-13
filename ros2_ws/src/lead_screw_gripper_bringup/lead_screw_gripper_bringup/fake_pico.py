"""Fake Pico: the real gripper firmware logic, running on the laptop against a simulated gripper.

It creates a pseudo-terminal (a software serial port) and links it to a path such as /tmp/lsg_fake_pico.
The ROS 2 hardware interface opens that path exactly as it would open /dev/ttyACM0 for the real Pico.
Behind it, gripper_core.py (the same file that runs on the Pico) drives hal_sim.py, a simulated
motor, screw, encoder and object.

    ros2 run lead_screw_gripper_bringup fake_pico --link /tmp/lsg_fake_pico --object-mm 30

--object-mm puts an object of that width between the jaws, like a person would: only after homing has
finished and the jaws have opened wider than the object.
"""
import argparse
import os
import select
import sys
import time
import tty

from lead_screw_gripper_bringup.firmware_path import add_firmware_to_path

add_firmware_to_path()
import gripper_core  # noqa: E402
from hal_sim import SimHal  # noqa: E402


class FakePico:

    def __init__(self, start_gap=30.0, tips='narrow', object_mm=None):
        self.hal = SimHal(start_gap=start_gap, tips=tips)
        cfg = {'dir_close': 1, 'enc_sign': 1, 'tips': tips, 'checked': True}
        self.core = gripper_core.GripperCore(self.hal, cfg)
        self.object_mm = object_mm
        self.object_placed = False

    def handle(self, line):
        if len(line) > gripper_core.MAX_LINE:
            return 'ERR line_too_long'
        return self.core.handle_line(line)

    def step(self, ms):
        """Advance the simulation by `ms` of real time, then run the firmware loop once."""
        self.hal.advance(ms)
        self.core.poll()
        if (self.object_mm is not None and not self.object_placed
                and self.core.flags() & gripper_core.F_HOMED and self.hal.gap() > self.object_mm + 1.0):
            self.hal.object_mm = self.object_mm
            self.object_placed = True
            print('fake_pico: placed a %.1f mm object between the jaws' % self.object_mm, flush=True)


def serve(link, fake, verbose=False):
    master, slave = os.openpty()
    tty.setraw(slave)                    # no echo or line editing on the software serial port
    if os.path.lexists(link):
        os.remove(link)
    os.symlink(os.ttyname(slave), link)
    print('fake_pico: serial port ready at %s' % link, flush=True)
    buf = b''
    last = time.monotonic()
    try:
        while True:
            ready, _, _ = select.select([master], [], [], 0.002)
            if ready:
                try:
                    data = os.read(master, 1024)
                except OSError:
                    data = b''
                buf += data
                while b'\n' in buf:
                    raw, buf = buf.split(b'\n', 1)
                    line = raw.decode(errors='replace').strip('\r')
                    if not line:
                        continue
                    reply = fake.handle(line)
                    if verbose and line != 'R':
                        print('fake_pico: %s -> %s' % (line, reply), flush=True)
                    os.write(master, (reply + '\n').encode())
            now = time.monotonic()
            fake.step(min(50.0, (now - last) * 1000.0))
            last = now
    finally:
        if os.path.islink(link):
            os.remove(link)
        os.close(master)
        os.close(slave)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if '--ros-args' in argv:             # started from a launch file: ignore the ROS arguments
        argv = argv[:argv.index('--ros-args')]
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--link', default='/tmp/lsg_fake_pico', help='path for the fake serial port')
    p.add_argument('--start-gap', type=float, default=30.0, help='jaw gap (mm) at power-up')
    p.add_argument('--tips', choices=['narrow', 'wide'], default='narrow')
    p.add_argument('--object-mm', type=float, default=None, help='object width (mm), placed after homing')
    p.add_argument('--verbose', action='store_true', help='print every command except R')
    args = p.parse_args(argv)
    fake = FakePico(args.start_gap, args.tips, args.object_mm)
    try:
        serve(args.link, fake, args.verbose)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
