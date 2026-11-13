# Real gripper hardware for the ROS 2 firmware (MicroPython, Raspberry Pi Pico).
#
# gripper_core.py does the thinking; this file only moves pins and talks to the chips. The hardware code is
# copied from bench.py (same wiring, constants and safety settings) and rearranged so that nothing here waits:
# a move is handed to the PIO step generator in short segments, and gripper_core.py checks on it every loop.
#
# Not yet run on the real gripper: test it with the bench tests first (docs/BUILD_AND_TEST_GUIDE.md), then
# with ros_main.py (see the top of that file).

from machine import Pin, UART, I2C, ADC
import rp2
import time

# ---- wiring (DESIGN_REPORT.md, pin table), same as bench.py ----
STEP, DIR, EN = 2, 3, 4
UART_ID, UART_TX, UART_RX = 1, 8, 9      # TX through 1 k to PDN_UART, RX straight to PDN_UART
I2C_ID, I2C_SDA, I2C_SCL = 0, 0, 1
ADC_VM = 26
DIV = (100 + 27) / 27                     # motor-power divider 100 k / 27 k
AS5600 = 0x36
I_FULL = 0.70                             # A RMS at IRUN 31: set by the VREF pot (0.99 V on a BTT TMC2209 V1.3)

# ---- TMC2209 registers ----
GCONF, GSTAT, IFCNT, IHOLD_IRUN, CHOPCONF = 0x00, 0x01, 0x02, 0x10, 0x6C

# ---- step pulses from a PIO state machine: (steps - 1, half-period) per segment, one word back when done ----
PIO_HZ = 2_000_000


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def _pulses():
    pull(block)
    mov(x, osr)                           # steps - 1
    pull(block)                           # half-period count, kept in OSR
    label("step")
    set(pins, 1)
    mov(y, osr)
    label("hi")
    jmp(y_dec, "hi")
    set(pins, 0)
    mov(y, osr)
    label("lo")
    jmp(y_dec, "lo")
    jmp(x_dec, "step")
    push(noblock)


class PicoHal:

    def __init__(self, cfg):
        self.cfg = cfg                    # dir_close from bench_cfg.json
        self.en = Pin(EN, Pin.OUT, value=1)       # high = driver off (a 10 k pull-up also holds it off at boot)
        self.dirp = Pin(DIR, Pin.OUT, value=0)
        self.adc = ADC(ADC_VM)
        self.i2c = I2C(I2C_ID, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)
        self.uart = UART(UART_ID, baudrate=115200, tx=Pin(UART_TX), rx=Pin(UART_RX))
        self.sm = rp2.StateMachine(0, _pulses, freq=PIO_HZ, set_base=Pin(STEP))
        self.sm.active(1)
        self.in_flight = 0                # segments handed to the PIO and not finished yet
        self.cs = None                    # current scale last written (0-31)
        self.closing = None

    # ---- time ----
    def ticks_ms(self):
        return time.ticks_ms()

    def ticks_diff(self, a, b):
        return time.ticks_diff(a, b)

    # ---- motor power ----
    def supply_volts(self):
        return self.adc.read_u16() * 3.3 / 65535 * DIV

    # ---- TMC2209 over single-wire UART (datasheet section 4) ----
    def _crc(self, data):
        crc = 0
        for b in data:
            for _ in range(8):
                crc = ((crc << 1) ^ 0x07) & 0xFF if (crc >> 7) ^ (b & 1) else (crc << 1) & 0xFF
                b >>= 1
        return crc

    def _xfer(self, msg, nreply):
        # The Pico hears its own bytes first (TX and RX share the PDN_UART wire), then the driver's reply.
        while self.uart.any():
            self.uart.read()
        self.uart.write(msg)
        want, buf, t0 = len(msg) + nreply, b'', time.ticks_ms()
        while len(buf) < want and time.ticks_diff(time.ticks_ms(), t0) < 30:
            n = self.uart.any()
            if n:
                buf += self.uart.read(n)
        return buf[len(msg):]

    def _write(self, reg, val):
        d = bytes([0x05, 0, reg | 0x80, (val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])
        self._xfer(d + bytes([self._crc(d)]), 0)

    def _read(self, reg):
        """Register value, or None if the driver did not answer correctly."""
        d = bytes([0x05, 0, reg])
        r = self._xfer(d + bytes([self._crc(d)]), 8)
        if len(r) != 8 or r[2] != reg or self._crc(r[:7]) != r[7]:
            return None
        return (r[3] << 24) | (r[4] << 16) | (r[5] << 8) | r[6]

    def driver_status(self):
        """'silent' if it does not answer, 'reset' if it restarted (its settings are lost), else 'ok'."""
        g = self._read(GSTAT)
        if g is None:
            return 'silent'
        return 'reset' if g & 1 else 'ok'

    def configure_driver(self, amps):
        """Send the driver settings. True when the driver counted every write (same as bench.configure)."""
        c0 = self._read(IFCNT)
        self._write(GSTAT, 0x07)          # clear the reset and error flags
        self._write(GCONF, 0x1C1)         # VREF sets full scale (UART can only lower it), UART only, MRES from register
        self._write(CHOPCONF, 0x14000053)  # 1/16 microstep, interpolated to 1/256, StealthChop
        self.cs = None
        self.set_current(amps)
        c1 = self._read(IFCNT)
        return c0 is not None and c1 is not None and (c1 - c0) & 0xFF == 4

    def set_current(self, amps):
        """Run and hold current in A RMS, never above the VREF ceiling. Hold = run: the screw back-drives."""
        cs = max(0, min(31, round(32 * amps / I_FULL) - 1))
        if self.cs != cs:
            self._write(IHOLD_IRUN, (6 << 16) | (cs << 8) | cs)
            self.cs = cs

    def enable(self, on):
        self.en.value(0 if on else 1)

    # ---- AS5600 ----
    def encoder_raw(self):
        """12-bit magnet angle (0-4095). Raises OSError if the encoder does not answer."""
        hi, lo = self.i2c.readfrom_mem(AS5600, 0x0C, 2)
        return ((hi << 8) | lo) & 0x0FFF

    # ---- step segments ----
    def queue_segment(self, steps, closing, steps_per_s):
        if closing != self.closing:
            # gripper_core only turns around when no segment is in flight, so changing DIR here is safe
            self.dirp.value(self.cfg['dir_close'] if closing else 1 - self.cfg['dir_close'])
            self.closing = closing
            time.sleep_us(20)
        delay = max(1, int(PIO_HZ / steps_per_s - 7) // 2)   # one step = 2 * delay + 7 PIO cycles
        self.sm.put(steps - 1)
        self.sm.put(delay)
        self.in_flight += 1

    def segment_room(self):
        return self.sm.tx_fifo() <= 2

    def segments_done(self):
        n = 0
        while self.sm.rx_fifo():
            self.sm.get()
            n += 1
        self.in_flight = max(0, self.in_flight - n)
        return n

    def stop(self):
        """Stop the pulses at once and throw away queued segments (same as bench._stop)."""
        self.sm.active(0)
        while self.sm.tx_fifo():
            self.sm.exec("pull(noblock)")
        while self.sm.rx_fifo():
            self.sm.get()
        self.sm.restart()
        self.sm.exec("set(pins, 0)")
        self.sm.active(1)
        self.in_flight = 0
