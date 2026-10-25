# GripperV2 design review: independent senior-engineer critique (2026-10-24)

An independent agent, briefed as a senior mechanical design engineer (brief: `docs/REVIEW_BRIEF.md`), reviewed the local files and the Onshape document read-only. Tags: **V** = verified with data, code or Onshape; **S** = suspected (judgement). Before relaying, the main session re-checked three items: the tongue section and stresses (1), the slider position (28) and the report wording (39). All three hold.

## Status after the fixes (rev 7.1, same day)
| Item | Status | Commit |
|---|---|---|
| 1 Tip joint | Fixed: tongue 16.3 × 13.6 mm root, rises to the block top; screws from below at mid-depth. Tongue root SF 1.6 at the limit, 5.3 in use (was 0.27 / 0.89) | e576355 |
| 2 Out-of-plane load | Fixed for normal grips: block and pad centred on the pin plane. Checked a grip on the pad edge: tongue torsion SF 1.7 / 5.6; F2 bore twist SF 0.6 limit / 2.0 in use (bore-only model, conservative) | e576355 |
| 3 Fixed pivots | Fixed: dowel tops in bronze sleeves bonded into the cover (zero clearance, no reamer); dowels 4×36. Base socket SF 2.6, cover 4.5 | a7d0215 |
| 4 Pad retention | Fixed: snap barb on the key catches a step at the groove entrance (checked: blocked when pulled back) | 01b9647 |
| 5 Dynamics / homing | Documented: hard-stop estimate, homing at 0.3 A and 10 mm/s with the encoder detecting the stop. **Needs input:** the motor's axial load rating and rotor inertia | 03488d6 |
| 6 Driver current | Documented: VREF ceiling + i_scale_analog, EN pull-up, re-init after driver reset (BOM updated) | 03488d6 |
| 7 Battery | Fixed: strapped to the column, ≥ 45 mm from every gripper part; fuse before the switch, divider after it, balance-lead alarm | b032bca |
| 8 Stand stability | Fixed: 180 × 170 base, 2 more M5 at the column foot, and 2 printed C-clamps with M8 star knobs that clamp the base's front corners to Anurag's desk edge (40 × 40 mm black edge; range 24–49 mm). Unclamped it would tip at about 5 N | b032bca + desk clamps |
| 9 Grip schedule | Documented: run-current table against the gap for about 30 N per jaw | 03488d6 |
| 10 Encoder in the 608 | **Needs a bench test** (procedure in the report section 4a) before printing the bearing block; redesign only if the field is too weak | 03488d6 |
| 11 Fit coupons | Fixed: 13b (rev 7 fits, cut from the real parts) and 13c (TPU pad snap) | 7cf320d |
| 12 Warping | Partly: 2 locating pins across the bearing-block split, flatness check in the print notes. **Needs input:** may the stand parts be printed in PLA/PETG? | 3058a98 |

Items 13–39 are not addressed yet.

## Verdict
The linkage, pivots, thrust path, collision sweep and the Onshape match are sound. The v2 additions are the weak spots:
- **Tip joint:** undersized, and checked on the wrong section.
- **Narrow pads:** can slide out of their groove.
- **Out-of-plane pad load:** not analysed.
- **Fixed-pivot dowels:** they depend on a reamed cover fit that's hard to achieve.
- **Encoder magnet:** it sits inside a steel bearing.
- **Current limit:** it can be lost when the battery is switched.
- **Battery:** the LiPo sits under a jaw.
- **Stand:** it tips over at about 5 N.

The core gripper is close to printable; the tip blocks, pads, stand and electronics need another round.

