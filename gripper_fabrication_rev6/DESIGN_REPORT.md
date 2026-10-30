# Lead-Screw Parallel Gripper: Design & Validation Report

Generated from the verified model (design.py → results.json, results_struct.json). All numbers below come from those files.

## 1. Summary

| Item | Value |
|---|---|
| Mechanism | Reference architecture kept: parallelogram finger (pure translation) + 90° bell crank + conrod to lead-screw carriage, 1 DOF, mirrored |
| Jaw range | 0 → 66 mm (spec 0–60 mm) |
| Carriage stroke | 32.0 mm = 16.0 screw turns (Tr8×2) |
| Grip force per jaw | ≥ 33.1 N anywhere in range at 0.45 A RMS, worst-case screw friction (needs 21.0 N for 500 g) |
| Holding | Tr8×2 self-locking (lead angle 5.2°): holds the payload with power off |
| Structure | Min safety factor 3.6 vs yield at a 200 N screw-force limit case (the motor clamps at 96–175 N at 0.45 A) |
| Motion check | 0 collisions over 41 poses (all 49 parts, including the 16 modelled screws); only intended joint/stack contacts below 0.8 mm |
| Grip thrust | Screw reaction → lock collar → 608 inner ring → outer ring → block front lip. 608 static axial capacity ≈ 685 N vs 200 N limit (3.4×) |
| Fasteners | 2 screw sizes (12× M3×8, 4× M3×20 button head); min SF 4.3 under mount, stall and limit loads; tighten ≤ 0.2 N·m |
| Printed volume | 333 cm³ PETG (~233 g at typical infill) + motor ~280 g |
| Mount | ISO 9409-1-50-4-M6 adapter (PCD 50, 4×M6, Ø31.5 spigot, Ø6 pin) |

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

Jaw gap ↔ carriage position (for firmware; home = open stop, 1600 steps/mm at 1/16 µstep):

| Gap mm | Crank θ° | C_x mm | Carriage from open stop mm | Steps from home |
|---|---|---|---|---|
| 0 | -15.5 | -27.49 | -32.03 | 51255 |
| 6 | -9.2 | -25.37 | -29.92 | 47873 |
| 12 | -3.1 | -23.19 | -27.74 | 44381 |
| 18 | 3.1 | -20.95 | -25.5 | 40797 |
| 24 | 9.3 | -18.65 | -23.2 | 37119 |
| 30 | 15.6 | -16.28 | -20.83 | 33331 |
| 36 | 22.0 | -13.82 | -18.37 | 29394 |
| 42 | 28.8 | -11.23 | -15.77 | 25237 |
| 48 | 36.1 | -8.41 | -12.96 | 20735 |
| 54 | 44.2 | -5.23 | -9.78 | 15643 |
| 60 | 53.5 | -1.32 | -5.87 | 9391 |
| 66 | 65.6 | 4.55 | 0.0 | 0 |

## 4. Motor and driver sizing

- Screw force for ≥ 25 N everywhere: 72.4 N → torque 0.050–0.091 N·m (screw η 0.25–0.46).
- **Set driver current to 0.45 A RMS** (for a 1.5 A / 0.4 N·m motor): screw force 95.7–174.6 N → grip ≥ 33.1 N per jaw, and stays below the 200 N structural limit even with a well-greased screw.
- **Warning:** at full rated current the motor can push ~582 N, far above what the printed parts are sized for. The current limit is a safety item.
- Speed: 600 rpm -> 20 mm/s -> full stroke 1.6 s. Self-locking means no holding current is needed for the payload. Keep a low hold current anyway so the step position is not lost.

## 5. Structural checks (200 N screw-force limit case; σ op = at the 174.6 N stall force at 0.45 A)

