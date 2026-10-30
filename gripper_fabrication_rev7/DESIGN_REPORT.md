# Lead-Screw Parallel Gripper: Design & Validation Report

Generated from the verified model (design.py → results.json, results_struct.json). All numbers below come from those files.

## 1. Summary

| Item | Value |
|---|---|
| Mechanism | Reference architecture kept: parallelogram finger (pure translation) + 90° bell crank + conrod to lead-screw carriage, 1 DOF, mirrored |
| Jaw range | narrow tips 0 → 60.5 mm, wide tips 20 → 80.5 mm (pad to pad; firmware caps the opening at 60 / 80 mm) |
| Carriage stroke | 26.5 mm = 3.3 screw turns (Tr8×8, 400 steps/mm at 1/16 µstep) |
| Grip force per jaw | ≥ 26.0 N anywhere in range at 0.7 A RMS, worst-case screw friction (needs 21.0 N for 500 g) |
| Holding | Tr8×8 is back-drivable (lead angle 20.0°): the driver hold current keeps the grip; with power off the jaws can be pushed open |
| Structure | Min safety factor 1.0 vs yield at a 200 N screw-force limit case (the motor clamps at 75–107 N at 0.7 A). Grip-driven rows assume a far-tip grip at the 66 mm stop; in use (stall at 0.7 A, 60 mm cap, 80.2 N per jaw) they are 1.94× higher: min SF 1.9 in use |
| Motion check | 0 collisions over 41 poses (95 parts with the stand and electronics, 24 modelled screws), for both tip sets; only intended joint/stack contacts below 0.8 mm |
| Grip thrust | Screw reaction → lock collar → 608 inner ring → outer ring → block front lip. 608 static axial capacity ≈ 685 N vs 200 N limit (3.4×) |
| Fasteners | 4 button-head sizes on the gripper (14× M3×8, 8× M3×10, 4× M3×20, ISO 7380); min SF 2.8 under mount, stall and limit loads; tighten ≤ 0.15 N·m |
| Printed volume | gripper with the narrow set 497 cm³ (~284 g at typical infill) + motor ~280 g; wide set 20 cm³; bench stand 395 cm³ |
| Mount | ISO 9409-1-50-4-M6 adapter (PCD 50, 4×M6, Ø31.5 spigot, Ø6 pin) |

## 1a. Rev 7 (v2) changes

- **Rev 7.2b (2026-10-26), compact controller and flush dowels:** the protoboard is cut to 48 × 60 mm and sits on 4 mm spacers, the 7805 lies flat, the 100 µF stands beside the driver, and the two Pico-end mounting screws sit between the Pico's socket rows. The electronics cover shrinks from 57.5 × 78 × 33.6 to 54 × 66 × 26.2 mm (envelope 151 → 93 cm³, −38%); the driver's heatsink is now the tallest part. The 4 × 40 dowels are cut to 38.5 mm and pressed up through the base, flush with its underside and the cover top, with 9 mm of press fit (was 6.5).
- **Rev 7.2 finishing pass (2026-10-26):** the open hard stop moved from 66 to 60.5 mm, just past the 60 mm firmware cap: the last 6 mm were never used, and there the linkage advantage, and so every pin load in the 200 N limit case, climbs steeply. The finger bores at F1 and F2 (twist from a pad-edge grip) now pass that limit case (SF 1.0, was 0.6, bore-only model), the gripper is 5.5 mm of stroke shorter at the front and the lead screw is cut to 73.0 mm. Fillets in the desk clamps' inside corners (R3 / R6) and a stepped fillet round the stand column socket, a 0.4 mm elephant's-foot relief on the carriage tongue's bed side, and a printed electronics cover (Electronics cover x1) over the controller with cable notches, a BOOTSEL window and driver vents, held by 2 M3×8 into 2 more cover-top inserts. The Pico and driver now sit at their real socketed height (11 mm above the board). In Onshape the button-head screws are Onshape standard ISO 7380 parts and the Pico is Raspberry Pi's official model.
- **B, tip sets:** each finger splits at x = 41 mm. A tip block slides up onto a 15 mm tongue on the finger and takes 2× M3×10 from below. Block and pad are centred on the pin plane, so a normal grip does not twist the finger. Narrow set: pad face on the rev 6 face line (gap 0–66 mm). Wide set: pad face 10 mm further out per side (20–86 mm), blunt end. Both run 12 mm further forward (pad x 44–83). The same 2 mm TPU 95A pad fits both (dovetail key, slides in from the rear and snaps past a step, so it cannot slide back out). The heel is trimmed, so the O2-spacer clearance grew from 1.18 to 1.90 mm.
- **Trade-offs of the longer tips:** the gripper is 12 mm longer. Gripping at the far end of the pad raises the F2/O2 pin loads by about 17% over gripping at the far end of the rev 6 jaw, and by about 75% over the rev 6 check basis (a grip near the jaw root). The 200 N limit rows below use the worst point on the pad.
- **C, encoder:** AS5600 with a 6 × 2.5 mm diametric magnet in a printed puck at the screw end (screw cut 3 mm shorter). The board stands in a slot across the bearing block, 0.8 mm air gap; the block bolts moved to ears at the rear of the block.
- **D, controller:** Pico + TMC2209 (in sockets), 7805, motor-power divider, 100 µF and the USB-C trigger board on a 48 × 60 mm protoboard (7805 and 100 µF lying flat), on 4 printed 4 mm spacers over heat-set inserts in the cover top. Runs on its own from the power bank (demo mode: the Pico BOOTSEL button opens and closes the jaws); USB serial to ROS 2 when a laptop is plugged in.
- **A, drive:** Tr8×8 (lead 8 mm): 3.3 turns over the stroke, 400 steps/mm, 300 rpm max on the 9 V supply -> 40 mm/s -> full stroke 0.7 s. Driver 0.7 A RMS. Not self-locking.
- **F, bench stand:** the gripper hangs jaws-down from a 2020 × 400 mm column: printed head bracket on the ISO 9409 adapter, printed 180 × 170 mm base, clamped to the desk edge by 2 printed C-clamps with M8 star knobs (sized for a 40 mm edge, 24–49 mm range); unclamped, a few newtons at gripper height would tip it over. The power bank sits on the desk next to the base. Slide the bracket to set the height.
- **Power:** USB-C PD power bank → 9 V trigger board → TMC2209 VM, the motor-power divider and a 7805 that feeds the Pico VSYS through a 1N5817, so one cable runs everything and the laptop is optional (USB can be plugged in at the same time). 9 V is offered by every PD bank and by USB-C laptop and phone chargers of 18 W and up, so any of them works. The bank protects itself and cuts out when empty; firmware disables the driver when the divider shows the 9 V is gone (9 V reads 1.91 V). Many banks switch off below about 50–100 mA: the driver stays enabled at hold current while powered (the back-drivable screw needs it to hold a grip anyway), which keeps the bank awake.
- **Material:** printed parts in ABS (taken as 30 MPa); pads in TPU 95A.

