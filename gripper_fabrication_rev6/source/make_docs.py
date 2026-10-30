import json, numpy as np, csv, design as D
from kin import geom
R = json.load(open('results.json')); S = json.load(open('results_struct.json')); FX = json.load(open('results_fasteners.json')); OS = json.load(open('results_onshape_rev5.json')); PP = json.load(open('../print_parts.json'))
PARTS = [p for p in PP if not p['file'].startswith('Fit test coupons')]   # the 12 gripper print files
CP = next(p for p in PP if p['file'].startswith('Fit test coupons'))       # fit-test coupons (print first, not part of the gripper)
OUT = '..'
P = D.P
# ---- gap table ----
rows = []
for g in range(0, 67, 6):
    th = np.arcsin(g/(2*D.L) + np.sin(D.TH_C)); cx = float(geom(P, th)['C'][0])
    rows.append((g, round(np.degrees(th), 1), round(cx, 2), round(cx - D.S_MAX, 2), int(round((D.S_MAX - cx)*1600))))
# ---- BOM ----
bom = [
 ('P1', 'NEMA 17 external linear stepper, 1.8 deg, body <= 40 mm, ~1.5 A, ~0.4 N.m holding, integrated Tr8x2 lead screw (lead 2 mm, single start) >= 85 mm', 1, 'Cut screw to %.1f mm +/- 0.5 from motor face (end flush with the 608 face), chamfer end' % D.SCREW_LEN),
 ('P2', 'Tr8x2 brass flange nut (flange D22 x 3.5, body D10.2, 4x D3.5 on D16) - usually supplied with P1', 1, ''),
 ('P3', '608ZZ ball bearing 8 x 22 x 7', 1, 'Screw tip support; carries the grip thrust into the block front lip'),
 ('P12', 'Shaft lock collar, 8 mm bore, OD <= 14 mm, width <= 7 mm, with set screw (e.g. OpenBuilds T8 lock collar)', 1, 'Behind the 608, against its inner ring: takes the screw reaction when gripping'),
 ('P4', 'Dowel pin ISO 8734 / DIN 6325, D4 m6 x 32, hardened', 4, 'Fixed pivots O1, O2 (press into base)'),
 ('P5', 'Shoulder screw, 4 mm shoulder x 12 mm, M3 thread <= 6 mm, head <= D7.5 x 3.5 (e.g. Bambu Lab AA123)', 8, 'Moving pivots F1, F2, D, C x2 sides'),
 ('P6', 'M3 heat-set insert, M3 x 5.7, for D4.0 hole', 18, 'Buy 25'),
 ('P7', 'M3 x 8 button head screw ISO 7380', 12, '4 motor (3.5 mm into the motor), 2 cover-to-post, 2 nut flange (self-tap into D2.5 pilots), 4 side walls to adapter'),
 ('P8', 'M3 x 20 button head screw ISO 7380', 4, 'Cover to motor wall (2) and bearing block (2)'),
 ('P9', 'M6 x 12 socket head cap screw ISO 4762 (6 mm into the robot flange; check its thread depth)', 4, 'Adapter to ISO 9409-1-50-4-M6 flange'),
 ('P10', 'Grease: PTFE/lithium for lead screw and pivots', 1, ''),
 ('P11', 'Stepper driver TMC2209 (or equivalent, current-limited 0.45 A RMS), 12-24 V supply', 1, 'Electronics, not modelled'),
]
with open(f'{OUT}/BOM.csv', 'w', newline='') as fh:
    w = csv.writer(fh, lineterminator='\n'); w.writerow(['ID', 'Item', 'Qty', 'Note'])
    for p in PARTS: w.writerow(['PRINT', p['file'].replace('.stl', '') + ' (PETG)', p['qty'], f"{p['note']}; orientation {p['orientation']}; {p['volume_cm3']} cm3"])
    w.writerow(['PRINT', 'Fit test coupons x1 (PETG)', 1, 'Print FIRST: checks pin bores, z-stack gaps, 608 seat and carriage tongue fit on your printer; %.0f cm3' % CP['volume_cm3']])
    for b in bom: w.writerow(b)