| Check | Load N | σ limit MPa | σ op MPa | SF yield |
|---|---|---|---|---|
| Shoulder screw Ø4 double shear (12.9 steel) | 309.3 | 12.31 | 10.75 | 81.3 |
| Dowel Ø4 bending, simply supported base↔cover | 309.3 | 329.91 | 288.08 | 3.6 |
| Finger bore at F2 on shoulder (7.6 mm) | 309.3 | 10.17 | 8.88 | 4.4 |
| Finger bore at F1 (7.6 mm) | 192.4 | 6.33 | 5.53 | 7.1 |
| FrontCrank bores at O2 (6.0+3.8 plates + 8.1 spacer) | 309.3 | 4.32 | 3.77 | 10.4 |
| Base dowel press hole (55% share, 6 mm) | 309.3 | 7.05 | 6.16 | 6.4 |
| Cover dowel hole (45% share, 3.9 mm) | 309.3 | 8.98 | 7.84 | 5.0 |
| ConRod bores (7.6 mm) | 156.4 | 5.14 | 4.49 | 8.7 |
| Carriage ears at C (6.3 + 3.8 mm) | 156.4 | 3.87 | 3.38 | 11.6 |
| Finger boss tear-out at F2 | 309.3 | 5.98 | 5.23 | 4.5 |
| FrontCrank (two-force) net section | 309.3 | 4.64 | 4.05 | 9.7 |
| ConRod (two-force) net section | 156.4 | 3.55 | 3.1 | 12.7 |
| BellCrank bending near O1 (two plates) | 192.4 | 6.04 | 5.28 | 7.4 |
| Finger jaw root (in-plane, 25 mm deep x 7.6) | 273.0 | 10.34 | 9.03 | 4.4 |
| Jaw extension root (z=14.1 layer plane) | 163.8 | 0.29 | 0.25 | 70.0 |
| Block front lip bearing on 608 outer ring | 200.0 | 1.31 | 1.14 | 34.5 |
| Block front lip shear-out (8 mm wall) | 200.0 | 0.36 | 0.32 | 74.6 |

**Grip thrust (rev 6):** closing the jaws pushes the carriage toward the motor, so the screw is pulled the other way. A lock collar behind the 608 carries that pull into the bearing inner ring; the outer ring bears on the block front lip, which is the base and cover halves clamped together. The motor's own bearing no longer takes the full reaction. Limit case 200 N vs ≈ 685 N 608 static axial capacity. Collar set-screw holding on the threaded screw is not rated: verify with a hand pull test before assembly.


The dowel is modelled as a beam on two supports: the 6 mm press socket in the base and the 3.9 mm close-fit hole in the cover. The cover hole must be reamed to Ø4.0 so it carries its share; with a loose cover hole the base socket would see the full bending moment.


PETG printed in-plane yield taken as 45 MPa. All link loads are in the print plane (along the rasters). Interlayer stress appears only at the jaw-block root (≈0.3 MPa).


### 5.1 Fasteners (every screw is modelled)

Gripper mass 763 g (printed parts taken as solid, conservative), CG at x = -27 mm; payload at x = 82.5 mm; mount at x = -98.5 mm. Pitch moment at the mount 2.85 N·m (×2 dynamic).

| Check | Load N | Stress MPa | SF yield | Note |
|---|---|---|---|---|
| Side screw M3x8, shank shear (mount, x2 dynamic) | 120.2 | 23.91 | 15.5 | 8.8 steel; ignores clamp friction |
| Side wall hole bearing, 3.8 mm wall (mount) | 120.2 | 10.55 | 4.3 | base/cover side wall |
| Adapter insert bearing in PETG (mount) | 120.2 | 4.59 | 9.8 | insert OD 4.6 x 5.7 mm |
| Motor screw head on PETG (open-stop stall, tension) | 43.6 | 2.66 | 16.9 | 4 screws share the stall force |
| Nut screw pull-out, self-tapped 4.4 mm (open-stop stall) | 87.3 | 2.53 | 10.3 | shear at the D2.5 pilot wall |
| Nut screw head on brass flange | 87.3 | 5.31 | 37.7 | CuZn yield ~200 MPa |
| Cover screw bearing in cover (200 N limit case) | 92.8 | 7.36 | 6.1 | all four dowel reactions on 6 screws |

| Screw | Clamp mm | Thread engaged mm | Tip to hole bottom mm | Into |
|---|---|---|---|---|
| Motor M3x8 | 4.5 | 3.5 | 1.0 | motor tapped hole, ~4.5 deep |
| Cover to wall/block M3x20 | 16.0 | 4.0 | 2.5 | insert 5.7 (hole 6.5) |
| Cover to post M3x8 | 4.2 | 3.8 | 2.7 | insert 5.7 (hole 6.5) |
| Side wall to adapter M3x8 | 4.0 | 4.0 | 2.5 | insert 5.7 (hole 6.5) |
| Nut flange M3x8 | 3.6 | 4.4 | 2.6 | self-tapped D2.5 pilot, 7 deep |

**Tightening:** a button head bears on 16.4 mm² of PETG. At 0.2 N·m an M3 makes about 330 N of clamp, about 20 MPa under the head (PETG yields near 45 MPa). Tighten every M3 to **0.2 N·m or less**: snug with the short arm of the key, no more. The two nut-flange screws bear on brass and self-tap into plastic; snug them only.

## 6. Motion, clearance and printability checks