| Pico pin | Connects to |
|---|---|
| GP2 | TMC2209 STEP |
| GP3 | TMC2209 DIR |
| GP4 | TMC2209 EN |
| GP5 | TMC2209 DIAG (stall detect for homing) |
| GP8 / GP9 (UART1) | TMC2209 PDN_UART (1 k in series on TX) |
| GP0 / GP1 (I2C0) | AS5600 SDA / SCL |
| GP26 (ADC0) | Motor-power divider 100 k / 27 k (9 V reads 1.91 V) |
| 3V3 / GND | AS5600 VCC / GND (DIR to GND), TMC2209 VIO / GND; 10 k from TMC2209 EN to VIO |
| VSYS | 7805 output through the 1N5817 (USB can be connected at the same time) |

## 2. Mechanism and dimensions

Reference measured from the video (143 frames, hole centres tracked; rigid distances constant to <1 px). Link ratios kept exactly, scaled to crank length L = 28 mm.

| Parameter | Value (mm / deg) | Ratio to L |
|---|---|---|
| Crank length L (O1–F1 = O2–F2) | 28.00 | 1.0000 |
| Ground link O1–O2 | 43.98 | 1.5708 |
| Bell-crank arm O1–D (90° to O1–F1) | 20.91 | 0.7468 |
| Conrod C–D | 22.68 | 0.8098 |
| Carriage pin line Y_C | 24.91 | 0.8898 |
| Fixed pivot O1 Y | 50.97 | 1.8204 |
| O1 → O2 direction | −42.80° | |
| Crank angle range | -15.5° (jaws touch) → 54.4° (open stop) | |

**Architecture change vs reference (engineering reason):** every pivot is double-shear. Fixed pivots O1/O2 are hardened 4 mm dowels held by the base AND the cover; each crank is two plates (lower plate with spacer boss + upper plate) acting as a clevis around the finger and conrod; the carriage has upper and lower ears around the conrod. Single-ended 4 mm pins in printed plastic would see roughly 80–200 MPa of local bearing stress from pin bending at these loads.

**Layer stack (z = 0 at base-plate top):** base −9…0 · lower crank plates 0.3…6.3 · finger / conrod 6.5…14.1 · upper crank plates 14.4…18.2 · shoulder-screw heads ≤ 21.3 · cover 22.1…29.5 · screw axis 10.3 (= conrod mid-plane, so rod forces line up with the nut). Jaw block extends to z = 26. Moving layers have 0.2 mm below and 0.3 mm above them (rev 6), so first-layer squish and top-surface bulge do not bind the stack.

## 3. Kinematics and force transmission

- No toggle or singularity in the window: ds/dθ 18.6–25.3 mm/rad; transmission angle 59.4°–89.9°; rod ≤ 38° to the screw axis.
- Mechanical advantage (grip per jaw ÷ total screw force): 0.345 at 0 mm, 0.752 at 60 mm, 0.776 at 66 mm. Grip rises as the jaws open.
- Cross-checks: analytic vs finite-difference ds/dθ 5.2e-06; virtual work vs free-body statics 4e-16; inverse solve 4e-13 rad.
- Grip requirement: 500 g, μ = 0.35 (printed serrations), ×2 dynamic, ×1.5 slip SF → 21.0 N per jaw; target 25 N.

Jaw gap ↔ carriage position (for firmware; home = open stop, 400 steps/mm at 1/16 µstep; the AS5600 also counts screw turns, 8 mm per turn):

| Gap mm (narrow) | Crank θ° | C_x mm | Carriage from open stop mm | Steps from home | Gap mm (wide) |
|---|---|---|---|---|---|
| 0 | -15.5 | -27.49 | -26.55 | 10619 | 20.0 |
| 6 | -9.2 | -25.37 | -24.43 | 9773 | 26.0 |
| 12 | -3.1 | -23.19 | -22.25 | 8900 | 32.0 |
| 18 | 3.1 | -20.95 | -20.01 | 8004 | 38.0 |
| 24 | 9.3 | -18.65 | -17.71 | 7085 | 44.0 |
| 30 | 15.6 | -16.28 | -15.34 | 6138 | 50.0 |
| 36 | 22.0 | -13.82 | -12.88 | 5153 | 56.0 |
| 42 | 28.8 | -11.23 | -10.29 | 4114 | 62.0 |
| 48 | 36.1 | -8.41 | -7.47 | 2989 | 68.0 |
| 54 | 44.2 | -5.23 | -4.29 | 1716 | 74.0 |
| 60 | 53.5 | -1.32 | -0.38 | 153 | 80.0 |
| 60.5 | 54.4 | -0.94 | 0.0 | 0 | 80.5 |

## 4. Motor and driver sizing

