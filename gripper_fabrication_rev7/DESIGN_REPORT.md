# Lead-Screw Parallel Gripper: Design & Validation Report

Generated from the verified model (design.py → results.json, results_struct.json). All numbers below come from those files.

## 1. Summary

| Item | Value |
|---|---|
| Mechanism | Reference architecture kept: parallelogram finger (pure translation) + 90° bell crank + conrod to lead-screw carriage, 1 DOF, mirrored |
| Jaw range | narrow tips 0 → 66 mm, wide tips 20 → 86 mm (pad to pad; firmware caps the opening at 60 / 80 mm) |
| Carriage stroke | 32.0 mm = 4.0 screw turns (Tr8×8, 400 steps/mm at 1/16 µstep) |
| Grip force per jaw | ≥ 26.8 N anywhere in range at 0.7 A RMS, worst-case screw friction (needs 21.0 N for 500 g) |
| Holding | Tr8×8 is back-drivable (lead angle 20.0°): the driver hold current keeps the grip; with power off the jaws can be pushed open |
| Structure | Min safety factor 0.6 vs yield at a 200 N screw-force limit case (the motor clamps at 78–110 N at 0.7 A). Grip-driven rows assume a far-tip grip at the 66 mm stop; in use (stall at 0.7 A, 60 mm cap, 82.6 N per jaw) they are 3.3× higher: min SF 2.0 in use |
| Motion check | 0 collisions over 41 poses (78 parts with the stand and electronics, 20 modelled screws), for both tip sets; only intended joint/stack contacts below 0.8 mm |
| Grip thrust | Screw reaction → lock collar → 608 inner ring → outer ring → block front lip. 608 static axial capacity ≈ 685 N vs 200 N limit (3.4×) |
| Fasteners | 3 screw sizes on the gripper (12× M3×8, 4× M3×10, 4× M3×20 button head); min SF 2.3 under mount, stall and limit loads; tighten ≤ 0.15 N·m |
| Printed volume | gripper with the narrow set 370 cm³ (~211 g at typical infill) + motor ~280 g; wide set 20 cm³; bench stand 394 cm³ |
| Mount | ISO 9409-1-50-4-M6 adapter (PCD 50, 4×M6, Ø31.5 spigot, Ø6 pin) |

## 1a. Rev 7 (v2) changes

- **B, tip sets:** each finger splits at x = 41 mm. A tip block slides up onto a 15 mm tongue on the finger and takes 2× M3×10 from below. Block and pad are centred on the pin plane, so a normal grip does not twist the finger. Narrow set: pad face on the rev 6 face line (gap 0–66 mm). Wide set: pad face 10 mm further out per side (20–86 mm), blunt end. Both run 12 mm further forward (pad x 44–83). The same 2 mm TPU 95A pad fits both (dovetail key, slides in from the rear and snaps past a step, so it cannot slide back out). The heel is trimmed, so the O2-spacer clearance grew from 1.18 to 1.90 mm.
- **Trade-offs of the longer tips:** the gripper is 12 mm longer. Gripping at the far end of the pad raises the F2/O2 pin loads by about 17% over gripping at the far end of the rev 6 jaw, and by about 75% over the rev 6 check basis (a grip near the jaw root). The 200 N limit rows below use the worst point on the pad.
- **C, encoder:** AS5600 with a 6 × 2.5 mm diametric magnet in a printed puck at the screw end (screw cut 3 mm shorter). The board stands in a slot across the bearing block, 0.8 mm air gap; the block bolts moved to ears at the rear of the block.
- **D, controller:** Pico + TMC2209 + 5 V buck + battery divider on a 50 × 70 mm protoboard, on 4 standoffs in heat-set inserts in the cover top. USB serial to ROS 2.
- **A, drive:** Tr8×8 (lead 8 mm): 4.0 turns over the stroke, 400 steps/mm, 600 rpm -> 80 mm/s -> full stroke 0.4 s. Driver 0.7 A RMS. Not self-locking.
- **F, bench stand:** the gripper hangs jaws-down from a 2020 × 400 mm column: printed head bracket on the ISO 9409 adapter, printed 180 × 170 mm base with 4 holes to fix it to the bench (fix it: unclamped, a few newtons at gripper height tip it over). The battery is strapped to the column, away from the jaws. Slide the bracket to set the height.
- **Power:** 3S LiPo (about 650 mAh, XT30) → 3 A fuse → switch → TMC2209 VM and the buck → Schottky → Pico VSYS. The battery divider sits after the switch (no drain when off). Firmware stops the motor below 10.5 V; a balance-lead alarm warns before the cells go too low, and the switch must be turned off after use (the Pico and buck still draw current).
- **Material:** printed parts in ABS (taken as 30 MPa); pads in TPU 95A.