- 3D boolean interference over 41 poses from closed to fully open, every part pair, both sides: **0 collisions**. Minimum-distance scan: all pairs under 0.8 mm are intended (shoulder screws in crank bores 0.05, dowels and shoulder screws in running bores 0.1, z-stack gaps 0.2 below / 0.3 above each moving layer, crank plates on base 0.3, fingers meeting at closed, carriage on the open stop). Lock collar 1.0 mm radial to the block; cover 1.38 mm from the front crank at closed.
- Every part is a single valid solid. FeatureScript round-trip rebuild gives identical volumes.
- Print orientation (no supports): links and fingers 0 mm² overhang; base, cover and adapter only hole tops and counterbore steps; carriage printed rear face down, so the nut recess opens upward and nothing needs a bridge or support.

| Print file | Qty | Volume cm³ | Bounding box mm | Orientation / note |
|---|---|---|---|---|
| Base x1.stl | 1 | 106.84 | 145.3 × 130.9 × 31.1 | flat: bottom face on bed; 4 walls, 30% gyroid |
| Cover x1.stl | 1 | 91.62 | 145.3 × 130.9 × 19.2 | flip_x: flat top face on bed |
| Adapter ISO9409-50 x1.stl | 1 | 37.95 | 59.0 × 48.6 × 17.0 | front_down: gripper-side face on bed, spigot up |
| Carriage x1.stl | 1 | 20.16 | 27.8 × 60.8 × 26.0 | rear_down: rear face on bed, nut recess up; no supports; 100% infill around inserts and nut-screw pilots |
| BellCrank Lower U x1.stl | 1 | 5.52 | 39.0 × 31.9 × 14.1 | flat: spacer boss up |
| BellCrank Lower L x1.stl | 1 | 5.52 | 39.0 × 31.9 × 14.1 | flat: mirror of BellCrank Lower U (other side) |
| BellCrank Upper U+L x2.stl | 2 | 3.07 | 39.0 × 31.9 × 3.8 | flat: same part both sides (flip one) |
| FrontCrank Lower U+L x2.stl | 2 | 2.78 | 39.0 × 11.0 × 14.1 | flat: spacer boss up |
| FrontCrank Upper U+L x2.stl | 2 | 1.43 | 39.0 × 11.0 × 3.8 | flat:  |
| ConRod U+L x2.stl | 2 | 2.41 | 33.7 × 11.0 × 7.6 | flat:  |
| Finger U x1.stl | 1 | 23.17 | 79.5 × 49.0 × 19.5 | flat: jaw block up |
| Finger L x1.stl | 1 | 23.17 | 79.5 × 49.0 × 19.5 | flat: mirror of Finger U |

**Print Fit test coupons x1.stl first** (16 cm³, one plate). It checks every fit that depends on your printer: Ø3.9–4.2 pin bores in 6 mm plate, the three z-stacks with their 0.2/0.3 mm gaps, the 608 cradle (Ø22.06 seat, front lip, collar recess), and a 12.0 mm channel with an 11.6 mm tongue. If the 608 is loose, or a pin or the tongue binds, adjust the matching value in design.py before printing the real parts.


Print settings: PETG, 0.2 mm layers, 4 perimeters, 30–40% gyroid, 100% around insert holes. After printing, run a 4.0 mm drill through the pivot bores by hand (Ø4.2 bores = running fit, Ø4.1 = snug) and ream the four cover dowel holes to Ø4.0. Do not drill the Ø3.9 dowel press holes in the base.

## 7. Onshape

**Status:** the Onshape document is at **rev 6** (updated 2026-10-13). Feature Studio 1 holds the rev 6 `LeadScrewGripper.fs` (exact SHA-256 match with the local file) and the lock collar is in the frame group of Assembly 1.

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
  - Grip thrust: added an 8 mm lock collar behind the 608. The bearing moved 4.5 mm toward the jaws, the block grew from 18.0 to 22.5 mm long (R6 front corners, bolts 8.5 mm off the axis), and the collar sits in an Ø16 pocket at the back of the block, 0.5 mm inside its rear face. The screw is cut to 81.5 mm (was 78.0) and ends flush with the 608 face.
  - Section through the thrust path: images/rev6_thrust_section.png.
  - Layer stack: finger / conrod now 6.5–14.1 (7.6 mm = 38 layers) and upper crank plates 14.4–18.2 (3.8 mm), with the screw axis at 10.3. Gaps went from 0.1 to 0.2 below and 0.3 above each moving layer.
  - Fit coupons (Fit test coupons x1.stl) so the bore, stack, bearing-seat and tongue fits are tested before the full print.
  - Re-checked: 49 valid parts, 0 collisions over 41 poses, intended contacts only; structural min SF 3.6 (unchanged, dowel); new block front lip SF 34.5 bearing / 74.6 shear-out; fasteners min SF 4.3; no new overhangs.