- Screw force for ≥ 25 N everywhere: 72.4 N → torque 0.123–0.174 N·m (screw η 0.53–0.75).
- **Set driver current to 0.7 A RMS** (for a 1.7 A / 0.44 N·m motor): screw force 75.3–106.6 N → grip ≥ 26.0 N per jaw, and stays below the 200 N structural limit even with a well-greased screw.
- **Warning:** at full rated current the motor can push ~259 N, far above what the printed parts are sized for. The current limit is a safety item.
- Speed: 300 rpm max on the 9 V supply -> 40 mm/s -> full stroke 0.7 s. The Tr8×8 is not self-locking, so keep the hold current on while gripping (TMC2209 IHOLD); the AS5600 confirms the position after any slip.


### 4a. Drive safety and grip control (rev 7.1)

- **Driver current ceiling in hardware.** Set the TMC2209 VREF pot so its full-scale current is 0.7 A RMS and enable `GCONF.i_scale_analog`, so UART can only lower the current. The driver resets to its pot setting whenever its motor supply comes back (power bank unplugged and plugged back in), while the Pico stays alive on USB: put a 10 k pull-up from EN to VIO (driver off while the Pico boots), and in firmware read GSTAT/IFCNT before every move and re-send the configuration after a reset.
- **Hard stops.** The rotor (about 65 g·cm², assumed) looks like 4.01 kg at the carriage through the 8 mm lead. Running into a stop at 300 rpm (top speed on 9 V) adds about 80–253 N of screw force; at 10 mm/s only 20–63 N. So: never reach either end at speed (slow to 10 mm/s in the last 2 mm, using the encoder position).
- **Homing: close, never open, into a stop.** Close at 0.3 A and 10 mm/s (screw force at most 45.7 N) until the jaws stop: with the narrow set the pads meet at gap 0, with the wide set the carriage reaches the motor wall at about a 17 mm pad gap. Closing puts the reaction on the protected path (lock collar, 608, printed lip); running into the open stop would push the screw into the motor bearing, whose axial rating budget motors do not publish. Detect the stop with the AS5600: commanded steps keep going but the measured angle stops (StallGuard only as a backup, it needs speed). Then open to the working position, and cap the opening at 60 mm (80 mm wide) so the open stop is never touched.
- **Grip control.** At a fixed current the grip rises about 3× from gap 0 to 60 mm (the linkage gains advantage as it opens). Schedule the run current against the encoder gap so the grip stays near 30 N per jaw (worst-case screw friction; the second grip value is with a greased screw):

| Gap mm (narrow / wide) | MA | Run current A | IRUN (0–31) | Grip per jaw N |
|---|---|---|---|---|
| 0 / 20 | 0.345 | 0.7 | 31 | 26.0–36.8 |
| 10 / 30 | 0.365 | 0.7 | 31 | 27.5–39.0 |
| 20 / 40 | 0.381 | 0.7 | 31 | 28.7–40.7 |
| 30 / 50 | 0.401 | 0.69 | 31 | 30.0–42.5 |
| 40 / 60 | 0.437 | 0.64 | 28 | 30.0–42.5 |
| 50 / 70 | 0.516 | 0.54 | 24 | 30.0–42.5 |
| 60 / 80 | 0.752 | 0.37 | 16 | 30.0–42.5 |

- **Hold.** The Tr8×8 back-drives: while gripping set IHOLD = IRUN and a long TPOWERDOWN, and keep the screw greased.
- **Encoder bench test before printing the bearing block.** The magnet sits inside the steel 608 inner ring, which can weaken or distort its field. Push the printed puck with the magnet into a 608, hold the AS5600 0.8 mm in front of it, turn the bearing by hand and read MAGNITUDE and AGC over I2C (AGC should sit mid-range) and the angle over a full turn (it should be linear). If the field is too weak, the magnet has to move 3–4 mm in front of the 608 in a non-ferrous holder, which needs a longer block (ask before redesigning). Tie the AS5600 DIR pin to GND.

## 5. Structural checks (200 N screw-force limit case; σ op = at the 106.6 N stall force at 0.7 A)

| Check | Load N | σ limit MPa | σ op MPa | SF yield |
|---|---|---|---|---|
| Shoulder screw Ø4 double shear (304 stainless) | 392.3 | 15.61 | 8.32 | 16.7 |
| Dowel Ø4 bending, simply supported base↔cover | 295.3 | 346.08 | 184.46 | 3.5 |
| Finger bore at F2 on shoulder (7.6 mm) | 295.3 | 9.71 | 5.18 | 3.1 |
| Finger bore at F1 (7.6 mm) | 310.1 | 10.2 | 5.44 | 2.9 |
| FrontCrank bores at O2 (6.0+3.8 plates + 8.1 spacer) | 295.3 | 4.12 | 2.2 | 7.3 |
| Base dowel press hole (54% share, 9.0 mm) | 295.3 | 4.39 | 2.34 | 6.8 |
| Cover hole on the bonded sleeve (46% share, Ø6 x 6) | 295.3 | 3.81 | 2.03 | 7.9 |
| ConRod bores (7.6 mm) | 126.4 | 4.16 | 2.22 | 7.2 |
| Carriage ears at C (6.3 + 3.8 mm) | 126.4 | 3.13 | 1.67 | 9.6 |
| Finger boss tear-out at F2 | 295.3 | 5.71 | 3.05 | 3.1 |
| FrontCrank (two-force) net section | 295.3 | 4.43 | 2.36 | 6.8 |
| ConRod (two-force) net section | 126.4 | 2.87 | 1.53 | 10.5 |
| BellCrank bending near O1 (two plates) | 310.1 | 9.75 | 5.19 | 3.1 |
| Finger body at the tip seam (23.8 mm deep x 7.6) | 155.3 | 9.12 | 4.86 | 3.3 |
| Tongue root bending at the seam (16.3 deep x 13.6) | 155.3 | 10.9 | 5.81 | 2.8 |
| Tongue flank bearing in the tip block pocket (15 mm long) | 652.2 | 6.42 | 3.42 | 4.7 |
| Tip block wall, interlayer shear at z = 6.5 (wide set, 2.53 mm wall) | 47.4 | 0.45 | 0.24 | 16.1 |
| Tongue torsion, grip on the pad edge (9.75 mm off the pin plane) | 155.3 | 2.44 | 1.3 | 3.0 |
| Finger bore at F2, far-tip grip on the pad edge | 295.3 | 29.37 | 15.66 | 1.0 |
| Finger bore at F1, far-tip grip on the pad edge | 310.1 | 29.86 | 15.92 | 1.0 |
| Block front lip bearing on 608 outer ring | 200.0 | 1.31 | 0.7 | 23.0 |
| Block front lip shear-out (1.45 mm lip) | 200.0 | 2.0 | 1.06 | 9.0 |
| Desk clamp spine bending (30 x 14, hand-tight 400 N) | 400.0 | 11.22 | 5.98 | 2.7 |
| Desk clamp lower arm at the spine (30 x 12) | 400.0 | 11.39 | 6.07 | 2.6 |