| Pico pin | Connects to |
|---|---|
| GP2 | TMC2209 STEP |
| GP3 | TMC2209 DIR |
| GP4 | TMC2209 EN |
| GP5 | TMC2209 DIAG (stall detect for homing) |
| GP8 / GP9 (UART1) | TMC2209 PDN_UART (1 k in series on TX) |
| GP0 / GP1 (I2C0) | AS5600 SDA / SCL |
| GP26 (ADC0) | Battery divider 100 k / 27 k (12.6 V reads 2.68 V) |
| 3V3 / GND | AS5600 VCC / GND, TMC2209 VIO / GND |
| VSYS | 5 V buck output through the 1N5817 |

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
| Crank angle range | -15.5° (jaws touch) → 65.6° (open stop) | |

**Architecture change vs reference (engineering reason):** every pivot is double-shear. Fixed pivots O1/O2 are hardened 4 mm dowels held by the base AND the cover; each crank is two plates (lower plate with spacer boss + upper plate) acting as a clevis around the finger and conrod; the carriage has upper and lower ears around the conrod. Single-ended 4 mm pins in printed plastic would see roughly 80–200 MPa of local bearing stress from pin bending at these loads.

**Layer stack (z = 0 at base-plate top):** base −9…0 · lower crank plates 0.3…6.3 · finger / conrod 6.5…14.1 · upper crank plates 14.4…18.2 · shoulder-screw heads ≤ 21.3 · cover 22.1…29.5 · screw axis 10.3 (= conrod mid-plane, so rod forces line up with the nut). Jaw block extends to z = 26. Moving layers have 0.2 mm below and 0.3 mm above them (rev 6), so first-layer squish and top-surface bulge do not bind the stack.

## 3. Kinematics and force transmission

- No toggle or singularity in the window: ds/dθ 18.6–31.5 mm/rad; transmission angle 59.4°–90.0°; rod ≤ 50° to the screw axis.
- Mechanical advantage (grip per jaw ÷ total screw force): 0.345 at 0 mm, 0.752 at 60 mm, 1.365 at 66 mm. Grip rises as the jaws open.
- Cross-checks: analytic vs finite-difference ds/dθ 2.1e-05; virtual work vs free-body statics 9e-16; inverse solve 5e-13 rad.
- Grip requirement: 500 g, μ = 0.35 (printed serrations), ×2 dynamic, ×1.5 slip SF → 21.0 N per jaw; target 25 N.

Jaw gap ↔ carriage position (for firmware; home = open stop, 400 steps/mm at 1/16 µstep; the AS5600 also counts screw turns, 8 mm per turn):

| Gap mm (narrow) | Crank θ° | C_x mm | Carriage from open stop mm | Steps from home | Gap mm (wide) |
|---|---|---|---|---|---|
| 0 | -15.5 | -27.49 | -32.03 | 12814 | 20.0 |
| 6 | -9.2 | -25.37 | -29.92 | 11968 | 26.0 |
| 12 | -3.1 | -23.19 | -27.74 | 11095 | 32.0 |
| 18 | 3.1 | -20.95 | -25.5 | 10199 | 38.0 |
| 24 | 9.3 | -18.65 | -23.2 | 9280 | 44.0 |
| 30 | 15.6 | -16.28 | -20.83 | 8333 | 50.0 |
| 36 | 22.0 | -13.82 | -18.37 | 7348 | 56.0 |
| 42 | 28.8 | -11.23 | -15.77 | 6309 | 62.0 |
| 48 | 36.1 | -8.41 | -12.96 | 5184 | 68.0 |
| 54 | 44.2 | -5.23 | -9.78 | 3911 | 74.0 |
| 60 | 53.5 | -1.32 | -5.87 | 2348 | 80.0 |
| 66 | 65.6 | 4.55 | 0.0 | 0 | 86.0 |

