# Gripper bench tool (MicroPython, Raspberry Pi Pico): power-up tests, homing, moves, grip, and a stand-alone demo.
#
# Copy this file to the Pico with Thonny (File > Save as > Raspberry Pi Pico, name it bench.py), then type in the
# Thonny shell:
#     import bench
# It prints the list of tests. docs/BUILD_AND_TEST_GUIDE.md says which one to run at each build step.
# Settings found by the tests (motor direction, encoder direction, tip set) are saved on the Pico in bench_cfg.json.
#
# This is a bench and demo tool, not the ROS 2 firmware. It drives the motor through the TMC2209 (STEP/DIR + UART),
# reads the AS5600 to know where the carriage really is, and stops a move when the encoder says the jaws have stopped.

from machine import Pin, UART, I2C, ADC
import rp2, time, json

# ---- wiring (DESIGN_REPORT.md, pin table) ----
STEP, DIR, EN, DIAG = 2, 3, 4, 5
UART_ID, UART_TX, UART_RX = 1, 8, 9     # TX through 1 k to PDN_UART, RX straight to PDN_UART
I2C_ID, I2C_SDA, I2C_SCL = 0, 0, 1
ADC_VM = 26
DIV = (100 + 27) / 27                    # motor-power divider 100 k / 27 k
AS5600 = 0x36

# ---- drive: Tr8x8 screw, 1/16 microstep ----
STEPS_PER_MM = 400
ENC_PER_MM = 4096 / 8                    # AS5600 counts per mm of carriage travel (one screw turn = 8 mm)
I_FULL = 0.70                            # A RMS at IRUN 31: set by the VREF pot (0.99 V on a BTT TMC2209 V1.3)
V_MIN = 7.0                              # below this the 9 V supply is gone: driver off
MAX_MM_S = 40                            # 300 rpm, the most the 9 V supply drives at full current
MOVE_MM_S = 20                           # normal moves
HOME_MM_S, HOME_A = 10, 0.30             # homing and gripping: close slowly at low current until the jaws stop
ACCEL = 300                              # mm/s^2
CHUNK = 100                              # steps per motion segment (0.25 mm)
MIN_GAP_N = 2.0                          # moves stop 2 mm short of closed (narrow-tip gap); grip() goes further

# Carriage position = steps from the open stop, bigger = more closed (DESIGN_REPORT.md section 3, narrow-tip gap).
GAP_TABLE = [(0, 12814), (6, 11968), (12, 11095), (18, 10199), (24, 9280), (30, 8333), (36, 7348),
             (42, 6309), (48, 5184), (54, 3911), (60, 2348), (66, 0)]
POS_TABLE = sorted((s, g) for g, s in GAP_TABLE)
# Homing stops where the jaws stop: narrow tips when the pads meet, wide tips when the carriage reaches the motor
# wall 1 mm further on (about a 17 mm pad gap).
HOME_POS = {'narrow': 12814, 'wide': 12814 + STEPS_PER_MM}
WIDE_OFS = 20                            # wide-tip pad gap = narrow-tip gap + 20 mm
# Run current against narrow-tip gap for about 30 N per jaw (section 4a).
CURRENT_TABLE = [(0, 0.70), (20, 0.70), (30, 0.69), (40, 0.64), (50, 0.54), (60, 0.37)]

# ---- saved settings ----
cfg = {'dir_close': 1, 'enc_sign': 1, 'tips': 'narrow', 'checked': False}
try:
    with open('bench_cfg.json') as f:
        cfg.update(json.load(f))
except (OSError, ValueError):
    pass

def save_cfg():
    with open('bench_cfg.json', 'w') as f:
        json.dump(cfg, f)

# ---- hardware ----
en = Pin(EN, Pin.OUT, value=1)           # high = driver off (the 10 k pull-up also holds it off while the Pico boots)
dirp = Pin(DIR, Pin.OUT, value=0)
diag = Pin(DIAG, Pin.IN)
adc = ADC(ADC_VM)
i2c = I2C(I2C_ID, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)
uart = UART(UART_ID, baudrate=115200, tx=Pin(UART_TX), rx=Pin(UART_RX))