**Grip thrust (rev 6):** closing the jaws pushes the carriage toward the motor, so the screw is pulled the other way. A lock collar behind the 608 carries that pull into the bearing inner ring; the outer ring bears on the block front lip, which is the base and cover halves clamped together. The motor's own bearing no longer takes the full reaction. Limit case 200 N vs ≈ 685 N 608 static axial capacity. Collar set-screw holding on the threaded screw is not rated: verify with a hand pull test before assembly.


The dowel is modelled as a beam on two supports: the 6.5 mm press socket in the base and the bronze sleeve bonded into the cover (rev 7.1). The sleeve is bonded with the cover on the dowels, so the top support has no clearance however the printed parts shrink; a loose top support would leave the base socket with the full bending moment (about 86–119 MPa in use).


ABS printed in-plane yield taken as 30 MPa (low end of generic FDM ABS; the spool brand is not fixed) and 12 MPa across layers. All link loads are in the print plane (along the rasters). Interlayer stress appears only at the jaw-block root (≈0.3 MPa).


### 5.1 Fasteners (every screw is modelled)

Gripper mass 755 g (printed parts taken as solid, conservative), CG at x = -25 mm; payload at x = 89.0 mm; mount at x = -98.5 mm. Pitch moment at the mount 2.93 N·m (×2 dynamic).

| Check | Load N | Stress MPa | SF yield | Note |
|---|---|---|---|---|
| Side screw M3x8, shank shear (mount, x2 dynamic) | 123.4 | 24.53 | 15.1 | 8.8 steel; ignores clamp friction |
| Side wall hole bearing, 3.8 mm wall (mount) | 123.4 | 10.82 | 2.8 | base/cover side wall |
| Adapter insert bearing in ABS (mount) | 123.4 | 4.71 | 6.4 | insert OD 4.6 x 5.7 mm |
| Motor screw head on ABS (open-stop stall, tension) | 26.6 | 1.62 | 18.5 | 4 screws share the stall force |
| Nut screw pull-out, self-tapped 4.4 mm (open-stop stall) | 53.3 | 1.54 | 11.3 | shear at the D2.5 pilot wall |
| Nut screw head on brass flange | 53.3 | 3.24 | 61.7 | CuZn yield ~200 MPa |
| Cover screw bearing in cover (200 N limit case) | 88.6 | 7.03 | 4.3 | all four dowel reactions on 6 screws |

| Screw | Clamp mm | Thread engaged mm | Tip to hole bottom mm | Into |
|---|---|---|---|---|
| Motor M3x8 | 4.5 | 3.5 | 1.0 | motor tapped hole, ~4.5 deep |
| Cover to wall/block M3x20 | 16.0 | 4.0 | 2.5 | insert 5.7 (hole 6.5) |
| Cover to post M3x8 | 4.2 | 3.8 | 2.7 | insert 5.7 (hole 6.5) |
| Side wall to adapter M3x8 | 4.0 | 4.0 | 2.5 | insert 5.7 (hole 6.5) |
| Nut flange M3x8 | 3.6 | 4.4 | 2.6 | self-tapped D2.5 pilot, 7 deep |
| Tip block to tongue M3x10 (from below) | 4.15 | 5.85 | 0.65 | insert 5.7 in the tongue underside (hole 6.5) |

**Tightening:** a button head bears on 16.4 mm² of ABS. At 0.15 N·m an M3 makes about 250 N of clamp, about 15 MPa under the head (ABS taken as 30 MPa, so SF ≈ 2.0). Tighten every M3 to **0.15 N·m or less**: snug with the short arm of the key, no more. The two nut-flange screws bear on brass and self-tap into plastic; snug them only.

## 6. Motion, clearance and printability checks

- 3D boolean interference over 41 poses from closed to fully open, every part pair, both sides: **0 collisions**. Minimum-distance scan: all pairs under 0.8 mm are intended (shoulder screws in crank bores 0.05, dowels and shoulder screws in running bores 0.1, z-stack gaps 0.2 below / 0.3 above each moving layer, crank plates on base 0.3, fingers meeting at closed, carriage on the open stop). Lock collar 1.0 mm radial to the block; cover 1.38 mm from the front crank at closed.
- Every part is a single valid solid. FeatureScript round-trip rebuild gives identical volumes.
- Print orientation (no supports): links and fingers 0 mm² overhang; base, cover and adapter only hole tops and counterbore steps; carriage printed rear face down, so the nut recess opens upward and nothing needs a bridge or support.