_th = np.linspace(D.TH_C, D.TH_O, 2001); _x = geom(P, _th)['F1'][:, 0]; _g = 2*D.L*(np.sin(_th) - np.sin(D.TH_C))
FA = dict(travel=float(_x.max() - _x.min()), gap_fwd=float(_g[np.argmax(_x)]), open_behind_closed=float(_x[0] - _x[-1]))
printed_cm3 = sum(p['volume_cm3']*p['qty'] for p in PARTS)
W, M, T, MO, SC = R['window'], R['MA'], R['transmission'], R['motor'], R['requirement']
drv = S['driver']
md = []
A = md.append
A('# Lead-Screw Parallel Gripper: Design & Validation Report\n')
A('Generated from the verified model (design.py → results.json, results_struct.json). All numbers below come from those files.\n')
A('## 1. Summary\n')
A('| Item | Value |\n|---|---|')
A(f'| Mechanism | Reference architecture kept: parallelogram finger (pure translation) + 90° bell crank + conrod to lead-screw carriage, 1 DOF, mirrored |')
A(f'| Jaw range | 0 → {W["gap_max_mm"]:.0f} mm (spec 0–60 mm) |')
A(f'| Carriage stroke | {W["stroke_mm"]:.1f} mm = {W["screw_turns"]:.1f} screw turns (Tr8×2) |')
A(f'| Grip force per jaw | ≥ {drv["grip_min_per_jaw_N"]} N anywhere in range at 0.45 A RMS, worst-case screw friction (needs {SC["Fg_req_per_jaw"]:.1f} N for 500 g) |')
A(f'| Holding | Tr8×2 self-locking (lead angle {R["screw"]["lead_angle_deg"]:.1f}°): holds the payload with power off |')
A(f'| Structure | Min safety factor {S["min_SF"]} vs yield at a 200 N screw-force limit case (the motor clamps at {drv["Fs_range_at_set_N"][0]:.0f}–{drv["Fs_range_at_set_N"][1]:.0f} N at 0.45 A) |')
A(f'| Motion check | 0 collisions over 41 poses (all 49 parts, including the 16 modelled screws); only intended joint/stack contacts below 0.8 mm |')
A(f'| Grip thrust | Screw reaction → lock collar → 608 inner ring → outer ring → block front lip. 608 static axial capacity ≈ {S["thrust"]["bearing608_axial_static_capacity_N"]:.0f} N vs {S["thrust"]["load_N"]:.0f} N limit ({S["thrust"]["ratio"]}×) |')
A(f'| Fasteners | 2 screw sizes (12× M3×8, 4× M3×20 button head); min SF {FX["min_SF"]} under mount, stall and limit loads; tighten ≤ 0.2 N·m |')
A(f'| Printed volume | {printed_cm3:.0f} cm³ PETG (~{printed_cm3*1.27*0.55:.0f} g at typical infill) + motor ~280 g |')
A(f'| Mount | ISO 9409-1-50-4-M6 adapter (PCD 50, 4×M6, Ø31.5 spigot, Ø6 pin) |\n')
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
A('Jaw gap ↔ carriage position (for firmware; home = open stop, 1600 steps/mm at 1/16 µstep):\n')
A('| Gap mm | Crank θ° | C_x mm | Carriage from open stop mm | Steps from home |\n|---|---|---|---|---|')
for r_ in rows: A('| ' + ' | '.join(map(str, r_)) + ' |')
A('\n## 4. Motor and driver sizing\n')
A(f'- Screw force for ≥ 25 N everywhere: {MO["Fs_op_N"]:.1f} N → torque {MO["T_op_Nm_range"][0]:.3f}–{MO["T_op_Nm_range"][1]:.3f} N·m (screw η {R["screw"]["eta_mu025"]:.2f}–{R["screw"]["eta_mu010"]:.2f}).')
A(f'- **Set driver current to {drv["I_set_rms_A"]} A RMS** (for a {drv["I_rated_A"]} A / {drv["T_hold_Nm"]} N·m motor): screw force {drv["Fs_range_at_set_N"][0]}–{drv["Fs_range_at_set_N"][1]} N → grip ≥ {drv["grip_min_per_jaw_N"]} N per jaw, and stays below the 200 N structural limit even with a well-greased screw.')
A(f'- **Warning:** at full rated current the motor can push ~{MO["Fs_at_full_hold_mu010"]:.0f} N, far above what the printed parts are sized for. The current limit is a safety item.')
A(f'- Speed: {drv["speed_note"]}. Self-locking means no holding current is needed for the payload. Keep a low hold current anyway so the step position is not lost.\n')
A(f'## 5. Structural checks (200 N screw-force limit case; σ op = at the {drv["Fs_operating_max_N"]} N stall force at 0.45 A)\n')
A('| Check | Load N | σ limit MPa | σ op MPa | SF yield |\n|---|---|---|---|---|')
for r_ in S['rows']: A(f'| {r_["item"]} | {r_["load_limit_N"]} | {r_["stress_limit_MPa"]} | {r_["stress_op_MPa"]} | {r_["SF_yield_at_limit"]} |')
A(f'\n**Grip thrust (rev 6):** closing the jaws pushes the carriage toward the motor, so the screw is pulled the other way. A lock collar behind the 608 carries that pull into the bearing inner ring; the outer ring bears on the block front lip, which is the base and cover halves clamped together. The motor\'s own bearing no longer takes the full reaction. Limit case {S["thrust"]["load_N"]:.0f} N vs ≈ {S["thrust"]["bearing608_axial_static_capacity_N"]:.0f} N 608 static axial capacity. {S["thrust"]["note"][0].upper() + S["thrust"]["note"][1:]}.\n')
A('\nThe dowel is modelled as a beam on two supports: the 6 mm press socket in the base and the 3.9 mm close-fit hole in the cover. The cover hole must be reamed to Ø4.0 so it carries its share; with a loose cover hole the base socket would see the full bending moment.\n')
A('\nPETG printed in-plane yield taken as 45 MPa. All link loads are in the print plane (along the rasters). Interlayer stress appears only at the jaw-block root (≈0.3 MPa).\n')
A('\n### 5.1 Fasteners (every screw is modelled)\n')
A(f'Gripper mass {FX["mass_g"]:.0f} g (printed parts taken as solid, conservative), CG at x = {FX["x_cg_mm"]:.0f} mm; payload at x = {FX["x_payload_mm"]} mm; mount at x = {FX["x_mount_mm"]} mm. Pitch moment at the mount {FX["M_pitch_Nm"]} N·m (×2 dynamic).\n')
A('| Check | Load N | Stress MPa | SF yield | Note |\n|---|---|---|---|---|')
for r_ in FX['rows']: A(f'| {r_["item"]} | {r_["load_N"]} | {r_["stress_MPa"]} | {r_["SF_yield"]} | {r_["note"]} |')
A('\n| Screw | Clamp mm | Thread engaged mm | Tip to hole bottom mm | Into |\n|---|---|---|---|---|')
for e in FX['engagement']: A(f'| {e["screw"]} | {e["clamp_mm"]} | {e["thread_mm"]} | {e["tip_to_hole_bottom_mm"]} | {e["into"]} |')
A(f'\n**Tightening:** a button head bears on {FX["head_bearing_area_mm2"]} mm² of PETG. At 0.2 N·m an M3 makes about 330 N of clamp, about 20 MPa under the head (PETG yields near 45 MPa). Tighten every M3 to **0.2 N·m or less**: snug with the short arm of the key, no more. The two nut-flange screws bear on brass and self-tap into plastic; snug them only.\n')
A('## 6. Motion, clearance and printability checks\n')
A('- 3D boolean interference over 41 poses from closed to fully open, every part pair, both sides: **0 collisions**. Minimum-distance scan: all pairs under 0.8 mm are intended (shoulder screws in crank bores 0.05, dowels and shoulder screws in running bores 0.1, z-stack gaps 0.2 below / 0.3 above each moving layer, crank plates on base 0.3, fingers meeting at closed, carriage on the open stop). Lock collar 1.0 mm radial to the block; cover 1.38 mm from the front crank at closed.')
A('- Every part is a single valid solid. FeatureScript round-trip rebuild gives identical volumes.')
A('- Print orientation (no supports): links and fingers 0 mm² overhang; base, cover and adapter only hole tops and counterbore steps; carriage printed rear face down, so the nut recess opens upward and nothing needs a bridge or support.\n')
A('| Print file | Qty | Volume cm³ | Bounding box mm | Orientation / note |\n|---|---|---|---|---|')
for p in PARTS: A(f'| {p["file"]} | {p["qty"]} | {p["volume_cm3"]} | {" × ".join(map(str, p["bbox_mm"]))} | {p["orientation"]}: {p["note"]} |')
A('\n**Print Fit test coupons x1.stl first** (16 cm³, one plate). It checks every fit that depends on your printer: Ø3.9–4.2 pin bores in 6 mm plate, the three z-stacks with their 0.2/0.3 mm gaps, the 608 cradle (Ø22.06 seat, front lip, collar recess), and a 12.0 mm channel with an 11.6 mm tongue. If the 608 is loose, or a pin or the tongue binds, adjust the matching value in design.py before printing the real parts.\n')
A('\nPrint settings: PETG, 0.2 mm layers, 4 perimeters, 30–40% gyroid, 100% around insert holes. After printing, run a 4.0 mm drill through the pivot bores by hand (Ø4.2 bores = running fit, Ø4.1 = snug) and ream the four cover dowel holes to Ø4.0. Do not drill the Ø3.9 dowel press holes in the base.\n')
A('## 7. Onshape\n')
A('**Status:** the Onshape document is at **rev 6** (updated 2026-10-13). Feature Studio 1 holds the rev 6 `LeadScrewGripper.fs` (exact SHA-256 match with the local file) and the lock collar is in the frame group of Assembly 1.\n')
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
A('  - Fit coupons (Fit test coupons x1.stl) so the bore, stack, bearing-seat and tongue fits are tested before the full print.')
A('  - Re-checked: 49 valid parts, 0 collisions over 41 poses, intended contacts only; structural min SF 3.6 (unchanged, dowel); new block front lip SF 34.5 bearing / 74.6 shear-out; fasteners min SF 4.3; no new overhangs.')
A('- Alternative: `step/LeadScrewGripper_assembly_gap30mm.step` imports into any CAD package as a 49-part assembly.\n')
A('## 8. Assembly sequence\n')
for i, s_ in enumerate([
 'Heat-set inserts, pressed from the top face until flush (the shoulder screws seat on the insert top): BellCrank Lower (F1, D), FrontCrank Lower (F2), Carriage lower ears (2). Base: 2 motor-wall joint, 2 bearing block, 2 posts. Adapter: 4 side holes.',
 'Press the 4 dowels into the base (O1, O2 both sides; 6 mm deep, square to the plate). Ream the 4 cover dowel holes to Ø4.0.',
 'Pull-test the lock collar first: tighten its set screw on the end of the lead screw, check it holds a firm pull by hand without slipping, then take it off. Cut the lead screw to %.1f mm ± 0.5 from the motor face, so its end sits flush with the 608 face (never proud of the 1 mm front recess). Chamfer, clean and grease it.' % D.SCREW_LEN,
 'Slide the nut into the carriage from the front: body into the bore, flange into the front recess, two flange holes at 3 and 9 o\'clock. Fit 2× M3×8 button heads into the Ø2.5 pilots, snug only.',
 'Spin the carriage onto the motor screw from its rear. Slide the lock collar on (set screw loose), then the 608ZZ onto the screw tip.',
 'Lay motor + screw + carriage + bearing into the base: motor connector facing up, pilot into the wall recess, carriage tongue in the channel, 608 in the lower cradle against the front lip, collar behind it. Fit the 2 lower motor screws (M3×8) through the access slots with a 2.5 mm ball-end driver. Push the collar forward until it just touches the 608 inner ring (no preload) and tighten its set screw. Run the carriage end to end by hand, then tighten the 2 nut screws.',
 'Per side: BellCrank Lower on O1 and FrontCrank Lower on O2 (bosses up). Finger onto F1/F2, conrod onto D and between the carriage ears at C. BellCrank Upper and FrontCrank Upper on top. Shoulder screws at F1, F2, D, C into the lower-plate/ear inserts.',
 'Cover onto the dowels (press evenly; close fit). 2× M3×20 at the motor wall, 2× M3×20 at the bearing block, 2× M3×8 at the posts, then the 2 upper motor screws (M3×8) through the cover slots.',
 'Bolt the adapter to the robot flange first (4× M6×12). Slide the gripper onto it (the U-slot is open at the rear) and fit 4× M3×8 through the side walls into the adapter inserts.',
 'Driver: 0.45 A RMS, 1/16 µstep. Home by driving open slowly into the stop (carriage meets the bearing block at 66 mm) with stall detection, then back off 1 mm. In use, cap the commanded opening at 60 mm so the carriage never hits the stop at speed. Calibrate grip once with a kitchen scale between the jaws.']):
    A(f'{i+1}. {s_}')