## Critical
1. **Tip-block joint carried by a 9 × 7.6 mm tongue, unchecked** (V).
   - **Where:** `design.py` TONGUE_Y/TONGUE_X1, `structural.py` tip rows.
   - **Evidence:** the only finger material past x = 41 is the tongue (Z = 103 mm³). Far-tip moment: 11,466 N·mm at the 200 N limit and about 3,470 N·mm in use (82.6 N per jaw), giving 112 MPa (SF 0.27) and 34 MPa (SF 0.89). The "tongue alone SF 2.7" row only checked flank contact pressure.
   - **What carries the load:** with that bending, the joint leans on 2 × M3 in Ø3.4 clearance holes. They need 934 N at the limit and 282 N in use against about 150 N of clamp friction, so the block slips until the screws bear.
   - **Other unchecked sections:** the tongue net section at the rear insert (SF 1.2 at the limit) and the front-insert shear-out (SF 2.2).
   - **Fix:** a deeper tongue (16–20 mm; about 15 mm for the wide block); a steel Ø3–4 cross-pin near the top of the seam; add root-bending, net-section, shear-out and torsion rows.

## Major
2. **Out-of-plane pad load not modelled** (V, hand calculation). The pad centre is z 16.25 against the pin plane at z 10.3, and up to 15.7 mm above it for top-edge contact.
   - **Tongue torsion:** 4–11 MPa in use and 14–38 MPa at the limit, much of it interlayer shear (allowable about 7 MPa).
   - **Pin bores:** the torsion also adds bearing couples at F1/F2 (F2 at the limit reaches about 39 MPa combined).
   - **Fix:** add a z-offset case, or centre the tip block and pad on z = 10.3 (for example z 0.5–20; the block is clear of the crank plates and the base; confirm with `check.py`).
3. **Fixed pivots rely on a reamed close fit in the cover** (V, calculation). With any clearance, the dowel cantilevers from the 6 mm base socket.
   - **Socket pressure:** 86–119 MPa in use and about 300 MPa at the limit.
   - **Fit:** 4 pressed dowels into a separately printed ABS cover (shrink mismatch about 0.1–0.2 mm over 102 mm), and no reamer in the BOM.
   - **Fix:** clamp each pivot through both plates (shoulder screw from below into an insert or nut in the cover, or a flanged bushing).
4. **Narrow pads not retained rearward** (V). Sliding the narrow pad −x by up to 45 mm hits nothing, because the groove is open at the rear and nothing covers it. The dovetail lips are knife-edged. **Fix:** close the groove at the rear and snap the key in, or put a hook/barb on the key; fit-test it.
5. **No dynamic load case; the homing method conflicts with StallGuard and loads the motor bearings** (V calculation; inertia assumed).
   - **Impact:** the rotor reflects about 3.3 kg at the carriage, so a hard stop at 600 rpm can add 150–460 N.
   - **Homing:** stalling into the open stop pushes the screw into the motor bearings, because the collar only protects the grip direction. StallGuard also needs speed, so "drive open slowly" makes DIAG unreliable.
   - **Fix:** home at about 0.3 A and about 10 mm/s; detect the stop with the AS5600 (commanded against measured); slow down near the ends; add a dynamic row; check the motor's axial rating.
6. **The 0.7 A limit is set only over UART and is lost when the battery switch cycles** (S). The TMC2209 resets to its VREF-pot current, often 1 A or more, while the Pico stays alive on USB, and EN floats while the Pico boots.
   - **Fix:** set the VREF pot to 0.7 A with `i_scale_analog=1` (so UART can only lower it).
   - **Fix:** add a 10 k pull-up from EN to VIO.
   - **Fix:** in firmware, detect a driver reset (GSTAT/IFCNT) and re-send the configuration.
7. **LiPo in the work zone, no hardware over-discharge cut-off** (V geometry; S drain).
   - **Placement:** the upper tip block passes 8.9 mm (wide) or 12.9 mm (narrow) from the pack.
   - **Discharge:** the 10.5 V cut-off only disables the driver; the Pico, buck and driver logic keep draining.
   - **Fix:** move the tray outside the jaw footprint; add a balance-lead alarm, a protection board or a latching switch; use a LiPo bag; put the divider after the switch.