| Print file | Qty | Volume cm³ | Bounding box mm | Orientation / note |
|---|---|---|---|---|
| Base x1.stl | 1 | 107.17 | 145.3 × 130.9 × 31.1 | flat: bottom face on bed; 4 walls, 30% gyroid |
| Cover x1.stl | 1 | 90.33 | 145.3 × 130.9 × 19.2 | flip_x: flat top face on bed |
| Adapter ISO9409-50 x1.stl | 1 | 37.95 | 59.0 × 48.6 × 17.0 | front_down: gripper-side face on bed, spigot up |
| Carriage x1.stl | 1 | 20.16 | 27.8 × 60.8 × 26.0 | rear_down: rear face on bed, nut recess up; no supports; 100% infill around inserts and nut-screw pilots |
| BellCrank Lower U x1.stl | 1 | 5.52 | 39.0 × 31.9 × 14.1 | flat: spacer boss up |
| BellCrank Lower L x1.stl | 1 | 5.52 | 39.0 × 31.9 × 14.1 | flat: mirror of BellCrank Lower U (other side) |
| BellCrank Upper U+L x2.stl | 2 | 3.07 | 39.0 × 31.9 × 3.8 | flat: same part both sides (flip one) |
| FrontCrank Lower U+L x2.stl | 2 | 2.78 | 39.0 × 11.0 × 14.1 | flat: spacer boss up |
| FrontCrank Upper U+L x2.stl | 2 | 1.43 | 39.0 × 11.0 × 3.8 | flat:  |
| ConRod U+L x2.stl | 2 | 2.41 | 33.7 × 11.0 × 7.6 | flat:  |
| Finger U x1.stl | 1 | 10.19 | 61.5 × 40.9 × 13.6 | flat: tongue forward; M layer only since rev 7 |
| Finger L x1.stl | 1 | 10.19 | 61.5 × 40.9 × 13.6 | flat: mirror of Finger U |
| Fit test gripper x1.stl | 1 | 23.47 | 131.9 × 33.3 × 19.5 | flat: print FIRST (rev 7 fits): tongue stub + tip-block pocket stub (install the 2 inserts, then test the slide fit and the M3x10 screws), AS5600 slot (1.6 mm board), M6 nut pocket, 2020 column socket, magnet puck (try it in a 608); not part of the gripper |
| Fit test pad x1.stl | 1 | 0.71 | 15.5 × 19.5 × 3.4 | face_down: print FIRST in TPU 95A: pad stub with the snap barb, for the pocket stub groove (it should snap in and not pull out by hand) |
| Tip block U narrow x1.stl | 1 | 16.1 | 45.0 × 33.3 × 19.5 | flat: narrow set; floor down, tongue pocket opens upward |
| Tip block L narrow x1.stl | 1 | 16.1 | 45.0 × 33.3 × 19.5 | flat: mirror of Tip block U narrow |
| Tip block U wide x1.stl | 1 | 10.13 | 45.0 × 23.3 × 19.5 | flat: wide set; floor down, tongue pocket opens upward |
| Tip block L wide x1.stl | 1 | 10.13 | 45.0 × 23.3 × 19.5 | flat: mirror of Tip block U wide |
| Pad TPU U+L x4.stl | 4 | 1.71 | 38.0 × 19.5 × 3.4 | side_py_down: TPU 95A, contact face on bed; 2 per tip set (same pad fits both) |
| Encoder magnet puck x1.stl | 1 | 0.07 | 7.9 × 7.9 × 2.9 | rear_down: magnet pocket up; glue to the screw end |
| Stand head bracket x1.stl | 1 | 137.36 | 103.8 × 52.0 × 30.0 | rear_down: bench stand; back face on bed, nut pockets and column hole open upward |
| Stand base x1.stl | 1 | 257.41 | 170.0 × 180.0 × 28.0 | front_down: bench stand; table face on bed, column socket up |
| Stand desk clamp U x1.stl | 1 | 52.58 | 83.0 × 54.5 × 30.0 | side_my_down: desk clamp; lying on its side, nut slot up, 100% infill at the corners |
| Stand desk clamp L x1.stl | 1 | 52.58 | 83.0 × 54.5 × 30.0 | side_py_down: mirror of Stand desk clamp U |
| Stand clamp pad U+L x2.stl | 2 | 2.54 | 24.0 × 24.0 × 6.0 | rear_down: desk side down; felt on it is optional |
| Controller spacer rear+front U+L x4.stl | 4 | 0.06 | 5.5 × 5.5 × 4.0 | flat: end on bed, 100% infill; 4 mm tall, replaces the brass standoffs (M3 x 10 through board and spacer into the cover insert) |
| Electronics cover x1.stl | 1 | 16.62 | 54.0 × 83.0 × 26.2 | flip_x: top face on bed, no supports; 2 M3 x 8 into the cover-top inserts |

**Print the fit coupons first**, in ABS on the same printer as the real parts: Fit test gripper x1.stl (rev 7 fits: tongue and tip-block pocket stubs cut from the real parts, so install the 2 inserts and then test the slide fit and the M3×10 screws; AS5600 slot; M6 nut pocket; 2020 column socket; magnet puck, to try in a 608) and Fit test pad x1.stl in TPU (it should snap into the pocket stub groove and not pull out by hand). Then Fit test coupons x1.stl (16 cm³, one plate). ABS shrinks more than PETG, so the rev 6 fits may need retuning. It checks every fit that depends on your printer: Ø3.9–4.2 pin bores in 6 mm plate, the three z-stacks with their 0.2/0.3 mm gaps, the 608 cradle (Ø22.06 seat, front lip, collar recess), and a 12.0 mm channel with an 11.6 mm tongue. If the 608 is loose, or a pin or the tongue binds, adjust the matching value in design.py before printing the real parts.


Print settings: ABS in an enclosed printer (a draft shield at minimum), part-cooling fan low or off, brim on the base, cover and the stand parts (the stand is ABS too; PLA is an acceptable fallback if the 180 × 170 base or the clamps warp); check the base, cover and stand base on a flat surface (glass) before assembly and reprint any that rock, 0.2 mm layers, 4 perimeters, 30–40% gyroid, 100% around insert holes. After printing, run a 4.0 mm drill through the pivot bores by hand (Ø4.2 bores = running fit, Ø4.1 = snug) Do not drill the Ø3.9 dowel press holes in the base; the cover holes are oversize on purpose (the sleeves are bonded in).