- Alternative: `step/LeadScrewGripper_assembly_gap30mm.step` imports into any CAD package as a 49-part assembly.

## 8. Assembly sequence

1. Heat-set inserts, pressed from the top face until flush (the shoulder screws seat on the insert top): BellCrank Lower (F1, D), FrontCrank Lower (F2), Carriage lower ears (2). Base: 2 motor-wall joint, 2 bearing block, 2 posts. Adapter: 4 side holes.
2. Press the 4 dowels into the base (O1, O2 both sides; 6 mm deep, square to the plate). Ream the 4 cover dowel holes to Ø4.0.
3. Pull-test the lock collar first: tighten its set screw on the end of the lead screw, check it holds a firm pull by hand without slipping, then take it off. Cut the lead screw to 81.5 mm ± 0.5 from the motor face, so its end sits flush with the 608 face (never proud of the 1 mm front recess). Chamfer, clean and grease it.
4. Slide the nut into the carriage from the front: body into the bore, flange into the front recess, two flange holes at 3 and 9 o'clock. Fit 2× M3×8 button heads into the Ø2.5 pilots, snug only.
5. Spin the carriage onto the motor screw from its rear. Slide the lock collar on (set screw loose), then the 608ZZ onto the screw tip.
6. Lay motor + screw + carriage + bearing into the base: motor connector facing up, pilot into the wall recess, carriage tongue in the channel, 608 in the lower cradle against the front lip, collar behind it. Fit the 2 lower motor screws (M3×8) through the access slots with a 2.5 mm ball-end driver. Push the collar forward until it just touches the 608 inner ring (no preload) and tighten its set screw. Run the carriage end to end by hand, then tighten the 2 nut screws.
7. Per side: BellCrank Lower on O1 and FrontCrank Lower on O2 (bosses up). Finger onto F1/F2, conrod onto D and between the carriage ears at C. BellCrank Upper and FrontCrank Upper on top. Shoulder screws at F1, F2, D, C into the lower-plate/ear inserts.
8. Cover onto the dowels (press evenly; close fit). 2× M3×20 at the motor wall, 2× M3×20 at the bearing block, 2× M3×8 at the posts, then the 2 upper motor screws (M3×8) through the cover slots.
9. Bolt the adapter to the robot flange first (4× M6×12). Slide the gripper onto it (the U-slot is open at the rear) and fit 4× M3×8 through the side walls into the adapter inserts.
10. Driver: 0.45 A RMS, 1/16 µstep. Home by driving open slowly into the stop (carriage meets the bearing block at 66 mm) with stall detection, then back off 1 mm. In use, cap the commanded opening at 60 mm so the carriage never hits the stop at speed. Calibrate grip once with a kitchen scale between the jaws.

Tighten every M3 to 0.2 N·m or less (snug with the short arm of the key). More crushes the PETG under the head.

## 9. Assumptions, limits, verify before buying

- Rigid links, quasi-static, equal load sharing between the two sides, Coulomb friction in the screw only (pivot friction lowers grip a few %; the current setting has margin).
- Verify on receipt: motor body ≤ 40 mm (the adapter sits 1 mm behind it), pilot Ø22×2, M3 holes on 31 mm square; nut flange Ø22×3.5 and body Ø10.2 (edit NUT_* in design.py if different); shoulder-screw head ≤ Ø7.5×3.5 and thread ≤ 6 mm.
- Robot flange: I assumed a Ø31.5 H7 centring recess (spigot 31.44 × 3 mm) and the Ø6 pin on the PCD at +Z, between bolts. Check your robot drawing.
- μ = 0.35 is conservative for serrated PETG. A thin TPU or rubber pad on the jaw face roughly doubles the slip margin.
- PETG creeps slowly under sustained clamp. For long holds, re-tighten with a short current pulse, or print the fingers and lower crank plates in PA-CF/ASA.
- Motor connector: the adapter sits 1 mm behind the motor, so the cable must leave from a side face. Mount the motor with the connector facing up, through the cover's U-slot.
- M6×12 puts 6 mm of thread into the robot flange. Check your flange's thread depth, and use a washer or modest torque on the PETG.
- Thrust: the collar and the motor's internal bearing share the screw load in a way that depends on how the collar is set. Check the motor datasheet's axial load rating anyway, and don't preload the collar.
- The jaws also move fore-aft: 16.5 mm in total over the stroke. They are furthest forward near a 15 mm gap and furthest back fully open (15.4 mm behind the closed position). That is inherent to this linkage; teach grasp poses at the gap you'll use.
- Not modelled: wiring, a limit switch (sensorless homing assumed), cable strain relief.