8. **Bench stand tips over at about 5 N** (V). The centre of gravity is 161 mm high and the nearest base edge is 68 mm away; there is also one M5 at the column foot (expect wobble). **Fix:** clamp or screw holes to fix it to the bench, a bigger or heavier base, a shorter column (about 280 mm), 2 foot screws.
9. **Grip varies about 3× over the range** (V). MA is 0.345 → 0.752 at 60 mm, so at 0.7 A the grip is 27–38 N at gap 0 and 58–83 N at 60 mm. **Fix:** schedule IRUN against the encoder gap; calibrate at 3–4 gaps; expose grip force as a ROS parameter.
10. **Encoder magnet inside the steel 608 bore** (S). The ferrous ring shunts and distorts the diametric field; the inner ring may also slip relative to the screw. **Fix:** bench-test a 608 + puck + module first (AGC/MAGNITUDE, linearity); otherwise mount the magnet ≥ 3–4 mm in front of the 608 in a non-ferrous holder.
11. **Fit coupons don't cover any rev 7 fit; inserts may bulge the tongue** (V coverage; S bulge). Not covered: tongue/pocket (0.15 mm), TPU dovetail (0.05 mm), encoder slot, puck in the bore, M6 nut hex, column hole. **Fix:** add a tongue + pocket + insert coupon and a pad/groove coupon; install the inserts before testing.
12. **ABS warping of the large flat parts** (S). Base, cover, stand base and bracket. The carriage slides on the base, and the split 608 seat and motor pilot are registered only by distant dowels. **Fix:** print the stand in PLA/PETG or use plywood; check the base and cover for flatness on glass; add 2 locating pins near the bearing block.

## Minor
13. **Back-driving at hold current** (V). Holding torque is about 0.52 of driving torque, so IHOLD at about 50 % plus auto power-down will let the grip back-drive. Dry brass drops the grip at gap 0 to about 22 N. **Fix:** IHOLD = IRUN while gripping, a long TPOWERDOWN, keep the screw greased.
14. **600 rpm on 12 V is unlikely** (S). Back-EMF ≈ the supply voltage; expect about 300 rpm (about 0.8 s full stroke).
15. **Shoulder-screw pivots are not ideal double shear** (S). The upper hole is Ø4.1, so the shoulder cantilevers on the M3 neck until that play closes. **Fix:** ream to Ø4.0, or check it as a cantilever.
16. **Thrust collar** (S). It only protects the grip direction; its set screw bears on 4-start thread crests; the "firm pull by hand" test is far below 200 N. **Fix:** clamp-style collar; pull-test ≥ 250 N with a luggage scale.
17. **Screw cut length is ambiguous** (V). "78.5 mm from the motor face" read from the pilot face gives a screw 2 mm too long, and the magnet would hit the chip (gap 0.8 mm). **Fix:** specify "76.5 mm past the pilot face".
18. **Encoder details** (S). 0.4 mm puck floor; CA glue can wick into the bearing (use epoxy); DIR not wired (the AS5600 needs it tied); I²C leads run beside the motor leads (twist them, cross-check turns against steps).
19. **Power details** (S). Set and verify the MP1584 at 5.0 V before it touches VSYS (or use a fixed 5 V buck); 100 nF at GP26; fuse ahead of the switch; ≥ 35 V bulk capacitor; single-point ground.
20. **Screw and nut seats print as bridges; one print note is wrong** (V). With `rear_down`, the bracket's nut pockets open onto the bed, not upward as documented. **Fix:** sacrificial layer, or flip the bracket.
21. **"All link loads are in the print plane" is false** (V). The carriage (printed `rear_down`) and the adapter side screws load across layers; low stress, but these rows should use MAT_SZ.
22. **BOM** (V count; S sourcing).
    - **Inserts:** 26 are needed, not 22 (the 4 in the cover top were missed).
    - **Missing:** Ø4.0 reamer, M5 tap, 2×8 female / 2×20 male headers, wire and connectors, epoxy, zip ties, Velcro, LiPo bag and alarm.
    - **Collar:** common 8 mm collars are 16 OD, too big for the ≤ 14 × 7 spec.
    - **Shoulder screw:** the example part number isn't findable.