## 7. Onshape

**Status (rev 7, 2026-10-26 (rev 7.2b: compact controller, flush dowels)):** the v2 design is in the Onshape document **GripperV2** (https://cad.onshape.com/documents/21eb00e5286d05130362fe39), a copy of the rev 6 document. The original "Lead Screw Gripper" document stays the rev 6 record.

- Feature Studio 1 holds the rev 7.2 `LeadScrewGripper.fs` (48058 characters, SHA-256 7806dea110f8299a…, identical to the local file), written through the browser session (0 FeatureScript MCP requests).
- The feature dialog now has **Tip set** (Narrow / Wide) and **Include bench stand**; it reports the pad-to-pad gap for the chosen set. Part Studio 1 builds 97 parts; every volume is within 0.7 mm³ of the local model, and the wide set matches too.
- Assembly 1: 97 instances, 21/21 features OK. New rigid groups "Finger U + tip" and "Finger L + tip" (finger, tip block, pad, 2 tip screws); the encoder, controller and stand parts are in "Frame (fixed)". Slider at both limits: carriage +15.34 / −11.20 mm, fingers 15.25 / −15.00 mm, tips and their screws follow the fingers; past the limit it clamps. Left at 0 (gap 30). The 26 button heads are Onshape standard content (ISO 7380 M3, configured from Onshape's own size table), placed exactly where the modelled screws sit and grouped with the part they hold; the Pico is Raspberry Pi's official model (Pico-R3.step, in the sub-assembly "Pico (official model)"). The simplified screws and Pico stay in Part Studio 1 for the local checks. Record: source/results_onshape_rev7.json.
- Pictures: images/onshape_v2_assembly_iso.png, images/onshape_v2_assembly_top.png, images/onshape_v2_assembly_front.png, images/onshape_v2_partstudio_iso.png. The "Robot export" assembly is unchanged (ROS 2 phase).

**Rev 6 record (original document):**

The original document is at **rev 6** (updated 2026-10-13). Feature Studio 1 holds the rev 6 `LeadScrewGripper.fs` (exact SHA-256 match with the local file) and the lock collar is in the frame group of Assembly 1.

Onshape document **Lead Screw Gripper**: https://cad.onshape.com/documents/95059d2be7659a57baadd94c/w/0895a7ec4eaef76618deb3e3/e/621a9c0dfd69e86e15b36ea6

- **Feature Studio 1** holds `LeadScrewGripper.fs` (feature "Lead Screw Gripper"). Its dialog has **Jaw gap** (0–66 mm), which solves the kinematics and poses every part, and **Include purchased parts**. It builds 49 named, coloured parts with materials (16 of them the M3 button-head screws, one the lock collar), plus 26 named mate connectors at the pivots and on the screw axis.
- **Part Studio 1** uses the feature (gap 30 mm). Onshape mass properties match the local model for every part within 0.9 mm³ (rev 6, source/results_onshape_rev6.json). That cross-check caught the bearing-block insert holes sitting tangent to the block face, now fixed with an 8 mm front wall.
- **Assembly 1** has 49 instances and is a working **1-DOF mechanism**:
  - The frame is fixed.
  - 6 rigid groups: frame (with its 14 static screws and the lock collar); carriage + nut + C pivots + 2 nut screws; each crank pair with its shoulder screws.
  - Revolute joints at the fixed pivots (O1, O2).
  - Cylindrical at F1 and D, and ball at F2 and C. This removes the redundant constraints of the closed planar loops (54 − 53 = 1 DOF).
  - One **slider** on the lead-screw axis, limited from −20.83 mm (open stop, 66 mm gap) to +11.2 mm (jaws closed) relative to the 30 mm pose. The mate’s +Z points toward the motor, so positive values close the jaws.
  - Verified in Onshape: at −20.83 mm the carriage moves +20.83 mm and each finger +18.00 mm (gap 66); at +11.2 mm the carriage moves −11.20 mm and each finger −15.00 mm (gap 0); a request past the limit is clamped. These match the local kinematics. Animate runs end to end.
  - To move it: right-click the slider mate → *Animate* (or drag a finger).
  - Onshape captures (rev 6) of both limits: images/onshape_assembly_open_66mm.png and images/onshape_assembly_closed_0mm.png.
  - Also: images/onshape_assembly_home_30mm.png and images/onshape_top_cover_hidden.png (cover hidden, top view). Mate connector markers are hidden in the assembly view.
- Detail refinements (rev 3):
  - Fingers have one straight back edge instead of clearance bites. The heel is at x = 37 mm in the finger frame, which keeps ≥ 1.18 mm from the O2 spacer boss over the full stroke (+1° overtravel).
  - The finger nose and heel are rounded r3 to match the other corners. The serrated face runs 37–71 mm; the raised jaw block (41–71 mm) is unchanged.
  - The motor-screw access slots have r1 corners, so the M3 head seats on a flat face instead of a line contact. In the base they run up through the wall half, so the slot end is visible and clean. Same M3 screws.
- Audit fixes (rev 4), from an independent review of every part, fastener and assembly step:
  - Nut install: the nut could not get into the carriage (closed bore, small front hole). The flange recess is now open at the front; the nut slides in from the front and 2× M3×8 button heads through two flange holes hold it axially and stop it turning. The thin-walled anti-rotation screw, counterbore and insert are gone. The carriage prints rear face down with no supports.
  - Adapter mounting: the side screws ran into the M6 counterbores and the rail holes were capped. The base and cover now have short side walls beside the adapter (flush with the plate outline) that carry 4× M3×8 at z 4.0 / 16.5, at least 4.2 mm from every M6 feature. The adapter is 2 mm wider (1.37 mm wall round the counterbores) and 3 mm taller (1.45 mm skin over the pin hole).
  - Motor screws: M3×12 would bottom out in the motor before clamping. Now M3×8 (3.5 mm into the motor).
  - Dowels: the cover holes are a close fit (Ø4.0, reamed), so each dowel is held at both ends instead of cantilevered from the base socket.
  - Jaw block made flush with the finger outline (the 1.08 mm wedge ledge is gone). Serrations end on a full tooth, with a 1 mm land at each end.
  - Removed features with no job: two bearing-block outlines (now one), 0.5 mm steps at the conrod ends and the O1 spacer (now R5.5 like the bosses; O2 stays R5.0 to clear the finger heel), carriage corner scallops and side-print chamfers, 0.01 mm slivers at the base channel, and a 1 mm overcut under the cover motor slots.
- Fasteners (rev 5): all 16 screws are modelled as ISO 7380 button heads (head Ø5.7 × 1.65) in their real seats, so the CAD shows exactly what you buy. Checked in Onshape with its own geometry kernel:
  - All 48 part volumes match the local model within 0.7 mm³; all 19 assembly features OK.
  - Interference at gaps 0, 30 and 66 mm (every part pair): only the intended overlaps remain (dowel press fits, motor screws in the motor's tapped holes, nut screws in the carriage pilots). Every head sits flat on its seat.
  - Clearances: nut screws 0.95 mm from the bearing block at the open stop and 1.15 mm from the lead screw; static screws ≥ 3.38 mm from every moving part.
  - Slider at both limits: the nut screws ride with the carriage and the 14 frame screws stay put.
  - The motor-slot corners went from r1 to r0.5, because the Ø5.7 head touched the r1 fillets.
- Rev 6 in Onshape (record: source/results_onshape_rev6.json): all 49 part volumes within 0.9 mm³ of the local model; 19/19 assembly features OK. Slider at both limits: carriage +20.83 / −11.20 mm, fingers 18.00 / −15.00 mm, same as rev 5; a request past the limit clamps. Onshape evCollision: the collar only touches the screw and the 608 inner ring and sits 1.0 mm from the base and cover; at the open stop the carriage touches only the base (channel and stop) and the nut is 3.1 mm from the collar.
- FeatureScript MCP usage: 15 API requests in total (56 → 71 of 2,500). All browser work in Onshape (rev 3 to rev 6) used none.
- Rev 6 (local, after an outside design review):
  - Grip thrust: added an 8 mm lock collar behind the 608. The bearing moved 4.5 mm toward the jaws, the block grew from 18.0 to 22.5 mm long (R6 front corners, bolts 8.5 mm off the axis), and the collar sits in an Ø16 pocket at the back of the block, 0.5 mm inside its rear face. The screw is cut to 73.0 mm (was 78.0) and ends flush with the 608 face.
  - Section through the thrust path: images/rev6_thrust_section.png.
  - Layer stack: finger / conrod now 6.5–14.1 (7.6 mm = 38 layers) and upper crank plates 14.4–18.2 (3.8 mm), with the screw axis at 10.3. Gaps went from 0.1 to 0.2 below and 0.3 above each moving layer.
  - Fit coupons (Fit test coupons x1.stl) so the bore, stack, bearing-seat and tongue fits are tested before the full print.
  - Re-checked: 49 valid parts, 0 collisions over 41 poses, intended contacts only; structural min SF 3.6 (unchanged, dowel); new block front lip SF 34.5 bearing / 74.6 shear-out; fasteners min SF 4.3; no new overhangs.
- Alternative: `step/LeadScrewGripper_assembly_gap30mm.step` imports into any CAD package as a 49-part assembly.

## 8. Assembly sequence

1. Heat-set inserts, pressed from the top face until flush (the shoulder screws seat on the insert top): BellCrank Lower (F1, D), FrontCrank Lower (F2), Carriage lower ears (2), Finger tongues (2 each). Base: 2 motor-wall joint, 2 bearing-block ears, 2 posts. Adapter: 4 side holes. Cover top: 4 for the controller spacers, 2 for the electronics cover. 28 inserts in all.
2. Screw the 2 locating pins (M3×16 with the heads cut off) into the bearing-block half of the base (8 mm deep). Cut the 4 dowels to 38.5 mm and press them up through the base from underneath (O1, O2 both sides; flush with the underside, square to the plate). Wax or grease the top 8 mm of each dowel (release) and slide a bronze sleeve onto each.
3. Pull-test the lock collar first: tighten its set screw on the end of the lead screw, check it holds a firm pull by hand without slipping, then take it off. Cut the lead screw to 73.0 mm -0.5/+0 from the motor face, so its end sits 3 mm inside the 608 bore (never longer: the encoder puck fills the rest). Chamfer, clean and grease it.
4. Slide the nut into the carriage from the front: body into the bore, flange into the front recess, two flange holes at 3 and 9 o'clock. Fit 2× M3×8 button heads into the Ø2.5 pilots, snug only.
5. Spin the carriage onto the motor screw from its rear. Slide the lock collar on (set screw loose), then the 608ZZ onto the screw tip.
6. Lay motor + screw + carriage + bearing into the base: motor connector facing up, pilot into the wall recess, carriage tongue in the channel, 608 in the lower cradle against the front lip, collar behind it. Fit the 2 lower motor screws (M3×8) through the access slots with a 2.5 mm ball-end driver. Push the collar forward until it just touches the 608 inner ring (no preload) and tighten its set screw. Run the carriage end to end by hand, then tighten the 2 nut screws.
7. Encoder: glue the magnet into the printed puck (flush), slide the puck into the 608 bore against the screw end and glue it to the screw end with a drop of CA. Solder 4 wires (VCC, GND, SDA, SCL) to the AS5600 pad row, drop the board into the slot in front of the 608 (chip toward the magnet, pads up) and lead the wires up through the slit in the cover.
8. Per side: BellCrank Lower on O1 and FrontCrank Lower on O2 (bosses up). Finger onto F1/F2, conrod onto D and between the carriage ears at C. BellCrank Upper and FrontCrank Upper on top. Shoulder screws at F1, F2, D, C into the lower-plate/ear inserts.
9. Tip blocks: slide a TPU pad into the tip block groove from the rear and press until the barb at its rear end snaps past the step at the groove entrance (a drop of soapy water helps; pliers to remove), push the tip block up onto the finger tongue from below and fit 2× M3×10 from below through its floor. To change sets, take the 2 screws out and slide the block off downward.
10. Cover: put slow-cure epoxy in the 4 oversize cover holes, lower the cover over the sleeves and dowels, fit all its screws, and let the epoxy cure with the gripper assembled (the sleeves bond to the cover where the dowels really are). 2× M3×20 at the motor wall, 2× M3×20 at the bearing-block ears, 2× M3×8 at the posts, then the 2 upper motor screws (M3×8) through the cover slots.
11. Controller: solder the female headers (Pico 2 × 20, TMC2209 2 × 8), the 7805, diode and divider to the protoboard (see the wiring table) and plug in the Pico and TMC2209, set it on the 4 printed spacers and screw it down with 4× M3×10 into the cover-top inserts. Zip-tie each cable (USB, power, motor, encoder) to the board grid as strain relief. Put the electronics cover over it (cables through the rim notches) and fit 2× M3×8 through its flanges into the cover-top inserts.
12. Bench stand: column into the base socket, M5×12 from below into the column end (tap it M5; skip this screw if there is no M5 tap) and 2× M5×12 through the socket walls into T-nuts. Desk clamps: drop an M8 nut into the slot of each clamp and thread the star knob in from below; put the front edge of the base flush with the front edge of the desk, hook a clamp over each front corner (its boss drops into the corner counterbore) and tighten the knobs by hand under the black edge. Slide the head bracket onto the column and lock it with 2× M5×12 into T-nuts. Drop 4 M6 nuts into the bracket pockets from the back. Put the power bank on the desk beside the base.
13. Bolt the adapter first: to a robot flange with 4× M6×12, or to the stand head bracket with 4× M6×20 into the nuts. Slide the gripper onto it (the U-slot is open at the rear) and fit 4× M3×8 through the side walls into the adapter inserts.
14. Driver: set the VREF pot to 0.70 A RMS full scale (section 4a), 1/16 µstep (400 steps/mm). Home at 0.3 A and 10 mm/s by closing until the jaws stop (narrow set: pads meet; wide set: carriage on the motor wall), detecting the stop with the encoder (bench test: firmware/as5600_bench_test.py); the AS5600 then tracks screw turns (4 over the full stroke). In use, cap the commanded opening at 60 mm (80 mm pad gap with the wide tips) so the carriage never hits the stop at speed. Keep the hold current on while gripping (the Tr8×8 is back-drivable). The driver turns off when the 9 V supply drops. Power-up tests, homing, grip and a stand-alone demo: firmware/bench.py, step by step in docs/BUILD_AND_TEST_GUIDE.md.

Tighten every M3 to 0.15 N·m or less (snug with the short arm of the key). More crushes the ABS under the head.

## 9. Assumptions, limits, verify before buying

- Rigid links, quasi-static, equal load sharing between the two sides, Coulomb friction in the screw only (pivot friction lowers grip a few %; the current setting has margin).
- Verify on receipt: motor body ≤ 40 mm (the YEJMKJ is 38.7 mm, so the adapter sits 2.3 mm behind it), pilot Ø22×2, M3 holes on 31 mm square; nut flange Ø22×3.5 and body Ø10.2 (edit NUT_* in design.py if different); shoulder-screw head ≤ Ø7.5×3.5 and thread ≤ 6 mm.
- Robot flange: I assumed a Ø31.5 H7 centring recess (spigot 31.44 × 3 mm) and the Ø6 pin on the PCD at +Z, between bolts. Check your robot drawing.
- μ = 0.35 is kept as the design value. The TPU 95A pads typically give more (about 0.6–0.7), which roughly doubles the slip margin.
- ABS creeps slowly under sustained clamp. For long holds, re-tighten with a short current pulse, or print the fingers and lower crank plates in PA-CF.
- Motor connector: the adapter sits 2.3 mm behind the motor, so the cable must leave from a side face. Mount the motor with the connector facing up, through the cover's U-slot.
- M6×12 puts 6 mm of thread into the robot flange. Check your flange's thread depth, and use a washer or modest torque on the ABS.
- Thrust: the collar and the motor's internal bearing share the screw load in a way that depends on how the collar is set. Check the motor datasheet's axial load rating anyway, and don't preload the collar.
- The jaws also move fore-aft: 11.7 mm in total over the stroke. They are furthest forward near a 15 mm gap and furthest back fully open (10.7 mm behind the closed position). That is inherent to this linkage; teach grasp poses at the gap you'll use.
- The model shows what is bought (2026-10-25): YEJMKJ motor (38.7 mm body), 4 × 40 dowels, headless M3 screws as block locating pins, printed controller spacers with their M3×16 screws, header sockets, 7805, 100 µF capacitor, USB-C trigger board, and the power bank on the desk.
- Not modelled: wiring and the USB-C cable, the 1N5817, resistors and small capacitors, heat-set inserts, zip ties, the stand T-nuts and M5/M6 hardware.
- Wide tips: the F2 pivot boss, 3–14 mm behind the seam, sits about 1.9 mm proud of the wide pad face. Round objects never reach it; a flat object longer than the pads that reaches back past the seam would touch it. A 7 mm offset instead of 10 would clear it (gap 14–80 mm).
- AS5600 module size: designed for 23 × 23 mm boards (most listings are 22–23 mm). The slot is 23.4 mm; the chip must be centred on the board, and parts on the chip side must sit within the 19.6 mm relief.