## 4. Motor and driver sizing

- Screw force for ≥ 25 N everywhere: 72.4 N → torque 0.123–0.174 N·m (screw η 0.53–0.75).
- **Set driver current to 0.7 A RMS** (for a 1.5 A / 0.4 N·m motor): screw force 77.6–109.8 N → grip ≥ 26.8 N per jaw, and stays below the 200 N structural limit even with a well-greased screw.
- **Warning:** at full rated current the motor can push ~235 N, far above what the printed parts are sized for. The current limit is a safety item.
- Speed: 600 rpm -> 80 mm/s -> full stroke 0.4 s. The Tr8×8 is not self-locking, so keep the hold current on while gripping (TMC2209 IHOLD); the AS5600 confirms the position after any slip.

## 5. Structural checks (200 N screw-force limit case; σ op = at the 109.8 N stall force at 0.7 A)

| Check | Load N | σ limit MPa | σ op MPa | SF yield |
|---|---|---|---|---|
| Shoulder screw Ø4 double shear (12.9 steel) | 543.0 | 21.61 | 11.87 | 46.3 |
| Dowel Ø4 bending, simply supported base↔cover | 543.0 | 604.0 | 331.69 | 2.0 |
| Finger bore at F2 on shoulder (7.6 mm) | 543.0 | 17.86 | 9.81 | 1.7 |
| Finger bore at F1 (7.6 mm) | 315.2 | 10.37 | 5.69 | 2.9 |
| FrontCrank bores at O2 (6.0+3.8 plates + 8.1 spacer) | 543.0 | 7.58 | 4.16 | 4.0 |
| Base dowel press hole (56% share, 6.5 mm) | 543.0 | 11.68 | 6.41 | 2.6 |
| Cover hole on the bonded sleeve (44% share, Ø6 x 6) | 543.0 | 6.65 | 3.65 | 4.5 |
| ConRod bores (7.6 mm) | 156.4 | 5.14 | 2.82 | 5.8 |
| Carriage ears at C (6.3 + 3.8 mm) | 156.4 | 3.87 | 2.13 | 7.8 |
| Finger boss tear-out at F2 | 543.0 | 10.51 | 5.77 | 1.7 |
| FrontCrank (two-force) net section | 543.0 | 8.15 | 4.47 | 3.7 |
| ConRod (two-force) net section | 156.4 | 3.55 | 1.95 | 8.5 |
| BellCrank bending near O1 (two plates) | 315.2 | 9.9 | 5.44 | 3.0 |
| Finger body at the tip seam (23.8 mm deep x 7.6) | 273.0 | 16.04 | 8.81 | 1.9 |
| Tongue root bending at the seam (16.3 deep x 13.6) | 273.0 | 19.16 | 10.52 | 1.6 |
| Tongue flank bearing in the tip block pocket (15 mm long) | 1146.5 | 11.28 | 6.2 | 2.7 |
| Tip block wall, interlayer shear at z = 6.5 (wide set, 2.53 mm wall) | 83.3 | 0.78 | 0.43 | 9.2 |
| Tongue torsion, grip on the pad edge (9.75 mm off the pin plane) | 273.0 | 4.28 | 2.35 | 1.7 |
| Finger bore at F2, far-tip grip on the pad edge | 543.0 | 52.42 | 28.79 | 0.6 |
| Block front lip bearing on 608 outer ring | 200.0 | 1.31 | 0.72 | 23.0 |
| Block front lip shear-out (1.45 mm lip) | 200.0 | 2.0 | 1.1 | 9.0 |

**Grip thrust (rev 6):** closing the jaws pushes the carriage toward the motor, so the screw is pulled the other way. A lock collar behind the 608 carries that pull into the bearing inner ring; the outer ring bears on the block front lip, which is the base and cover halves clamped together. The motor's own bearing no longer takes the full reaction. Limit case 200 N vs ≈ 685 N 608 static axial capacity. Collar set-screw holding on the threaded screw is not rated: verify with a hand pull test before assembly.


The dowel is modelled as a beam on two supports: the 6.5 mm press socket in the base and the bronze sleeve bonded into the cover (rev 7.1). The sleeve is bonded with the cover on the dowels, so the top support has no clearance however the printed parts shrink; a loose top support would leave the base socket with the full bending moment (about 86–119 MPa in use).


