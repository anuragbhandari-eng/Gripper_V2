# AS5600 bench test (MicroPython, Raspberry Pi Pico). Run it before printing the bearing block.
#
# Why: in this design the magnet sits inside the steel 608 bearing, and steel can weaken or bend the magnet's
# field. This 5-minute test tells you whether the encoder still reads well in that position.
#
# Setup:
#   1. Glue the magnet into the printed puck (Encoder magnet puck x1) and push the puck into a 608 bearing.
#   2. Wire the AS5600 board to the Pico: VCC -> 3V3, GND -> GND, SDA -> GP0, SCL -> GP1, DIR -> GND.
#   3. Hold the board flat in front of the bearing, chip centred on the magnet, about 0.8 mm away
#      (a 0.8 mm shim or two business cards between them works).
#   4. Copy this file to the Pico (Thonny: File > Save as > Raspberry Pi Pico) and run it.
#   5. Slowly turn the bearing's inner ring through one full turn and watch the output.
#
# Good result: "magnet: OK" the whole time, AGC roughly in the middle (about 30-100 out of 128 on 3.3 V), and
# the angle running smoothly from 0 to 360 degrees once per turn. If it says "too weak" or AGC sits at 128,
# the bearing is soaking up the field: tell Claude, and the magnet gets moved in front of the bearing.

from machine import I2C, Pin
import time

AS5600 = 0x36                      # I2C address of the AS5600
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400_000)

def read16(reg):
    hi, lo = i2c.readfrom_mem(AS5600, reg, 2)
    return ((hi << 8) | lo) & 0x0FFF   # 12-bit value

if AS5600 not in i2c.scan():
    raise SystemExit('AS5600 not found: check the 4 wires and that DIR is tied to GND')

while True:
    status = i2c.readfrom_mem(AS5600, 0x0B, 1)[0]   # bit 5: magnet detected, bit 4: too weak, bit 3: too strong
    if not status & 0x20:
        magnet = 'not detected'
    elif status & 0x10:
        magnet = 'too weak'
    elif status & 0x08:
        magnet = 'too strong'
    else:
        magnet = 'OK'
    agc = i2c.readfrom_mem(AS5600, 0x1A, 1)[0]      # automatic gain: high means a weak field
    magnitude = read16(0x1B)                         # field strength as the chip sees it
    angle = read16(0x0C) * 360 / 4096                # raw angle in degrees
    print('magnet: {:13s} AGC {:3d}/128  magnitude {:4d}  angle {:6.1f} deg'.format(magnet, agc, magnitude, angle))
    time.sleep(0.2)