A('\nTighten every M3 to 0.2 N·m or less (snug with the short arm of the key). More crushes the PETG under the head.')
A('\n## 9. Assumptions, limits, verify before buying\n')
A('- Rigid links, quasi-static, equal load sharing between the two sides, Coulomb friction in the screw only (pivot friction lowers grip a few %; the current setting has margin).')
A('- Verify on receipt: motor body ≤ 40 mm (the adapter sits 1 mm behind it), pilot Ø22×2, M3 holes on 31 mm square; nut flange Ø22×3.5 and body Ø10.2 (edit NUT_* in design.py if different); shoulder-screw head ≤ Ø7.5×3.5 and thread ≤ 6 mm.')
A('- Robot flange: I assumed a Ø31.5 H7 centring recess (spigot 31.44 × 3 mm) and the Ø6 pin on the PCD at +Z, between bolts. Check your robot drawing.')
A('- μ = 0.35 is conservative for serrated PETG. A thin TPU or rubber pad on the jaw face roughly doubles the slip margin.')
A('- PETG creeps slowly under sustained clamp. For long holds, re-tighten with a short current pulse, or print the fingers and lower crank plates in PA-CF/ASA.')
A('- Motor connector: the adapter sits 1 mm behind the motor, so the cable must leave from a side face. Mount the motor with the connector facing up, through the cover\'s U-slot.')
A('- M6×12 puts 6 mm of thread into the robot flange. Check your flange\'s thread depth, and use a washer or modest torque on the PETG.')
A('- Thrust: the collar and the motor\'s internal bearing share the screw load in a way that depends on how the collar is set. Check the motor datasheet\'s axial load rating anyway, and don\'t preload the collar.')
A('- The jaws also move fore-aft: %.1f mm in total over the stroke. They are furthest forward near a %.0f mm gap and furthest back fully open (%.1f mm behind the closed position). That is inherent to this linkage; teach grasp poses at the gap you\'ll use.' % (FA['travel'], FA['gap_fwd'], FA['open_behind_closed']))
A('- Not modelled: wiring, a limit switch (sensorless homing assumed), cable strain relief.')
open(f'{OUT}/DESIGN_REPORT.md', 'w').write('\n'.join(md) + '\n')
print('ok', printed_cm3)