23. **Cover can't come off without removing the controller board** (V). The block bolts at (21.55, ±16) are under the protoboard. **Fix:** move the board about 10 mm toward −x, or drill access holes.
24. **Wide set has no stop at 20 mm; firmware can't tell which set is fitted** (V). The real stop is a wide-set gap of 17.1 mm. **Fix:** per-set limits plus a tip-set parameter or touch-off.
25. **Wide set: F2 boss and both front-crank bosses sit 1.9 mm proud of the pad face** (V). **Fix:** 7–8 mm offset instead of 10.
26. **Stand fasteners** (V/S). M5×10 leaves about 2.4 mm in the T-nut (use M5×12); M6×20 ends flush with the nut; no M6 torque given (crushes ABS above about 0.6–0.8 N·m).
27. **Onshape masses are wrong** (V). Total 1888 g: the motor is solid steel (554 g against about 280 g real) and the extrusion is 432 g against about 200 g real. **Fix:** density overrides, before any URDF export.
28. **Onshape assemblies** (V).
    - **Slider:** now at +11.2 mm (closed), not the recorded 0.
    - **Limits:** they are constants tied to the gap-30 pose, so changing the dialog gap silently breaks them.
    - **Screw:** it is in the fixed group, so it never turns.
    - **Stand:** it is in the gripper's frame group, so the base appears upright in the default view.
    - **Robot export:** it has no jaw geometry.
29. **FeatureScript and dialog** (V). `try silent` around the subtraction booleans hides failed cuts; the gap input stays in narrow-set units when Wide is chosen; Tip set as a parameter means only one set exists in the BOM and exports. **Fix:** pad-to-pad gap input; use an Onshape configuration for the tip set and the stand.
30. **Clamp-load creep** (S). About 15 MPa under the heads; anaerobic threadlockers crack ABS. **Fix:** nylon-patch screws; re-torque after 24 h.
31. **Pinch points** (S). An open linkage with up to about 150 N per jaw. **Fix:** a guard for public demos; label the battery switch as the E-stop.
32. **Stand height** (V). The tips are 23 mm above the plate top (not 32) and drop 16 mm while closing, so a lowered bracket drives them into the plate or battery. **Fix:** document a minimum bracket height, or add a stop collar.

## Nits
33. **Stale text and dead code** (V). "printed serrations" and "jaw block" text; unused `_jaw_profile`/`_serration_cut`; `TIP_R` redefined (2.0 → 3.0); handoff says "carriage abuts only the base", but the cover also touches.
34. Ball-end driver for M3 button heads is 2.0 mm, not 2.5 (V).
35. `fasteners.py` reports 7.3 mm of thread engaged in a 5.7 mm insert (V).
36. `kin.statics(Fx)` is never used. Jaws-down payload acts along x and back-drives below a 15 mm gap (about 5 %) (V).
37. Wide-set check reports predate commit 71eec9e; rerun for traceability (V).
38. Front-lip bearing area: the 608 outer-ring face is about 90 mm², not 153; SF is still about 13 (V).
39. `DESIGN_REPORT.md` lines 9 and 46 contain source-provenance wording that the handoff's section 0 rule says must not be published. Remove it before any portfolio use (V).

## Good decisions worth keeping
- Double-shear clevis cranks, z-stack gaps, screw axis on the conrod mid-plane.
- No toggle in the window; transmission angle ≥ 59°.
- The collar → 608 → front-lip thrust path.
- design.py as the single source of truth with FS round-trip, 41-pose sweeps for both sets, and append-only part ids; Onshape matches.
- The bolt-on tip-set concept with one common pad.
- Encoder turn counting from the open stop.
- Keeping the ISO 9409 adapter.
- Back-drivable screw plus VM switch as a de facto E-stop.
- Honest trade-off notes.

## Open questions for the owner
1. Heaviest or most fragile demo object; is 25 N at gap 0 really needed?
2. Exact motor (axial rating, k_e, inductance)?
3. Will people hand objects to the gripper; can the stand be clamped to the bench?
4. Does the fablab printer have an enclosure; may the stand be PLA/PETG or plywood?
5. Do you have a Ø4.0 reamer, an M5 tap and a torque driver?
6. Would you accept a 7–8 mm wide offset instead of 10?
7. Tip-set detection in firmware, or a ROS parameter?
8. Is a URDF with mimic joints acceptable for sim-to-real?