ABS printed in-plane yield taken as 30 MPa (low end of generic FDM ABS; the spool brand is not fixed) and 12 MPa across layers. All link loads are in the print plane (along the rasters). Interlayer stress appears only at the jaw-block root (≈0.3 MPa).


### 5.1 Fasteners (every screw is modelled)

Gripper mass 731 g (printed parts taken as solid, conservative), CG at x = -26 mm; payload at x = 89.0 mm; mount at x = -98.5 mm. Pitch moment at the mount 2.88 N·m (×2 dynamic).

| Check | Load N | Stress MPa | SF yield | Note |
|---|---|---|---|---|
| Side screw M3x8, shank shear (mount, x2 dynamic) | 121.4 | 24.13 | 15.4 | 8.8 steel; ignores clamp friction |
| Side wall hole bearing, 3.8 mm wall (mount) | 121.4 | 10.65 | 2.8 | base/cover side wall |
| Adapter insert bearing in ABS (mount) | 121.4 | 4.63 | 6.5 | insert OD 4.6 x 5.7 mm |
| Motor screw head on ABS (open-stop stall, tension) | 27.4 | 1.67 | 18.0 | 4 screws share the stall force |
| Nut screw pull-out, self-tapped 4.4 mm (open-stop stall) | 54.9 | 1.59 | 11.0 | shear at the D2.5 pilot wall |
| Nut screw head on brass flange | 54.9 | 3.34 | 59.9 | CuZn yield ~200 MPa |
| Cover screw bearing in cover (200 N limit case) | 162.9 | 12.93 | 2.3 | all four dowel reactions on 6 screws |

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
| 01_Base.stl | 1 | 106.86 | 145.3 × 130.9 × 31.1 | flat: bottom face on bed; 4 walls, 30% gyroid |
| 02_Cover.stl | 1 | 90.49 | 145.3 × 130.9 × 19.2 | flip_x: flat top face on bed |
| 03_Adapter_ISO9409-50-4-M6.stl | 1 | 37.95 | 59.0 × 48.6 × 17.0 | front_down: gripper-side face on bed, spigot up |
| 04_Carriage.stl | 1 | 20.16 | 27.8 × 60.8 × 26.0 | rear_down: rear face on bed, nut recess up; no supports; 100% infill around inserts and nut-screw pilots |
| 05_BellCrank_Lower_A.stl | 1 | 5.52 | 39.0 × 31.9 × 14.1 | flat: spacer boss up |
| 06_BellCrank_Lower_B_mirrored.stl | 1 | 5.52 | 39.0 × 31.9 × 14.1 | flat: mirror of 05 (other side) |
| 07_BellCrank_Upper.stl | 2 | 3.07 | 39.0 × 31.9 × 3.8 | flat: same part both sides (flip one) |
| 08_FrontCrank_Lower.stl | 2 | 2.78 | 39.0 × 11.0 × 14.1 | flat: spacer boss up |
| 09_FrontCrank_Upper.stl | 2 | 1.43 | 39.0 × 11.0 × 3.8 | flat:  |
| 10_ConRod.stl | 2 | 2.41 | 33.7 × 11.0 × 7.6 | flat:  |
| 11_Finger_A.stl | 1 | 10.19 | 61.5 × 40.9 × 13.6 | flat: tongue forward; M layer only since rev 7 |
| 12_Finger_B_mirrored.stl | 1 | 10.19 | 61.5 × 40.9 × 13.6 | flat: mirror of 11 |
| 13b_FitTest_rev7.stl | 1 | 23.47 | 131.9 × 33.3 × 19.5 | flat: print FIRST (rev 7 fits): tongue stub + tip-block pocket stub (install the 2 inserts, then test the slide fit and the M3x10 screws), AS5600 slot (1.6 mm board), M6 nut pocket, 2020 column socket, magnet puck (try it in a 608); not part of the gripper |
| 13c_FitTest_pad_TPU95A.stl | 1 | 0.71 | 15.5 × 19.5 × 3.4 | face_down: print FIRST in TPU 95A: pad stub with the snap barb, for the pocket stub groove (it should snap in and not pull out by hand) |
| 14_TipBlock_Narrow_A.stl | 1 | 16.1 | 45.0 × 33.3 × 19.5 | flat: narrow set; floor down, tongue pocket opens upward |
| 15_TipBlock_Narrow_B_mirrored.stl | 1 | 16.1 | 45.0 × 33.3 × 19.5 | flat: mirror of 14 |
| 16_TipBlock_Wide_A.stl | 1 | 10.13 | 45.0 × 23.3 × 19.5 | flat: wide set; floor down, tongue pocket opens upward |
| 17_TipBlock_Wide_B_mirrored.stl | 1 | 10.13 | 45.0 × 23.3 × 19.5 | flat: mirror of 16 |
| 18_Pad_TPU95A.stl | 4 | 1.71 | 38.0 × 19.5 × 3.4 | side_py_down: TPU 95A, contact face on bed; 2 per tip set (same pad fits both) |
| 19_EncoderPuck.stl | 1 | 0.07 | 7.9 × 7.9 × 2.9 | rear_down: magnet pocket up; glue to the screw end |
| 20_Stand_HeadBracket.stl | 1 | 137.36 | 103.8 × 52.0 × 30.0 | rear_down: bench stand; back face on bed, nut pockets and column hole open upward |
| 21_Stand_Base.stl | 1 | 256.3 | 170.0 × 180.0 × 28.0 | front_down: bench stand; table face on bed, column socket up |

