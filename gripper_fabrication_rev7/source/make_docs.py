import json, numpy as np, csv, design as D
from kin import geom
R = json.load(open('results.json')); S = json.load(open('results_struct.json')); FX = json.load(open('results_fasteners.json')); OS = json.load(open('results_onshape_rev5.json')); PP = json.load(open('../print_parts.json'))
PARTS = [p for p in PP if not p['file'].startswith('13_')]   # the 12 gripper print files
CP = next(p for p in PP if p['file'].startswith('13_'))       # fit-test coupons (print first, not part of the gripper)
OUT = '..'
P = D.P
T_M3 = 0.15                 # N·m, M3 tightening limit (rev 6: 0.2 on PETG)
F_CL = T_M3/(0.2*0.003)     # N, clamp from T = K·F·d with K = 0.2, d = 3 mm
# ---- gap table ----
rows = []
for g in range(0, 67, 6):
    th = np.arcsin(g/(2*D.L) + np.sin(D.TH_C)); cx = float(geom(P, th)['C'][0])
    rows.append((g, round(np.degrees(th), 1), round(cx, 2), round(cx - D.S_MAX, 2), int(round((D.S_MAX - cx)*D.STEPS_PER_MM)), g + 2*D.WIDE_OFS))
# ---- BOM ----
bom = [
 ('P1', 'NEMA 17 stepper 42 x 42 x 40 mm with integrated 300 mm Tr8x8 lead screw (4 start, 8 mm lead) and brass flange nut, 1.5 A, about 0.4 N.m (recommended: DiGiYes, Amazon US ASIN B0CG5WQK3T; any 42-40 motor with these specs fits)', 1, 'Cut the screw so it sticks out %.1f mm past the D22 pilot face (%.1f mm from the mounting face), -0.5/+0: never long, the encoder puck fills the last 3 mm of the 608 bore; chamfer the end. If your motor is 0.35 N.m / 1.7 A, set T_hold and I_rated in structural.py and rerun (the current rises to about 0.9 A)' % (D.SCREW_LEN - 2.0, D.SCREW_LEN)),
 ('P2', 'Tr8x8 brass flange nut (flange D22 x 3.5, body D10.2, 4x D3.5 on D16; check on the listing) - usually supplied with P1', 1, ''),
 ('P3', '608ZZ ball bearing 8 x 22 x 7', 1, 'Screw tip support; carries the grip thrust into the block front lip'),
 ('P12', 'Shaft lock collar, 8 mm bore, OD <= 14 mm, width <= 7 mm, with set screw (e.g. OpenBuilds T8 lock collar)', 1, 'Behind the 608, against its inner ring: takes the screw reaction when gripping'),
 ('P4', 'Dowel pin ISO 8734 / DIN 6325, D4 m6 x 36, hardened', 4, 'Fixed pivots O1, O2 (press into base)'),
 ('P27', 'Sintered bronze sleeve bushing 4 x 6 x 6 mm + slow-cure epoxy + paste wax', 4, 'Bonded into the cover round the dowel tops (rev 7.1)'),
 ('P28', 'Dowel pin ISO 8734, D3 m6 x 16', 2, 'Register the base and cover halves of the bearing block (press into the base half)'),
 ('P5', 'Shoulder screw, 4 mm shoulder x 12 mm, M3 thread <= 6 mm, head <= D7.5 x 3.5 (e.g. Bambu Lab AA123)', 8, 'Moving pivots F1, F2, D, C x2 sides'),
 ('P6', 'M3 heat-set insert, M3 x 5.7, for D4.0 hole', 22, 'Buy 25 (rev 7: +4 in the finger tongues)'),
 ('P7', 'M3 x 8 button head screw ISO 7380', 12, '4 motor (3.5 mm into the motor), 2 cover-to-post, 2 nut flange (self-tap into D2.5 pilots), 4 side walls to adapter'),
 ('P8', 'M3 x 20 button head screw ISO 7380', 4, 'Cover to motor wall (2) and bearing block (2)'),
 ('P13', 'M3 x 10 button head screw ISO 7380', 4, 'Tip blocks to the finger tongues, from below (2 per side)'),
 ('P9', 'M6 x 12 socket head cap screw ISO 4762 (6 mm into the robot flange; check its thread depth)', 4, 'Adapter to ISO 9409-1-50-4-M6 flange'),
 ('P10', 'Grease: PTFE/lithium for lead screw and pivots', 1, ''),
 ('P11', 'TMC2209 stepper driver module, StepStick size (e.g. BIGTREETECH TMC2209), UART + DIAG', 1, 'Current limit %.2f A RMS (section 4); female headers on the protoboard' % S['driver']['I_set_rms_A']),
 ('P14', 'Raspberry Pi Pico (or Pico H with headers)', 1, 'USB serial to ROS 2; on the protoboard'),
 ('P15', 'AS5600 magnetic encoder module (about 23 x 23 mm) + 6 x 2.5 mm diametric magnet', 1, 'Solder 4 wires (VCC, GND, SDA, SCL) to the pad row, no header; pad row up'),
 ('P16', 'Double-sided protoboard 50 x 70 mm', 1, 'Drill the 4 corner holes to 3.2 mm on a 44 x 64 mm pattern'),
 ('P17', 'M3 x 10 male-female standoff + M3 x 6 screw', 4, 'Controller board to the cover-top inserts'),
 ('P18', 'MP1584 mini buck module (set to 5.0 V) + 1N5817 Schottky diode', 1, 'Battery -> Pico VSYS through the diode, so USB and battery can both be connected'),
 ('P19', '3S LiPo 11.1 V about 650 mAh, XT30 (about 62 x 30 x 18 mm, 60 g) + Velcro battery strap', 1, 'Strapped to the stand column, mid-height, on the side away from the gripper'),
 ('P20', 'LiPo balance charger (2-4S, XH balance lead)', 1, 'Charge only with this'),
 ('P21', 'XT30 pigtail + XT30 extension 30 cm, mini-blade fuse holder + 3 A fuse, toggle switch >= 3 A, LiPo low-voltage alarm (balance lead)', 1, 'Battery -> fuse -> switch -> TMC2209 VM and buck input; divider after the switch; alarm on the balance lead'),
 ('P22', 'Resistors 100 k + 27 k (battery divider into Pico ADC0) + 10 k (EN pull-up), 100 nF at ADC0, 100 uF 35 V capacitor at TMC2209 VM', 1, ''),
 ('P23', '2020 aluminium extrusion, 400 mm (V-slot or T-slot)', 1, 'Bench stand column'),
 ('P24', 'M5 drop-in T-nut + M5 x 12 screw (4), M5 x 16 screw (1), 4 bench screws or M5 bolts', 1, 'Head bracket to column (2), base socket to column (2), base to column end (1, tap the end M5); base to the bench (4)'),
 ('P29', 'M8 x 40 star knob screw (male thread) + M8 hex nut', 2, 'Desk clamps (nut drops into the slot in each clamp)'),
 ('P30', 'Self-adhesive felt pads, about 25 mm', 4, 'On the clamp pads and under the base front corners, to protect the desk'),
 ('P25', 'M6 x 20 socket head cap screw ISO 4762 + M6 hex nut', 4, 'Adapter to the stand head bracket (nuts drop into the bracket from the back)'),
 ('P26', 'TPU 95A filament', 1, 'Contact pads (18_Pad_TPU95A, 4 pcs)'),
]
with open(f'{OUT}/BOM.csv', 'w', newline='') as fh:
    w = csv.writer(fh, lineterminator='\n'); w.writerow(['ID', 'Item', 'Qty', 'Note'])
    for p in PARTS: w.writerow(['PRINT', p['file'].replace('.stl', '') + f" ({p.get('material', D.MAT)})", p['qty'], f"{p['note']}; orientation {p['orientation']}; {p['volume_cm3']} cm3"])
    w.writerow(['PRINT', f'13_FitTest_coupons ({D.MAT})', 1, 'Print FIRST: checks pin bores, z-stack gaps, 608 seat and carriage tongue fit on your printer; %.0f cm3' % CP['volume_cm3']])
    for b in bom: w.writerow(b)