def vm():
    """Motor supply voltage in volts (9 V when the trigger board is plugged into a power bank or charger)."""
    return adc.read_u16() * 3.3 / 65535 * DIV

# ---- TMC2209 over single-wire UART (datasheet section 4) ----
GCONF, GSTAT, IFCNT, IOIN, IHOLD_IRUN, CHOPCONF = 0x00, 0x01, 0x02, 0x06, 0x10, 0x6C

def _crc(data):
    crc = 0
    for b in data:
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if (crc >> 7) ^ (b & 1) else (crc << 1) & 0xFF
            b >>= 1
    return crc

def _xfer(msg, nreply):
    # The Pico hears its own bytes first (TX and RX share the PDN_UART wire), then the driver's reply.
    while uart.any():
        uart.read()
    uart.write(msg)
    want, buf, t0 = len(msg) + nreply, b'', time.ticks_ms()
    while len(buf) < want and time.ticks_diff(time.ticks_ms(), t0) < 30:
        n = uart.any()
        if n:
            buf += uart.read(n)
    return buf[len(msg):]

def tmc_write(reg, val):
    d = bytes([0x05, 0, reg | 0x80, (val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])
    _xfer(d + bytes([_crc(d)]), 0)

def tmc_read(reg):
    """Register value, or None if the driver did not answer correctly."""
    d = bytes([0x05, 0, reg])
    r = _xfer(d + bytes([_crc(d)]), 8)
    if len(r) != 8 or r[2] != reg or _crc(r[:7]) != r[7]:
        return None
    return (r[3] << 24) | (r[4] << 16) | (r[5] << 8) | r[6]

_amps = None
_configured = False

def set_current(amps):
    """Run and hold current in A RMS, never above the VREF ceiling. Hold = run: the screw back-drives."""
    global _amps
    cs = max(0, min(31, round(32 * amps / I_FULL) - 1))
    if _amps != cs:
        tmc_write(IHOLD_IRUN, (6 << 16) | (cs << 8) | cs)
        _amps = cs

def amps():
    return (_amps + 1) / 32 * I_FULL if _amps is not None else 0.0

def configure(a=HOME_A):
    """Send the driver settings. True when the driver counted every write."""
    global _configured, _amps
    c0 = tmc_read(IFCNT)
    tmc_write(GSTAT, 0x07)               # clear the reset and error flags
    tmc_write(GCONF, 0x1C1)              # VREF sets full scale (UART can only lower it), UART only, MRES from register
    tmc_write(CHOPCONF, 0x14000053)      # 1/16 microstep, interpolated to 1/256, default chopper (StealthChop)
    _amps = None
    set_current(a)
    c1 = tmc_read(IFCNT)
    _configured = c0 is not None and c1 is not None and (c1 - c0) & 0xFF == 4
    return _configured

# ---- AS5600 ----
enc_total, enc_last = 0, None

def _enc_raw():
    hi, lo = i2c.readfrom_mem(AS5600, 0x0C, 2)
    return ((hi << 8) | lo) & 0x0FFF

def enc():
    """Encoder position in counts, counting whole screw turns. Must be read at least every half turn (4 mm)."""
    global enc_total, enc_last
    a = _enc_raw()
    if enc_last is not None:
        d = (a - enc_last) & 0x0FFF
        enc_total += d - 4096 if d >= 2048 else d
    enc_last = a
    return enc_total

# ---- step pulses from a PIO state machine: (steps - 1, half-period) per segment, one word back when done ----
PIO_HZ = 2_000_000

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def _pulses():
    pull(block)
    mov(x, osr)                          # steps - 1
    pull(block)                          # half-period count, kept in OSR
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

sm = rp2.StateMachine(0, _pulses, freq=PIO_HZ, set_base=Pin(STEP))
sm.active(1)

def _delay(steps_per_s):
    return max(1, int(PIO_HZ / steps_per_s - 7) // 2)    # one step = 2 * delay + 7 PIO cycles

def _stop():
    sm.active(0)
    while sm.tx_fifo():
        sm.exec("pull(noblock)")
    while sm.rx_fifo():
        sm.get()
    sm.restart()
    sm.exec("set(pins, 0)")
    sm.active(1)

# ---- position and gap ----
pos = None                               # steps from the open stop; None until homed

def _lerp(x, pts):
    i = 1
    while i < len(pts) - 1 and x > pts[i][0]:
        i += 1
    (x0, y0), (x1, y1) = pts[i - 1], pts[i]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

def _wide():
    return WIDE_OFS if cfg['tips'] == 'wide' else 0

def gap():
    """Pad-to-pad gap in mm for the fitted tips (needs homing)."""
    return None if pos is None else _lerp(pos, POS_TABLE) + _wide()

def off():
    """Driver off. The jaws go limp: the screw back-drives."""
    en.value(1)

def _ready():
    global pos
    v = vm()
    if v < V_MIN:
        off()
        if pos is not None:
            print('Motor power lost: home again when it is back.')
        pos = None
        print('No motor power (%.1f V): plug the USB-C cable into the power bank or charger.' % v)
        return False
    g = tmc_read(GSTAT)
    if g is None:
        print('The driver does not answer on UART: run bench.t3_driver().')
        return False
    if g & 1 or not _configured:
        if g & 1 and pos is not None:
            print('The driver restarted (power came back): home again.')
            pos = None
        if not configure(amps() or HOME_A):
            print('The driver did not take its settings: run bench.t3_driver().')
            return False
    try:
        enc()
    except OSError:
        print('The encoder does not answer on I2C: run bench.t2_encoder().')
        return False
    en.value(0)
    return True

def _move(steps, mm_s, stall=False):
    """Move `steps` microsteps (positive closes). With stall=True, stop when the encoder shows the jaws stopped.
    Returns (signed steps really moved, from the encoder; reason: 'done', 'stall', 'power', 'timeout' or 'error')."""
    global pos
    if steps == 0:
        return 0, 'done'
    if not _ready():
        return 0, 'error'
    sign = 1 if steps > 0 else -1
    dirp.value(cfg['dir_close'] if sign > 0 else 1 - cfg['dir_close'])
    time.sleep_us(20)
    n = abs(steps)
    vmax = min(mm_s, MAX_MM_S) * STEPS_PER_MM
    a2, v02 = 2 * ACCEL * STEPS_PER_MM, (2 * STEPS_PER_MM) ** 2      # start and end at 2 mm/s
    e0 = e_seg = enc()
    sent = done = 0
    pending = []
    why = 'done'
    t_last = time.ticks_ms()
    while done < n:
        room = (not pending) if stall else (sm.tx_fifo() <= 2 and len(pending) < 3)
        if sent < n and room:
            k = min(CHUNK, n - sent)
            mid = sent + k / 2
            v = min(vmax, (v02 + a2 * mid) ** 0.5, (v02 + a2 * (n - mid)) ** 0.5)
            sm.put(k - 1)
            sm.put(_delay(v))
            pending.append(k)
            sent += k
        while sm.rx_fifo():
            sm.get()
            k = pending.pop(0)
            done += k
            t_last = time.ticks_ms()
            if stall:
                e = enc()
                moved = cfg['enc_sign'] * (e - e_seg) * sign
                e_seg = e
                if moved < 0.3 * k * ENC_PER_MM / STEPS_PER_MM:
                    why = 'stall'
        if not stall:
            enc()                        # keep counting screw turns during long moves
        if why == 'done' and vm() < V_MIN:
            why = 'power'
        if why == 'done' and time.ticks_diff(time.ticks_ms(), t_last) > 2000:
            why = 'timeout'
        if why != 'done':
            _stop()
            break
    made = round(cfg['enc_sign'] * (enc() - e0) * STEPS_PER_MM / ENC_PER_MM)
    if why == 'power':
        off()
        pos = None
        print('Motor power lost during the move: home again when it is back.')
    elif pos is not None:
        pos += made
    return made, why

# ---- user commands ----
def tips(name):
    """Tell the tool which tip set is fitted: bench.tips('narrow') or bench.tips('wide')."""
    global pos
    if name not in HOME_POS:
        print("Use 'narrow' or 'wide'.")
        return
    cfg['tips'] = name
    save_cfg()
    pos = None
    print('Tip set: %s. Home again: bench.home()' % name)

def home():
    """Close slowly at 0.3 A until the jaws stop. That point becomes 'closed' for the fitted tip set."""
    global pos
    if not cfg['checked']:
        print('Run bench.t4_direction() first.')
        return False
    pos = None
    set_current(HOME_A)
    made, why = _move(int(40 * STEPS_PER_MM), HOME_MM_S, stall=True)
    if why != 'stall':
        print('Homing failed (%s). If the jaws closed fully without stopping, check the encoder (bench.t5_tracking()).' % why)
        return False
    pos = HOME_POS[cfg['tips']]
    print('Homed: %s tips, closed. Pad gap now %.1f mm.' % (cfg['tips'], gap()))
    return True

def goto(gap_mm, mm_s=MOVE_MM_S):
    """Move to a pad-to-pad gap in mm (needs homing). Capped at 60 mm (80 mm wide) and 2 mm short of closed."""
    if pos is None:
        print('Home first: bench.home()')
        return False
    gn = max(MIN_GAP_N, min(60.0, gap_mm - _wide()))
    if abs(gn + _wide() - gap_mm) > 0.05:
        print('Limited to %.1f mm.' % (gn + _wide()))
    set_current(I_FULL)
    made, why = _move(round(_lerp(gn, GAP_TABLE)) - pos, mm_s)
    if pos is not None:
        print('Pad gap now %.1f mm%s.' % (gap(), '' if why == 'done' else ' (stopped: %s)' % why))
    return why == 'done'

def grip(mm_s=HOME_MM_S):
    """Close on an object until it stops the jaws. The current follows the gap for about 30 N per jaw, and stays on
    to hold (the screw back-drives without it)."""
    if pos is None:
        print('Home first: bench.home()')
        return False
    end = HOME_POS[cfg['tips']] - STEPS_PER_MM // 2     # half a mm before the closed point
    while pos < end:
        gn = max(0.0, min(60.0, _lerp(pos, POS_TABLE)))
        set_current(_lerp(gn, CURRENT_TABLE))
        made, why = _move(min(CHUNK, end - pos), mm_s, stall=True)
        if why == 'stall':
            print('Gripping at %.1f mm with %.2f A (about 30 N per jaw).' % (gap(), amps()))
            return True
        if why != 'done':
            return False
    print('Closed without meeting an object.')
    return False

def demo(open_gap=None):
    """Stand-alone demo: home, open, then each press of the Pico's BOOTSEL button grips or releases.
    Ctrl-C (or Stop in Thonny) ends it."""
    open_gap = open_gap or (40 if cfg['tips'] == 'narrow' else 60)
    holding = False
    print('Demo: press BOOTSEL on the Pico to grip or release.')
    while True:
        if pos is None:
            holding = False
            if vm() < V_MIN or not home() or not goto(open_gap):
                time.sleep(2)
                continue
        if rp2.bootsel_button():
            while rp2.bootsel_button():
                time.sleep_ms(10)
            if holding:
                holding = not goto(open_gap)
            else:
                holding = grip()
        time.sleep_ms(20)

def status():
    v = vm()
    g = tmc_read(IOIN)
    try:
        e = enc()
    except OSError:
        e = None
    print('Motor power %.1f V | driver %s | encoder %s | tips %s | %s' % (
        v, 'answers' if g is not None else 'NO ANSWER', e if e is not None else 'NO ANSWER', cfg['tips'],
        'pad gap %.1f mm' % gap() if pos is not None else 'not homed'))

# ---- bring-up tests, in build order ----
def t1_power():
    """Test 1: motor power. Expect about 9 V with the trigger board plugged in, about 0 V without."""
    for _ in range(10):
        v = vm()
        print('Motor power: %.2f V  %s' % (v, 'OK' if 8.3 < v < 9.7 else ('none' if v < 1 else 'CHECK: expected 9 V')))
        time.sleep(0.5)

def t2_encoder(seconds=15):
    """Test 2: AS5600. Turn the screw (or the 608) slowly by hand and watch the angle."""
    if AS5600 not in i2c.scan():
        print('AS5600 not found: check VCC to 3V3, GND, SDA to GP0, SCL to GP1, DIR to GND.')
        return
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < seconds * 1000:
        st = i2c.readfrom_mem(AS5600, 0x0B, 1)[0]
        mag = 'not detected' if not st & 0x20 else 'too weak' if st & 0x10 else 'too strong' if st & 0x08 else 'OK'
        agc = i2c.readfrom_mem(AS5600, 0x1A, 1)[0]
        print('magnet %-12s AGC %3d/128  angle %6.1f deg  turns %+.2f' % (mag, agc, _enc_raw() * 360 / 4096, enc() / 4096))
        time.sleep(0.2)

def t3_driver():
    """Test 3: TMC2209 over UART. Needs the 9 V plugged in (the driver's logic runs from 3V3, its UART needs VM)."""
    if vm() < V_MIN:
        print('Plug in the 9 V first (%.1f V now).' % vm())
        return False
    v = tmc_read(IOIN)
    if v is None:
        print('No reply. Check: 1 k from GP8 to the driver UART/PDN pin, GP9 straight to the same pin, driver seated '
              'the right way round, VIO to 3V3, GND.')
        return False
    print('Driver answers: version 0x%02X (TMC2209 = 0x21).' % (v >> 24))
    ok = configure(HOME_A)
    gc, ch = tmc_read(GCONF), tmc_read(CHOPCONF)
    print('Settings %s: GCONF 0x%03X (want 0x1C1), microsteps 1/%d (want 1/16).' % (
        'taken' if ok else 'NOT TAKEN', gc or 0, 256 >> ((ch or 0) >> 24 & 0xF) if ch is not None else 0))
    return ok

def t4_direction():
    """Test 4: which DIR level closes the jaws, and which way the encoder counts. Gripper fully assembled."""
    print('Push the jaws to about half open by hand (the driver is off, so they move freely).')
    input('Press Enter when ready... ')
    cfg['checked'] = True                # let _move run; reset below if the test fails
    set_current(HOME_A)
    e0 = enc()
    made, why = _move(2 * STEPS_PER_MM, 5)     # 2 mm in the direction currently called 'close'
    d = enc() - e0
    if why != 'done':
        print('The test move did not run (%s).' % why)
        cfg['checked'] = False
        return False
    closed = input('Did the jaws CLOSE a little? [y/n] ').strip().lower().startswith('y')
    if not closed:
        cfg['dir_close'] = 1 - cfg['dir_close']
    expect = 2 * ENC_PER_MM
    if abs(abs(d) - expect) > 0.25 * expect:
        print('The encoder moved %d counts, expected about %d. Check the magnet and the board (bench.t2_encoder()).' % (d, expect))
        cfg['checked'] = False
        save_cfg()
        return False
    cfg['enc_sign'] = 1 if (d > 0) == closed else -1
    save_cfg()
    _move(-2 * STEPS_PER_MM if closed else 2 * STEPS_PER_MM, 5)   # put the jaws back where they were
    print('Saved: dir_close=%d, enc_sign=%+d.' % (cfg['dir_close'], cfg['enc_sign']))
    return True

def t5_tracking():
    """Test 5: steps against encoder over half a screw turn each way. Jaws about half open."""
    set_current(I_FULL)
    for steps in (4 * STEPS_PER_MM, -4 * STEPS_PER_MM):
        made, why = _move(steps, 10)
        err = (made - steps) / STEPS_PER_MM
        print('Asked %+.1f mm, encoder saw %+.2f mm (%s) %s' % (steps / STEPS_PER_MM, made / STEPS_PER_MM, why,
              'OK' if abs(err) < 0.1 else 'CHECK: more than 0.1 mm off'))

def t6_home():
    """Test 6: home, then open to 30 mm (50 mm with the wide tips). Measure the pad gap with calipers: within 1 mm."""
    if home():
        goto(30 + _wide())

print('Gripper bench tool. Tests in build order:')
print('  bench.t1_power()  bench.t2_encoder()  bench.t3_driver()  bench.t4_direction()  bench.t5_tracking()  bench.t6_home()')
print('Then: bench.home()  bench.goto(40)  bench.grip()  bench.goto(40)  bench.demo()  bench.status()  bench.off()')
print("Tip set now '%s' (bench.tips('wide') to change)." % cfg['tips'])