**Print the fit coupons first**, in ABS on the same printer as the real parts: 13b_FitTest_rev7.stl (rev 7 fits: tongue and tip-block pocket stubs cut from the real parts, so install the 2 inserts and then test the slide fit and the M3×10 screws; AS5600 slot; M6 nut pocket; 2020 column socket; magnet puck, to try in a 608) and 13c_FitTest_pad_TPU95A.stl in TPU (it should snap into the pocket stub groove and not pull out by hand). Then 13_FitTest_coupons.stl (16 cm³, one plate). ABS shrinks more than PETG, so the rev 6 fits may need retuning. It checks every fit that depends on your printer: Ø3.9–4.2 pin bores in 6 mm plate, the three z-stacks with their 0.2/0.3 mm gaps, the 608 cradle (Ø22.06 seat, front lip, collar recess), and a 12.0 mm channel with an 11.6 mm tongue. If the 608 is loose, or a pin or the tongue binds, adjust the matching value in design.py before printing the real parts.


Print settings: ABS in an enclosed printer (a draft shield at minimum), part-cooling fan low or off, brim on the base and cover; check the base, cover and stand base on a flat surface (glass) before assembly and reprint any that rock, 0.2 mm layers, 4 perimeters, 30–40% gyroid, 100% around insert holes. After printing, run a 4.0 mm drill through the pivot bores by hand (Ø4.2 bores = running fit, Ø4.1 = snug) Do not drill the Ø3.9 dowel press holes in the base; the cover holes are oversize on purpose (the sleeves are bonded in).

## 7. Onshape