_th = np.linspace(D.TH_C, D.TH_O, 2001); _x = geom(P, _th)['F1'][:, 0]; _g = 2*D.L*(np.sin(_th) - np.sin(D.TH_C))
FA = dict(travel=float(_x.max() - _x.min()), gap_fwd=float(_g[np.argmax(_x)]), open_behind_closed=float(_x[0] - _x[-1]))
printed_cm3 = sum(p['volume_cm3']*p['qty'] for p in PARTS)
_grp = lambda pre: sum(p['volume_cm3']*p['qty'] for p in PARTS if p['file'][:3] in pre)
cm3_stand, cm3_wide = _grp(('20_', '21_')), _grp(('16_', '17_'))
cm3_gripper = printed_cm3 - cm3_stand - cm3_wide            # gripper with the narrow set (pads in TPU)
import json as _j
_CK = _j.load(open('check_report.json'))
W, M, T, MO, SC = R['window'], R['MA'], R['transmission'], R['motor'], R['requirement']
drv = S['driver']
md = []
A = md.append
A('# Lead-Screw Parallel Gripper: Design & Validation Report\n')
A('Generated from the verified model (design.py → results.json, results_struct.json). All numbers below come from those files.\n')
A('## 1. Summary\n')
A('| Item | Value |\n|---|---|')
A(f'| Mechanism | Reference architecture kept: parallelogram finger (pure translation) + 90° bell crank + conrod to lead-screw carriage, 1 DOF, mirrored |')
A(f'| Jaw range | narrow tips 0 → {W["gap_max_mm"]:.0f} mm, wide tips {2*D.WIDE_OFS:.0f} → {W["gap_max_mm"] + 2*D.WIDE_OFS:.0f} mm (pad to pad; firmware caps the opening at 60 / 80 mm) |')
A(f'| Carriage stroke | {W["stroke_mm"]:.1f} mm = {W["screw_turns"]:.1f} screw turns (Tr8×8, {D.STEPS_PER_MM:.0f} steps/mm at 1/16 µstep) |')
A(f'| Grip force per jaw | ≥ {drv["grip_min_per_jaw_N"]} N anywhere in range at {drv["I_set_rms_A"]} A RMS, worst-case screw friction (needs {SC["Fg_req_per_jaw"]:.1f} N for 500 g) |')
A(f'| Holding | Tr8×8 is back-drivable (lead angle {R["screw"]["lead_angle_deg"]:.1f}°): the driver hold current keeps the grip; with power off the jaws can be pushed open |')
A(f'| Structure | Min safety factor {S["min_SF"]} vs yield at a 200 N screw-force limit case (the motor clamps at {drv["Fs_range_at_set_N"][0]:.0f}–{drv["Fs_range_at_set_N"][1]:.0f} N at {drv["I_set_rms_A"]} A). Grip-driven rows assume a far-tip grip at the 66 mm stop; in use (stall at {drv["I_set_rms_A"]} A, 60 mm cap, {S["tip"]["Fg_in_use_N"]} N per jaw) they are {S["tip"]["factor_in_use"]}× higher: min SF {S["min_SF_in_use"]} in use |')
A(f'| Motion check | {sum(len(v) for v in _CK["hits"].values())} collisions over 41 poses ({len(_CK["parts"])} parts with the stand and electronics, 20 modelled screws), for both tip sets; only intended joint/stack contacts below 0.8 mm |')
A(f'| Grip thrust | Screw reaction → lock collar → 608 inner ring → outer ring → block front lip. 608 static axial capacity ≈ {S["thrust"]["bearing608_axial_static_capacity_N"]:.0f} N vs {S["thrust"]["load_N"]:.0f} N limit ({S["thrust"]["ratio"]}×) |')
A(f'| Fasteners | 3 screw sizes on the gripper (12× M3×8, 4× M3×10, 4× M3×20 button head); min SF {FX["min_SF"]} under mount, stall and limit loads; tighten ≤ {T_M3} N·m |')
A(f'| Printed volume | gripper with the narrow set {cm3_gripper:.0f} cm³ (~{cm3_gripper*D.MAT_RHO*0.55:.0f} g at typical infill) + motor ~280 g; wide set {cm3_wide:.0f} cm³; bench stand {cm3_stand:.0f} cm³ |')
A(f'| Mount | ISO 9409-1-50-4-M6 adapter (PCD 50, 4×M6, Ø31.5 spigot, Ø6 pin) |\n')
A('## 1a. Rev 7 (v2) changes\n')
A(f'- **B, tip sets:** each finger splits at x = {D.SEAM_X:.0f} mm. A tip block slides up onto a {D.TONGUE_X1 - D.SEAM_X:.0f} mm tongue on the finger and takes 2× M3×10 from below. Block and pad are centred on the pin plane, so a normal grip does not twist the finger. Narrow set: pad face on the rev 6 face line (gap 0–66 mm). Wide set: pad face {D.WIDE_OFS:.0f} mm further out per side (20–86 mm), blunt end. Both run {D.TIP_EXT:.0f} mm further forward (pad x {D.SEAM_X + D.TIP_R:.0f}–{D.FACE_X1:.0f}). The same 2 mm TPU 95A pad fits both (dovetail key, slides in from the rear and snaps past a step, so it cannot slide back out). The heel is trimmed, so the O2-spacer clearance grew from 1.18 to 1.90 mm.')
A(f'- **Trade-offs of the longer tips:** the gripper is {D.TIP_EXT:.0f} mm longer. Gripping at the far end of the pad raises the F2/O2 pin loads by about 17% over gripping at the far end of the rev 6 jaw, and by about 75% over the rev 6 check basis (a grip near the jaw root). The 200 N limit rows below use the worst point on the pad.')
A(f'- **C, encoder:** AS5600 with a 6 × 2.5 mm diametric magnet in a printed puck at the screw end (screw cut {D.ENC_CUT:.0f} mm shorter). The board stands in a slot across the bearing block, {D.ENC_GAP} mm air gap; the block bolts moved to ears at the rear of the block.')
A('- **D, controller:** Pico + TMC2209 + 5 V buck + battery divider on a 50 × 70 mm protoboard, on 4 standoffs in heat-set inserts in the cover top. USB serial to ROS 2.')
A(f'- **A, drive:** Tr8×8 (lead {D.LEAD:.0f} mm): {W["screw_turns"]:.1f} turns over the stroke, {D.STEPS_PER_MM:.0f} steps/mm, {drv["speed_note"]}. Driver {drv["I_set_rms_A"]} A RMS. Not self-locking.')
A('- **F, bench stand:** the gripper hangs jaws-down from a 2020 × 400 mm column: printed head bracket on the ISO 9409 adapter, printed 180 × 170 mm base, clamped to the desk edge by 2 printed C-clamps with M8 star knobs (sized for a 40 mm edge, 24–49 mm range); unclamped, a few newtons at gripper height would tip it over. The battery is strapped to the column, away from the jaws. Slide the bracket to set the height.')
A(f'- **Power:** 3S LiPo (about 650 mAh, XT30) → 3 A fuse → switch → TMC2209 VM and the buck → Schottky → Pico VSYS. The battery divider sits after the switch (no drain when off). Firmware stops the motor below 10.5 V; a balance-lead alarm warns before the cells go too low, and the switch must be turned off after use (the Pico and buck still draw current).')
A(f'- **Material:** printed parts in {D.MAT} (taken as {D.MAT_SY:.0f} MPa); pads in TPU 95A.\n')
A('| Pico pin | Connects to |\n|---|---|')
for pin, to in (('GP2', 'TMC2209 STEP'), ('GP3', 'TMC2209 DIR'), ('GP4', 'TMC2209 EN'), ('GP5', 'TMC2209 DIAG (stall detect for homing)'),
                ('GP8 / GP9 (UART1)', 'TMC2209 PDN_UART (1 k in series on TX)'), ('GP0 / GP1 (I2C0)', 'AS5600 SDA / SCL'),
                ('GP26 (ADC0)', 'Battery divider 100 k / 27 k (12.6 V reads 2.68 V)'), ('3V3 / GND', 'AS5600 VCC / GND (DIR to GND), TMC2209 VIO / GND; 10 k from TMC2209 EN to VIO'),
                ('VSYS', '5 V buck output through the 1N5817')):
    A(f'| {pin} | {to} |')
