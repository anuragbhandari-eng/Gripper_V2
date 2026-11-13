# ROS 2 firmware for the gripper (MicroPython, Raspberry Pi Pico): answers one-line commands over USB serial.
#
# The ROS 2 hardware interface (ros2_ws/src/lead_screw_gripper_hardware) sends a command, this program sends one
# line back. The commands are listed at the top of gripper_core.py's handle_line() and in ros2_ws/README.md.
#
# Install (with Thonny, after the bench tests t1-t6 have passed, so bench_cfg.json on the Pico says "checked"):
#   1. Copy gripper_core.py and hal_pico.py to the Pico (File > Save as > Raspberry Pi Pico, same names).
#   2. Copy this file to the Pico as main.py. It then starts every time the Pico powers up.
#      (This replaces the BOOTSEL demo main.py. To get the demo back, save firmware/main.py over it again.)
#   3. Close Thonny before starting ROS: only one program can hold the USB serial port.
# To stop it and get the Thonny shell back: press and release the Pico's BOOTSEL button while it runs.
# (Ctrl-C is switched off on purpose, because a stray 0x03 byte from the host would otherwise stop it.)
# Then delete main.py from the Pico if you don't want it to start at the next power-up.
#
# Not yet run on the real gripper. It was tested on the laptop with the same gripper_core.py and a simulated
# Pico (ros2_ws/src/lead_screw_gripper_bringup, fake_pico).

import sys
import json
import select
import micropython
import rp2

import gripper_core
from hal_pico import PicoHal

cfg = {'dir_close': 1, 'enc_sign': 1, 'tips': 'narrow', 'checked': False}
try:
    with open('bench_cfg.json') as f:
        cfg.update(json.load(f))      # written by the bench tests: motor and encoder direction, tip set
except (OSError, ValueError):
    pass

hal = PicoHal(cfg)
core = gripper_core.GripperCore(hal, cfg)

micropython.kbd_intr(-1)              # a stray 0x03 byte from the host must not stop the program
poller = select.poll()
poller.register(sys.stdin, select.POLLIN)
line = ''
too_long = False

while True:
    # Read whatever has arrived, one character at a time, without waiting
    while poller.poll(0):
        ch = sys.stdin.read(1)
        if ch in ('\n', '\r'):
            if too_long:
                sys.stdout.write('ERR line_too_long\n')
            elif line:
                sys.stdout.write(core.handle_line(line) + '\n')
            line, too_long = '', False
        elif len(line) < gripper_core.MAX_LINE:
            line += ch
        else:
            too_long = True           # drop the rest of an over-long line, then report it once
    core.poll()
    if rp2.bootsel_button():
        # Escape hatch back to the REPL: stop the motor, switch the driver off, re-enable Ctrl-C
        core.handle_line('O')
        micropython.kbd_intr(3)
        break