**Status (rev 7, 2026-10-24):** the v2 design is in the Onshape document **GripperV2** (https://cad.onshape.com/documents/21eb00e5286d05130362fe39), a copy of the rev 6 document. The original "Lead Screw Gripper" document stays the rev 6 record.

- Feature Studio 1 holds the rev 7 `LeadScrewGripper.fs` (42104 characters, SHA-256 05ef67f130b2d4b1…, identical to the local file), written through the browser session (0 FeatureScript MCP requests).
- The feature dialog now has **Tip set** (Narrow / Wide) and **Include bench stand**; it reports the pad-to-pad gap for the chosen set. Part Studio 1 builds 72 parts; every volume is within 1.3 mm³ of the local model, and the wide set matches too.
- Assembly 1: 72 instances, 21/21 features OK. New rigid groups "Finger U + tip" and "Finger L + tip" (finger, tip block, pad, 2 tip screws); the encoder, controller and stand parts are in "Frame (fixed)". Slider at both limits: carriage +20.83 / −11.20 mm, fingers 18.00 / −15.00 mm, tips follow the fingers; past the limit it clamps. Left at 0 (gap 30). Record: source/results_onshape_rev7.json.
- Pictures: images/onshape_v2_assembly_iso.png, images/onshape_v2_assembly_top.png, images/onshape_v2_partstudio_iso.png. The "Robot export" assembly is unchanged (ROS 2 phase).

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
  - Grip thrust: added an 8 mm lock collar behind the 608. The bearing moved 4.5 mm toward the jaws, the block grew from 18.0 to 22.5 mm long (R6 front corners, bolts 8.5 mm off the axis), and the collar sits in an Ø16 pocket at the back of the block, 0.5 mm inside its rear face. The screw is cut to 78.5 mm (was 78.0) and ends flush with the 608 face.
  - Section through the thrust path: images/rev6_thrust_section.png.
  - Layer stack: finger / conrod now 6.5–14.1 (7.6 mm = 38 layers) and upper crank plates 14.4–18.2 (3.8 mm), with the screw axis at 10.3. Gaps went from 0.1 to 0.2 below and 0.3 above each moving layer.
  - Fit coupons (13_FitTest_coupons.stl) so the bore, stack, bearing-seat and tongue fits are tested before the full print.
  - Re-checked: 49 valid parts, 0 collisions over 41 poses, intended contacts only; structural min SF 3.6 (unchanged, dowel); new block front lip SF 34.5 bearing / 74.6 shear-out; fasteners min SF 4.3; no new overhangs.
- Alternative: `step/LeadScrewGripper_assembly_gap30mm.step` imports into any CAD package as a 49-part assembly.

## 8. Assembly sequence

1. Heat-set inserts, pressed from the top face until flush (the shoulder screws seat on the insert top): BellCrank Lower (F1, D), FrontCrank Lower (F2), Carriage lower ears (2), Finger tongues (2 each). Base: 2 motor-wall joint, 2 bearing-block ears, 2 posts. Adapter: 4 side holes. Cover top: 4 for the controller standoffs.
2. Press the 2 Ø3 locating pins into the bearing-block half of the base (8 mm deep). Press the 4 dowels into the base (O1, O2 both sides; 6.5 mm deep, square to the plate). Wax the top 8 mm of each dowel (release) and slide a bronze sleeve onto each.
3. Pull-test the lock collar first: tighten its set screw on the end of the lead screw, check it holds a firm pull by hand without slipping, then take it off. Cut the lead screw to 78.5 mm -0.5/+0 from the motor face, so its end sits 3 mm inside the 608 bore (never longer: the encoder puck fills the rest). Chamfer, clean and grease it.
4. Slide the nut into the carriage from the front: body into the bore, flange into the front recess, two flange holes at 3 and 9 o'clock. Fit 2× M3×8 button heads into the Ø2.5 pilots, snug only.
5. Spin the carriage onto the motor screw from its rear. Slide the lock collar on (set screw loose), then the 608ZZ onto the screw tip.
6. Lay motor + screw + carriage + bearing into the base: motor connector facing up, pilot into the wall recess, carriage tongue in the channel, 608 in the lower cradle against the front lip, collar behind it. Fit the 2 lower motor screws (M3×8) through the access slots with a 2.5 mm ball-end driver. Push the collar forward until it just touches the 608 inner ring (no preload) and tighten its set screw. Run the carriage end to end by hand, then tighten the 2 nut screws.
7. Encoder: glue the magnet into the printed puck (flush), slide the puck into the 608 bore against the screw end and glue it to the screw end with a drop of CA. Solder 4 wires (VCC, GND, SDA, SCL) to the AS5600 pad row, drop the board into the slot in front of the 608 (chip toward the magnet, pads up) and lead the wires up through the slit in the cover.
8. Per side: BellCrank Lower on O1 and FrontCrank Lower on O2 (bosses up). Finger onto F1/F2, conrod onto D and between the carriage ears at C. BellCrank Upper and FrontCrank Upper on top. Shoulder screws at F1, F2, D, C into the lower-plate/ear inserts.
9. Tip blocks: slide a TPU pad into the tip block groove from the rear and press until the barb at its rear end snaps past the step at the groove entrance (a drop of soapy water helps; pliers to remove), push the tip block up onto the finger tongue from below and fit 2× M3×10 from below through its floor. To change sets, take the 2 screws out and slide the block off downward.
10. Cover: put slow-cure epoxy in the 4 oversize cover holes, lower the cover over the sleeves and dowels, fit all its screws, and let the epoxy cure with the gripper assembled (the sleeves bond to the cover where the dowels really are). 2× M3×20 at the motor wall, 2× M3×20 at the bearing-block ears, 2× M3×8 at the posts, then the 2 upper motor screws (M3×8) through the cover slots.
11. Controller: screw the 4 standoffs into the cover-top inserts and fit the protoboard (Pico, TMC2209, buck, divider; see the wiring table) with 4× M3×6. Zip-tie each cable (USB, battery, motor, encoder) to the board grid as strain relief.
12. Bench stand: column into the base socket, M5×16 from below into the column end (tap it M5) and 2× M5×12 through the socket walls into T-nuts. Screw or bolt the base to the bench through its 4 corner holes. Slide the head bracket onto the column and lock it with 2× M5×12 into T-nuts. Drop 4 M6 nuts into the bracket pockets from the back. Strap the battery to the column (side away from the gripper) and plug in the balance-lead alarm.
13. Bolt the adapter first: to a robot flange with 4× M6×12, or to the stand head bracket with 4× M6×20 into the nuts. Slide the gripper onto it (the U-slot is open at the rear) and fit 4× M3×8 through the side walls into the adapter inserts.
14. Driver: 0.70 A RMS, 1/16 µstep (400 steps/mm). Home by driving open slowly into the stop (carriage meets the bearing block at 66 mm) with stall detection, then back off 1 mm; the AS5600 then tracks screw turns (4 over the full stroke). In use, cap the commanded opening at 60 mm (80 mm pad gap with the wide tips) so the carriage never hits the stop at speed. Keep the hold current on while gripping (the Tr8×8 is back-drivable). Stop the motor below 10.5 V on the battery monitor. Calibrate grip once with a kitchen scale between the jaws.

Tighten every M3 to 0.15 N·m or less (snug with the short arm of the key). More crushes the ABS under the head.

## 9. Assumptions, limits, verify before buying

- Rigid links, quasi-static, equal load sharing between the two sides, Coulomb friction in the screw only (pivot friction lowers grip a few %; the current setting has margin).
- Verify on receipt: motor body ≤ 40 mm (the adapter sits 1 mm behind it), pilot Ø22×2, M3 holes on 31 mm square; nut flange Ø22×3.5 and body Ø10.2 (edit NUT_* in design.py if different); shoulder-screw head ≤ Ø7.5×3.5 and thread ≤ 6 mm.
- Robot flange: I assumed a Ø31.5 H7 centring recess (spigot 31.44 × 3 mm) and the Ø6 pin on the PCD at +Z, between bolts. Check your robot drawing.
- μ = 0.35 is kept as the design value. The TPU 95A pads typically give more (about 0.6–0.7), which roughly doubles the slip margin.
- ABS creeps slowly under sustained clamp. For long holds, re-tighten with a short current pulse, or print the fingers and lower crank plates in PA-CF.
- Motor connector: the adapter sits 1 mm behind the motor, so the cable must leave from a side face. Mount the motor with the connector facing up, through the cover's U-slot.
- M6×12 puts 6 mm of thread into the robot flange. Check your flange's thread depth, and use a washer or modest torque on the ABS.
- Thrust: the collar and the motor's internal bearing share the screw load in a way that depends on how the collar is set. Check the motor datasheet's axial load rating anyway, and don't preload the collar.
- The jaws also move fore-aft: 16.5 mm in total over the stroke. They are furthest forward near a 15 mm gap and furthest back fully open (15.4 mm behind the closed position). That is inherent to this linkage; teach grasp poses at the gap you'll use.
- Not modelled: wiring and connectors, zip ties, a limit switch (sensorless homing assumed), the stand T-nuts and M5/M6 hardware, the M3 screws on top of the standoffs.
- Wide tips: the F2 pivot boss, 3–14 mm behind the seam, sits about 1.9 mm proud of the wide pad face. Round objects never reach it; a flat object longer than the pads that reaches back past the seam would touch it. A 7 mm offset instead of 10 would clear it (gap 14–80 mm).
- AS5600 module size: designed for 23 × 23 mm boards (most listings are 22–23 mm). The slot is 23.4 mm; the chip must be centred on the board, and parts on the chip side must sit within the 19.6 mm relief.