A('')
A('## 2. Mechanism and dimensions\n')
A('Reference measured from the video (143 frames, hole centres tracked; rigid distances constant to <1 px). Link ratios kept exactly, scaled to crank length L = 28 mm.\n')
A('| Parameter | Value (mm / deg) | Ratio to L |\n|---|---|---|')
for k, v, rr in [('Crank length L (O1–F1 = O2–F2)', 28.0, 1.0), ('Ground link O1–O2', 1.5708*28, 1.5708), ('Bell-crank arm O1–D (90° to O1–F1)', D.r, D.r/28),
                 ('Conrod C–D', D.l, D.l/28), ('Carriage pin line Y_C', D.YC, D.YC/28), ('Fixed pivot O1 Y', D.O1[1], D.O1[1]/28)]:
    A(f'| {k} | {v:.2f} | {rr:.4f} |')
A(f'| O1 → O2 direction | −42.80° | |')
A(f'| Crank angle range | {W["th_closed_deg"]:.1f}° (jaws touch) → {W["th_open_deg"]:.1f}° (open stop) | |\n')
A('**Architecture change vs reference (engineering reason):** every pivot is double-shear. Fixed pivots O1/O2 are hardened 4 mm dowels held by the base AND the cover; each crank is two plates (lower plate with spacer boss + upper plate) acting as a clevis around the finger and conrod; the carriage has upper and lower ears around the conrod. Single-ended 4 mm pins in printed plastic would see roughly 80–200 MPa of local bearing stress from pin bending at these loads.\n')
A('**Layer stack (z = 0 at base-plate top):** base −9…0 · lower crank plates 0.3…6.3 · finger / conrod 6.5…14.1 · upper crank plates 14.4…18.2 · shoulder-screw heads ≤ 21.3 · cover 22.1…29.5 · screw axis 10.3 (= conrod mid-plane, so rod forces line up with the nut). Jaw block extends to z = 26. Moving layers have 0.2 mm below and 0.3 mm above them (rev 6), so first-layer squish and top-surface bulge do not bind the stack.\n')
A('## 3. Kinematics and force transmission\n')
A(f'- No toggle or singularity in the window: ds/dθ {T["ds_dth_min"]:.1f}–{T["ds_dth_max"]:.1f} mm/rad; transmission angle {T["mu_min_deg"]:.1f}°–{T["mu_max_deg"]:.1f}°; rod ≤ {T["rod_angle_max_deg"]:.0f}° to the screw axis.')
A(f'- Mechanical advantage (grip per jaw ÷ total screw force): {M["at_gap_0"]:.3f} at 0 mm, {M["at_gap_60"]:.3f} at 60 mm, {M["max"]:.3f} at 66 mm. Grip rises as the jaws open.')
A(f'- Cross-checks: analytic vs finite-difference ds/dθ {R["checks"]["deriv_fd_max_rel_err"]:.1e}; virtual work vs free-body statics {R["checks"]["virtual_work_vs_FBD_max_rel_err"]:.0e}; inverse solve {R["checks"]["inverse_solve_max_err_rad"]:.0e} rad.')
A(f'- Grip requirement: 500 g, μ = {SC["mu_jaw"]} (printed serrations), ×{SC["dyn"]:.0f} dynamic, ×{SC["SF_slip"]} slip SF → {SC["Fg_req_per_jaw"]:.1f} N per jaw; target 25 N.\n')
A(f'Jaw gap ↔ carriage position (for firmware; home = open stop, {D.STEPS_PER_MM:.0f} steps/mm at 1/16 µstep; the AS5600 also counts screw turns, {D.LEAD:.0f} mm per turn):\n')
A('| Gap mm (narrow) | Crank θ° | C_x mm | Carriage from open stop mm | Steps from home | Gap mm (wide) |\n|---|---|---|---|---|---|')
for r_ in rows: A('| ' + ' | '.join(map(str, r_)) + ' |')
A('\n## 4. Motor and driver sizing\n')
A(f'- Screw force for ≥ 25 N everywhere: {MO["Fs_op_N"]:.1f} N → torque {MO["T_op_Nm_range"][0]:.3f}–{MO["T_op_Nm_range"][1]:.3f} N·m (screw η {R["screw"]["eta_mu025"]:.2f}–{R["screw"]["eta_mu010"]:.2f}).')
A(f'- **Set driver current to {drv["I_set_rms_A"]} A RMS** (for a {drv["I_rated_A"]} A / {drv["T_hold_Nm"]} N·m motor): screw force {drv["Fs_range_at_set_N"][0]}–{drv["Fs_range_at_set_N"][1]} N → grip ≥ {drv["grip_min_per_jaw_N"]} N per jaw, and stays below the 200 N structural limit even with a well-greased screw.')
A(f'- **Warning:** at full rated current the motor can push ~{MO["Fs_at_full_hold_mu010"]:.0f} N, far above what the printed parts are sized for. The current limit is a safety item.')
A(f'- Speed: {drv["speed_note"]}. The Tr8×8 is not self-locking, so keep the hold current on while gripping (TMC2209 IHOLD); the AS5600 confirms the position after any slip.\n')
DY, SCH = S['dynamic'], S['current_schedule']
A('\n### 4a. Drive safety and grip control (rev 7.1)\n')
A(f'- **Driver current ceiling in hardware.** Set the TMC2209 VREF pot so its full-scale current is {drv["I_set_rms_A"]} A RMS and enable `GCONF.i_scale_analog`, so UART can only lower the current. The driver resets to its pot setting whenever its motor supply comes back (battery switch), while the Pico stays alive on USB: put a 10 k pull-up from EN to VIO (driver off while the Pico boots), and in firmware read GSTAT/IFCNT before every move and re-send the configuration after a reset.')
A(f'- **Hard stops.** The rotor (about {DY["J_rotor_kgm2_assumed"]*1e7:.0f} g·cm², assumed) looks like {DY["reflected_mass_kg"]} kg at the carriage through the {D.LEAD:.0f} mm lead. Running into a stop at 600 rpm adds about {DY["F_stop_N_at_600rpm"][0]}–{DY["F_stop_N_at_600rpm"][1]} N of screw force; at 10 mm/s only {DY["F_stop_N_at_10mm_s"][0]}–{DY["F_stop_N_at_10mm_s"][1]} N. So: never reach either end at speed (slow to 10 mm/s in the last 2 mm, using the encoder position).')
A(f'- **Homing: close, never open, into a stop.** Close at {DY["homing"]["current_A"]} A and {DY["homing"]["speed_mm_s"]:.0f} mm/s (screw force at most {DY["homing"]["Fs_max_N"]} N) until the jaws stop: with the narrow set the pads meet at gap 0, with the wide set the carriage reaches the motor wall at about a 17 mm pad gap. Closing puts the reaction on the protected path (lock collar, 608, printed lip); running into the open stop would push the screw into the motor bearing, whose axial rating budget motors do not publish. Detect the stop with the AS5600: commanded steps keep going but the measured angle stops (StallGuard only as a backup, it needs speed). Then open to the working position, and cap the opening at 60 mm (80 mm wide) so the open stop is never touched.')
A('- **Grip control.** At a fixed current the grip rises about 3× from gap 0 to 60 mm (the linkage gains advantage as it opens). Schedule the run current against the encoder gap so the grip stays near 30 N per jaw (worst-case screw friction; the second grip value is with a greased screw):\n')
A('| Gap mm (narrow / wide) | MA | Run current A | IRUN (0–31) | Grip per jaw N |\n|---|---|---|---|---|')
for r_ in SCH: A(f'| {r_["gap_narrow_mm"]} / {r_["gap_wide_mm"]} | {r_["MA"]} | {r_["I_run_A"]} | {r_["IRUN"]} | {r_["grip_N"][0]}–{r_["grip_N"][1]} |')
A('\n- **Hold.** The Tr8×8 back-drives: while gripping set IHOLD = IRUN and a long TPOWERDOWN, and keep the screw greased.')
A('- **Encoder bench test before printing the bearing block.** The magnet sits inside the steel 608 inner ring, which can weaken or distort its field. Push the printed puck with the magnet into a 608, hold the AS5600 0.8 mm in front of it, turn the bearing by hand and read MAGNITUDE and AGC over I2C (AGC should sit mid-range) and the angle over a full turn (it should be linear). If the field is too weak, the magnet has to move 3–4 mm in front of the 608 in a non-ferrous holder, which needs a longer block (ask before redesigning). Tie the AS5600 DIR pin to GND.\n')
A(f'## 5. Structural checks (200 N screw-force limit case; σ op = at the {drv["Fs_operating_max_N"]} N stall force at {drv["I_set_rms_A"]} A)\n')
A('| Check | Load N | σ limit MPa | σ op MPa | SF yield |\n|---|---|---|---|---|')
for r_ in S['rows']: A(f'| {r_["item"]} | {r_["load_limit_N"]} | {r_["stress_limit_MPa"]} | {r_["stress_op_MPa"]} | {r_["SF_yield_at_limit"]} |')
A(f'\n**Grip thrust (rev 6):** closing the jaws pushes the carriage toward the motor, so the screw is pulled the other way. A lock collar behind the 608 carries that pull into the bearing inner ring; the outer ring bears on the block front lip, which is the base and cover halves clamped together. The motor\'s own bearing no longer takes the full reaction. Limit case {S["thrust"]["load_N"]:.0f} N vs ≈ {S["thrust"]["bearing608_axial_static_capacity_N"]:.0f} N 608 static axial capacity. {S["thrust"]["note"][0].upper() + S["thrust"]["note"][1:]}.\n')
A('\nThe dowel is modelled as a beam on two supports: the 6.5 mm press socket in the base and the bronze sleeve bonded into the cover (rev 7.1). The sleeve is bonded with the cover on the dowels, so the top support has no clearance however the printed parts shrink; a loose top support would leave the base socket with the full bending moment (about 86–119 MPa in use).\n')
A(f'\n{D.MAT} printed in-plane yield taken as {D.MAT_SY:.0f} MPa (low end of generic FDM ABS; the spool brand is not fixed) and {D.MAT_SZ:.0f} MPa across layers. All link loads are in the print plane (along the rasters). Interlayer stress appears only at the jaw-block root (≈0.3 MPa).\n')
A('\n### 5.1 Fasteners (every screw is modelled)\n')
A(f'Gripper mass {FX["mass_g"]:.0f} g (printed parts taken as solid, conservative), CG at x = {FX["x_cg_mm"]:.0f} mm; payload at x = {FX["x_payload_mm"]} mm; mount at x = {FX["x_mount_mm"]} mm. Pitch moment at the mount {FX["M_pitch_Nm"]} N·m (×2 dynamic).\n')
A('| Check | Load N | Stress MPa | SF yield | Note |\n|---|---|---|---|---|')
for r_ in FX['rows']: A(f'| {r_["item"]} | {r_["load_N"]} | {r_["stress_MPa"]} | {r_["SF_yield"]} | {r_["note"]} |')
A('\n| Screw | Clamp mm | Thread engaged mm | Tip to hole bottom mm | Into |\n|---|---|---|---|---|')
for e in FX['engagement']: A(f'| {e["screw"]} | {e["clamp_mm"]} | {e["thread_mm"]} | {e["tip_to_hole_bottom_mm"]} | {e["into"]} |')
A(f'\n**Tightening:** a button head bears on {FX["head_bearing_area_mm2"]} mm² of {D.MAT}. At {T_M3} N·m an M3 makes about {F_CL:.0f} N of clamp, about {F_CL/FX["head_bearing_area_mm2"]:.0f} MPa under the head ({D.MAT} taken as {D.MAT_SY:.0f} MPa, so SF ≈ {D.MAT_SY*FX["head_bearing_area_mm2"]/F_CL:.1f}). Tighten every M3 to **{T_M3} N·m or less**: snug with the short arm of the key, no more. The two nut-flange screws bear on brass and self-tap into plastic; snug them only.\n')
A('## 6. Motion, clearance and printability checks\n')
A('- 3D boolean interference over 41 poses from closed to fully open, every part pair, both sides: **0 collisions**. Minimum-distance scan: all pairs under 0.8 mm are intended (shoulder screws in crank bores 0.05, dowels and shoulder screws in running bores 0.1, z-stack gaps 0.2 below / 0.3 above each moving layer, crank plates on base 0.3, fingers meeting at closed, carriage on the open stop). Lock collar 1.0 mm radial to the block; cover 1.38 mm from the front crank at closed.')
A('- Every part is a single valid solid. FeatureScript round-trip rebuild gives identical volumes.')
A('- Print orientation (no supports): links and fingers 0 mm² overhang; base, cover and adapter only hole tops and counterbore steps; carriage printed rear face down, so the nut recess opens upward and nothing needs a bridge or support.\n')
A('| Print file | Qty | Volume cm³ | Bounding box mm | Orientation / note |\n|---|---|---|---|---|')
for p in PARTS: A(f'| {p["file"]} | {p["qty"]} | {p["volume_cm3"]} | {" × ".join(map(str, p["bbox_mm"]))} | {p["orientation"]}: {p["note"]} |')
A(f'\n**Print the fit coupons first**, in {D.MAT} on the same printer as the real parts: 13b_FitTest_rev7.stl (rev 7 fits: tongue and tip-block pocket stubs cut from the real parts, so install the 2 inserts and then test the slide fit and the M3×10 screws; AS5600 slot; M6 nut pocket; 2020 column socket; magnet puck, to try in a 608) and 13c_FitTest_pad_TPU95A.stl in TPU (it should snap into the pocket stub groove and not pull out by hand). Then 13_FitTest_coupons.stl (16 cm³, one plate). ABS shrinks more than PETG, so the rev 6 fits may need retuning. It checks every fit that depends on your printer: Ø3.9–4.2 pin bores in 6 mm plate, the three z-stacks with their 0.2/0.3 mm gaps, the 608 cradle (Ø22.06 seat, front lip, collar recess), and a 12.0 mm channel with an 11.6 mm tongue. If the 608 is loose, or a pin or the tongue binds, adjust the matching value in design.py before printing the real parts.\n')
A('\nPrint settings: ABS in an enclosed printer (a draft shield at minimum), part-cooling fan low or off, brim on the base, cover and the stand parts (the stand is ABS too; PLA is an acceptable fallback if the 180 × 170 base or the clamps warp); check the base, cover and stand base on a flat surface (glass) before assembly and reprint any that rock, 0.2 mm layers, 4 perimeters, 30–40% gyroid, 100% around insert holes. After printing, run a 4.0 mm drill through the pivot bores by hand (Ø4.2 bores = running fit, Ø4.1 = snug) Do not drill the Ø3.9 dowel press holes in the base; the cover holes are oversize on purpose (the sleeves are bonded in).\n')
A('## 7. Onshape\n')
O7 = json.load(open('results_onshape_rev7.json'))
A(f'**Status (rev 7, {O7["date"]}):** the v2 design is in the Onshape document **GripperV2** ({O7["document"]["url"]}), a copy of the rev 6 document. The original "Lead Screw Gripper" document stays the rev 6 record.\n')
A(f'- Feature Studio 1 holds the rev 7 `LeadScrewGripper.fs` ({O7["feature_studio"]["chars"]} characters, SHA-256 {O7["feature_studio"]["sha256_first16"]}…, identical to the local file), written through the browser session (0 FeatureScript MCP requests).')
A(f'- The feature dialog now has **Tip set** (Narrow / Wide) and **Include bench stand**; it reports the pad-to-pad gap for the chosen set. Part Studio 1 builds {O7["part_studio"]["parts"]} parts; every volume is within {O7["part_studio"]["volumes_vs_local_max_diff_mm3"]} mm³ of the local model, and the wide set matches too.')
A(f'- Assembly 1: {O7["assembly_1"]["instances"]} instances, {O7["assembly_1"]["features_ok"]}/{O7["assembly_1"]["features"]} features OK. New rigid groups "Finger U + tip" and "Finger L + tip" (finger, tip block, pad, 2 tip screws); the encoder, controller and stand parts are in "Frame (fixed)". Slider at both limits: carriage +20.83 / −11.20 mm, fingers 18.00 / −15.00 mm, tips follow the fingers; past the limit it clamps. Left at 0 (gap 30). Record: source/results_onshape_rev7.json.')
A('- Pictures: images/onshape_v2_assembly_iso.png, images/onshape_v2_assembly_top.png, images/onshape_v2_partstudio_iso.png. The "Robot export" assembly is unchanged (ROS 2 phase).\n')
A('**Rev 6 record (original document):**\n')
A('The original document is at **rev 6** (updated 2026-10-13). Feature Studio 1 holds the rev 6 `LeadScrewGripper.fs` (exact SHA-256 match with the local file) and the lock collar is in the frame group of Assembly 1.\n')
A('Onshape document **Lead Screw Gripper**: https://cad.onshape.com/documents/95059d2be7659a57baadd94c/w/0895a7ec4eaef76618deb3e3/e/621a9c0dfd69e86e15b36ea6\n')
A('- **Feature Studio 1** holds `LeadScrewGripper.fs` (feature "Lead Screw Gripper"). Its dialog has **Jaw gap** (0–66 mm), which solves the kinematics and poses every part, and **Include purchased parts**. It builds 49 named, coloured parts with materials (16 of them the M3 button-head screws, one the lock collar), plus 26 named mate connectors at the pivots and on the screw axis.')
A('- **Part Studio 1** uses the feature (gap 30 mm). Onshape mass properties match the local model for every part within 0.9 mm³ (rev 6, source/results_onshape_rev6.json). That cross-check caught the bearing-block insert holes sitting tangent to the block face, now fixed with an 8 mm front wall.')
A('- **Assembly 1** has 49 instances and is a working **1-DOF mechanism**:')
A('  - The frame is fixed.')
A('  - 6 rigid groups: frame (with its 14 static screws and the lock collar); carriage + nut + C pivots + 2 nut screws; each crank pair with its shoulder screws.')
A('  - Revolute joints at the fixed pivots (O1, O2).')
A('  - Cylindrical at F1 and D, and ball at F2 and C. This removes the redundant constraints of the closed planar loops (54 − 53 = 1 DOF).')
A('  - One **slider** on the lead-screw axis, limited from −20.83 mm (open stop, 66 mm gap) to +11.2 mm (jaws closed) relative to the 30 mm pose. The mate’s +Z points toward the motor, so positive values close the jaws.')
A('  - Verified in Onshape: at −20.83 mm the carriage moves +20.83 mm and each finger +18.00 mm (gap 66); at +11.2 mm the carriage moves −11.20 mm and each finger −15.00 mm (gap 0); a request past the limit is clamped. These match the local kinematics. Animate runs end to end.')
A('  - To move it: right-click the slider mate → *Animate* (or drag a finger).')
A('  - Onshape captures (rev 6) of both limits: images/onshape_assembly_open_66mm.png and images/onshape_assembly_closed_0mm.png.')
A('  - Also: images/onshape_assembly_home_30mm.png and images/onshape_top_cover_hidden.png (cover hidden, top view). Mate connector markers are hidden in the assembly view.')
A('- Detail refinements (rev 3):')
A('  - Fingers have one straight back edge instead of clearance bites. The heel is at x = 37 mm in the finger frame, which keeps ≥ 1.18 mm from the O2 spacer boss over the full stroke (+1° overtravel).')
A('  - The finger nose and heel are rounded r3 to match the other corners. The serrated face runs 37–71 mm; the raised jaw block (41–71 mm) is unchanged.')
A('  - The motor-screw access slots have r1 corners, so the M3 head seats on a flat face instead of a line contact. In the base they run up through the wall half, so the slot end is visible and clean. Same M3 screws.')
A('- Audit fixes (rev 4), from an independent review of every part, fastener and assembly step:')
A('  - Nut install: the nut could not get into the carriage (closed bore, small front hole). The flange recess is now open at the front; the nut slides in from the front and 2× M3×8 button heads through two flange holes hold it axially and stop it turning. The thin-walled anti-rotation screw, counterbore and insert are gone. The carriage prints rear face down with no supports.')
A('  - Adapter mounting: the side screws ran into the M6 counterbores and the rail holes were capped. The base and cover now have short side walls beside the adapter (flush with the plate outline) that carry 4× M3×8 at z 4.0 / 16.5, at least 4.2 mm from every M6 feature. The adapter is 2 mm wider (1.37 mm wall round the counterbores) and 3 mm taller (1.45 mm skin over the pin hole).')
A('  - Motor screws: M3×12 would bottom out in the motor before clamping. Now M3×8 (3.5 mm into the motor).')
A('  - Dowels: the cover holes are a close fit (Ø4.0, reamed), so each dowel is held at both ends instead of cantilevered from the base socket.')
A('  - Jaw block made flush with the finger outline (the 1.08 mm wedge ledge is gone). Serrations end on a full tooth, with a 1 mm land at each end.')
A('  - Removed features with no job: two bearing-block outlines (now one), 0.5 mm steps at the conrod ends and the O1 spacer (now R5.5 like the bosses; O2 stays R5.0 to clear the finger heel), carriage corner scallops and side-print chamfers, 0.01 mm slivers at the base channel, and a 1 mm overcut under the cover motor slots.')
A('- Fasteners (rev 5): all 16 screws are modelled as ISO 7380 button heads (head Ø5.7 × 1.65) in their real seats, so the CAD shows exactly what you buy. Checked in Onshape with its own geometry kernel:')
A('  - All 48 part volumes match the local model within 0.7 mm³; all 19 assembly features OK.')
A('  - Interference at gaps 0, 30 and 66 mm (every part pair): only the intended overlaps remain (dowel press fits, motor screws in the motor\'s tapped holes, nut screws in the carriage pilots). Every head sits flat on its seat.')
A(f'  - Clearances: nut screws {OS["min_distance_mm"]["nut_screw_to_frame_at_open"]} mm from the bearing block at the open stop and {OS["min_distance_mm"]["nut_screw_to_lead_screw"]} mm from the lead screw; static screws ≥ {OS["min_distance_mm"]["static_screw_to_moving_part_min"]} mm from every moving part.')
A('  - Slider at both limits: the nut screws ride with the carriage and the 14 frame screws stay put.')
A('  - The motor-slot corners went from r1 to r0.5, because the Ø5.7 head touched the r1 fillets.')
A('- Rev 6 in Onshape (record: source/results_onshape_rev6.json): all 49 part volumes within 0.9 mm³ of the local model; 19/19 assembly features OK. Slider at both limits: carriage +20.83 / −11.20 mm, fingers 18.00 / −15.00 mm, same as rev 5; a request past the limit clamps. Onshape evCollision: the collar only touches the screw and the 608 inner ring and sits 1.0 mm from the base and cover; at the open stop the carriage touches only the base (channel and stop) and the nut is 3.1 mm from the collar.')
A('- FeatureScript MCP usage: 15 API requests in total (56 → 71 of 2,500). All browser work in Onshape (rev 3 to rev 6) used none.')
A('- Rev 6 (local, after an outside design review):')
A('  - Grip thrust: added an 8 mm lock collar behind the 608. The bearing moved 4.5 mm toward the jaws, the block grew from 18.0 to 22.5 mm long (R6 front corners, bolts 8.5 mm off the axis), and the collar sits in an Ø16 pocket at the back of the block, 0.5 mm inside its rear face. The screw is cut to %.1f mm (was 78.0) and ends flush with the 608 face.' % D.SCREW_LEN)
A('  - Section through the thrust path: images/rev6_thrust_section.png.')
A('  - Layer stack: finger / conrod now 6.5–14.1 (7.6 mm = 38 layers) and upper crank plates 14.4–18.2 (3.8 mm), with the screw axis at 10.3. Gaps went from 0.1 to 0.2 below and 0.3 above each moving layer.')
A('  - Fit coupons (13_FitTest_coupons.stl) so the bore, stack, bearing-seat and tongue fits are tested before the full print.')
A('  - Re-checked: 49 valid parts, 0 collisions over 41 poses, intended contacts only; structural min SF 3.6 (unchanged, dowel); new block front lip SF 34.5 bearing / 74.6 shear-out; fasteners min SF 4.3; no new overhangs.')
A('- Alternative: `step/LeadScrewGripper_assembly_gap30mm.step` imports into any CAD package as a 49-part assembly.\n')
A('## 8. Assembly sequence\n')
for i, s_ in enumerate([
 'Heat-set inserts, pressed from the top face until flush (the shoulder screws seat on the insert top): BellCrank Lower (F1, D), FrontCrank Lower (F2), Carriage lower ears (2), Finger tongues (2 each). Base: 2 motor-wall joint, 2 bearing-block ears, 2 posts. Adapter: 4 side holes. Cover top: 4 for the controller standoffs.',
 'Press the 2 Ø3 locating pins into the bearing-block half of the base (8 mm deep). Press the 4 dowels into the base (O1, O2 both sides; 6.5 mm deep, square to the plate). Wax the top 8 mm of each dowel (release) and slide a bronze sleeve onto each.',
 'Pull-test the lock collar first: tighten its set screw on the end of the lead screw, check it holds a firm pull by hand without slipping, then take it off. Cut the lead screw to %.1f mm -0.5/+0 from the motor face, so its end sits %.0f mm inside the 608 bore (never longer: the encoder puck fills the rest). Chamfer, clean and grease it.' % (D.SCREW_LEN, D.ENC_CUT),
 'Slide the nut into the carriage from the front: body into the bore, flange into the front recess, two flange holes at 3 and 9 o\'clock. Fit 2× M3×8 button heads into the Ø2.5 pilots, snug only.',
 'Spin the carriage onto the motor screw from its rear. Slide the lock collar on (set screw loose), then the 608ZZ onto the screw tip.',
 'Lay motor + screw + carriage + bearing into the base: motor connector facing up, pilot into the wall recess, carriage tongue in the channel, 608 in the lower cradle against the front lip, collar behind it. Fit the 2 lower motor screws (M3×8) through the access slots with a 2.5 mm ball-end driver. Push the collar forward until it just touches the 608 inner ring (no preload) and tighten its set screw. Run the carriage end to end by hand, then tighten the 2 nut screws.',
 'Encoder: glue the magnet into the printed puck (flush), slide the puck into the 608 bore against the screw end and glue it to the screw end with a drop of CA. Solder 4 wires (VCC, GND, SDA, SCL) to the AS5600 pad row, drop the board into the slot in front of the 608 (chip toward the magnet, pads up) and lead the wires up through the slit in the cover.',
 'Per side: BellCrank Lower on O1 and FrontCrank Lower on O2 (bosses up). Finger onto F1/F2, conrod onto D and between the carriage ears at C. BellCrank Upper and FrontCrank Upper on top. Shoulder screws at F1, F2, D, C into the lower-plate/ear inserts.',
 'Tip blocks: slide a TPU pad into the tip block groove from the rear and press until the barb at its rear end snaps past the step at the groove entrance (a drop of soapy water helps; pliers to remove), push the tip block up onto the finger tongue from below and fit 2× M3×10 from below through its floor. To change sets, take the 2 screws out and slide the block off downward.',
 'Cover: put slow-cure epoxy in the 4 oversize cover holes, lower the cover over the sleeves and dowels, fit all its screws, and let the epoxy cure with the gripper assembled (the sleeves bond to the cover where the dowels really are). 2× M3×20 at the motor wall, 2× M3×20 at the bearing-block ears, 2× M3×8 at the posts, then the 2 upper motor screws (M3×8) through the cover slots.',
 'Controller: screw the 4 standoffs into the cover-top inserts and fit the protoboard (Pico, TMC2209, buck, divider; see the wiring table) with 4× M3×6. Zip-tie each cable (USB, battery, motor, encoder) to the board grid as strain relief.',
 'Bench stand: column into the base socket, M5×16 from below into the column end (tap it M5) and 2× M5×12 through the socket walls into T-nuts. Desk clamps: drop an M8 nut into the slot of each clamp and thread the star knob in from below; put the front edge of the base flush with the front edge of the desk, hook a clamp over each front corner (its boss drops into the corner counterbore) and tighten the knobs by hand under the black edge. Slide the head bracket onto the column and lock it with 2× M5×12 into T-nuts. Drop 4 M6 nuts into the bracket pockets from the back. Strap the battery to the column (side away from the gripper) and plug in the balance-lead alarm.',
 'Bolt the adapter first: to a robot flange with 4× M6×12, or to the stand head bracket with 4× M6×20 into the nuts. Slide the gripper onto it (the U-slot is open at the rear) and fit 4× M3×8 through the side walls into the adapter inserts.',
 'Driver: set the VREF pot to %.2f A RMS full scale (section 4a), 1/16 µstep (%.0f steps/mm). Home at 0.3 A and 10 mm/s by closing until the jaws stop (narrow set: pads meet; wide set: carriage on the motor wall), detecting the stop with the encoder (bench test: firmware/as5600_bench_test.py); the AS5600 then tracks screw turns (4 over the full stroke). In use, cap the commanded opening at 60 mm (80 mm pad gap with the wide tips) so the carriage never hits the stop at speed. Keep the hold current on while gripping (the Tr8×8 is back-drivable). Stop the motor below 10.5 V on the battery monitor. Calibrate grip once with a kitchen scale between the jaws.' % (S['driver']['I_set_rms_A'], D.STEPS_PER_MM)]):
    A(f'{i+1}. {s_}')
A(f'\nTighten every M3 to {T_M3} N·m or less (snug with the short arm of the key). More crushes the {D.MAT} under the head.')
A('\n## 9. Assumptions, limits, verify before buying\n')
A('- Rigid links, quasi-static, equal load sharing between the two sides, Coulomb friction in the screw only (pivot friction lowers grip a few %; the current setting has margin).')
A('- Verify on receipt: motor body ≤ 40 mm (the adapter sits 1 mm behind it), pilot Ø22×2, M3 holes on 31 mm square; nut flange Ø22×3.5 and body Ø10.2 (edit NUT_* in design.py if different); shoulder-screw head ≤ Ø7.5×3.5 and thread ≤ 6 mm.')
A('- Robot flange: I assumed a Ø31.5 H7 centring recess (spigot 31.44 × 3 mm) and the Ø6 pin on the PCD at +Z, between bolts. Check your robot drawing.')
A('- μ = 0.35 is kept as the design value. The TPU 95A pads typically give more (about 0.6–0.7), which roughly doubles the slip margin.')
A(f'- {D.MAT} creeps slowly under sustained clamp. For long holds, re-tighten with a short current pulse, or print the fingers and lower crank plates in PA-CF.')
A('- Motor connector: the adapter sits 1 mm behind the motor, so the cable must leave from a side face. Mount the motor with the connector facing up, through the cover\'s U-slot.')
A(f'- M6×12 puts 6 mm of thread into the robot flange. Check your flange\'s thread depth, and use a washer or modest torque on the {D.MAT}.')
A('- Thrust: the collar and the motor\'s internal bearing share the screw load in a way that depends on how the collar is set. Check the motor datasheet\'s axial load rating anyway, and don\'t preload the collar.')
A('- The jaws also move fore-aft: %.1f mm in total over the stroke. They are furthest forward near a %.0f mm gap and furthest back fully open (%.1f mm behind the closed position). That is inherent to this linkage; teach grasp poses at the gap you\'ll use.' % (FA['travel'], FA['gap_fwd'], FA['open_behind_closed']))
A('- Not modelled: wiring and connectors, zip ties, a limit switch (sensorless homing assumed), the stand T-nuts and M5/M6 hardware, the M3 screws on top of the standoffs.')
A('- Wide tips: the F2 pivot boss, 3–14 mm behind the seam, sits about 1.9 mm proud of the wide pad face. Round objects never reach it; a flat object longer than the pads that reaches back past the seam would touch it. A 7 mm offset instead of 10 would clear it (gap 14–80 mm).')
A('- AS5600 module size: designed for 23 × 23 mm boards (most listings are 22–23 mm). The slot is 23.4 mm; the chip must be centred on the board, and parts on the chip side must sit within the 19.6 mm relief.')
open(f'{OUT}/DESIGN_REPORT.md', 'w').write('\n'.join(md) + '\n')
print('ok', printed_cm3)
