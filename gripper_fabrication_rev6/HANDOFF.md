# Gripper project: status and resume point (rev 6, local and Onshape; updated 2026-10-16)

## Status: done
History, oldest first. Each item gives the numbers at the revision it names; the current state is the **Rev 6** section below.

1. Reference mechanism measured from the video (source/data, ref_ratios.py).
2. Linkage sized (L = 28 mm, reference ratios kept). Kinematics and force model in analysis.py → results.json.
3. Architecture: double-shear sandwich (base + cover, two-plate cranks, clevis carriage). NEMA17 Tr8x2 lead screw, floating nut, 608ZZ tip support, ISO 9409-1-50-4-M6 adapter.
4. Professional styling pass, all requirements kept:
   - one tapered convex housing outline with a U-slot for the motor
   - consistent corner radii
   - flush counterbored fasteners
   - rounded finger profile with grooved jaws
   - chamfered NEMA body
   - graphite / silver / orange palette
5. Local CAD in design.py + prims.py (single source of truth). Checks at rev 3 (rev 6: 49 parts, see below):
   - 32 valid solids
   - 0 collisions over 41 poses
   - only intended contacts below 0.8 mm
   - printability OK
6. Structural and driver checks (structural.py): min SF 4.4 at the 200 N limit at rev 3 (rev 6: 3.6, at the dowel); driver set to 0.45 A RMS.
7. Onshape document "Lead Screw Gripper" (https://cad.onshape.com/documents/95059d2be7659a57baadd94c), created via Claude in Chrome.
   - Feature Studio 1 holds onshape/LeadScrewGripper.fs. Pasted with the Ace editor; whitespace-normalised SHA-256 matched the local file.
   - Part Studio 1: feature at gap 30. When first built (rev 2), all 32 parts matched local volumes within 0.4 mm³ (rev 6: 49 parts within 0.9 mm³).
   - Assembly 1 (rev 2): 32 instances; frame fixed; 6 rigid groups (rev 6: 49 instances).
   - Mates: revolutes at O1/O2, cylindricals at F1/D, balls at F2/C, slider on the screw axis (1 DOF). Base is the only fixed instance (the frame group carries the rest).
   - Slider limits −20.83 mm (open, 66 mm gap) … +11.2 mm (closed, 0 mm gap). The mate's +Z points toward the motor. Flip primary axis is off.
   - Verified 2026-10-09: the server solve (POST /matevalues) at both limits gives finger travel +18.00 / −15.00 mm, matching the local kinematics. Past-limit requests clamp. Animate runs. Left at the 30 mm home pose.
   - Fixed that session:
     - Flip primary axis was on, which turned the carriage 180°.
     - Limits written through REST had value 0, which locked the slider. Write both the expression and the SI value (metres).
     - Cover was fixed as well as Base; Cover is now unfixed.
   - Rev 3 (2026-10-09):
     - Finger: straight back edge, no clearance bites; r3 nose and heel; heel at x = 36.5. The O2 spacer clears it by 1.48 mm over the stroke, 1.05 mm with 1° overtravel. (Later moved to x = 37 mm, ≥ 1.18 mm with 1° overtravel; see DESIGN_REPORT §7.)
     - Motor-screw access slots: r1 corners for a flat head seat; in the base they run up through the wall half.
     - Patched into Feature Studio 1 by line replacement (normalised hash matched local: 3ece5fdfacd163ac) and committed. All 32 Onshape volumes match local within 0.1 mm³. Assembly motion re-verified at both limits.
     - Assembly mate-connector markers hidden (right-click any mate connector → Hide all mate connectors).
     - FeatureScript MCP: 0 requests used for rev 3.
   - Rev 4 (audit fixes, all items in AUDIT_REV4.md):
     - carriage front-loaded nut with 2× M3×8 button heads; adapter side walls and M3×10 at z 4 / 16.5 (M3×8 since rev 5); M3×8 motor screws
     - close-fit cover dowel holes; flush jaw block
     - removed no-function steps and slivers
     - Feature Studio patched (normalised hash aa31a05b050df5c7), Onshape volumes within 0.7 mm³ of local, all 19 assembly features OK, motion re-verified at both limits
     - The carriage body must stay an 'ext' op (a 'box' op changed its part identity and broke the carriage mates)
   - Rev 5 (lean fastener set, every screw modelled):
     - 16 ISO 7380 button heads in design.py FASTENERS (12× M3×8, 4× M3×20); nut flange got its 4 holes; motor-slot corners r0.5 (r1 touched the Ø5.7 head)
     - Local: 48 parts, 0 collisions over 41 poses; fasteners.py min SF 4.3 (side-wall hole bearing); tighten M3 ≤ 0.2 N·m
     - Feature Studio patched (normalised hash 1a86cc929f127e29) and committed; 48 Onshape volumes within 0.7 mm³ of local; the 8 new specs are appended at the END of SPEC so existing part ids stay stable
     - Assembly 1: 16 screw instances inserted at identity (slider reset to 0 first); 14 added to "Frame (fixed)", 2 nut screws to "Carriage + nut + C pivots"; 19/19 features OK; slider re-verified at both limits; nut screws follow the carriage
     - Onshape evCollision at gaps 0/30/66 (moving parts placed by the local kinematics inside an eval script): only intended overlaps. Record: source/results_onshape_rev5.json
     - FeatureScript MCP: 0 requests for rev 5 (total still 71)
   - Mates were created through Onshape's assembly features endpoint from the browser session. Query type: BTMPartStudioMateConnectorQuery-1324, featureId "<psFeatureId>.mc<j>".
   - FeatureScript MCP: 15 API requests total (56 → 71). Browser-session calls are not counted.
8. Package: stl/, step/, BOM.csv, DESIGN_REPORT.md, images/, onshape/, source/.
9. Build guide (Claude Docs, updated for rev 6 on 2026-10-16): https://claude.ai/code/artifact/5f313246-5418-4ccc-8875-ba779bcd4216. Its step pictures are images/build_guide/, made by source/guide_render.py.

## Rev 6 (2026-10-13): local model and Onshape
Why: an outside review flagged that the grip reaction pulled the screw out of the motor with nothing but the motor's own bearing to stop it, 0.1 mm z-stack gaps, and printed fits that were never tested.
- Thrust: Ø8 lock collar (OD 14 × 7, set screw) behind the 608. Path: screw → collar → 608 inner ring → outer ring → block front lip (base + cover halves). 608 static axial ≈ 685 N vs the 200 N limit. Front lip SF 34.5 in bearing, 74.6 in shear-out.
- Block 18.0 → 22.5 mm long (X 16.55…39.05). 608 seat X 24.05…31.05. Collar in an Ø16 pocket X 17.05…24.05. 1 mm deep front recess r6.3 clears the inner ring and the screw end. R6 front corners and block bolts at (X_BRG1 + 3.5, ±8.5) keep the cover 1.38 mm from the front cranks at full close. Insert-hole wall ≥ 1.33 mm.
- Screw cut 81.5 mm ± 0.5 (was 78.0); its end sits flush with the 608 face.
- Layer stack: lower plates 0.3–6.3, finger / conrod 6.5–14.1 (7.6 mm = 38 layers of 0.2), upper plates 14.4–18.2, screw axis 10.3. Gaps 0.2 below and 0.3 above each moving layer.
- Fit test coupons x1.stl (source/fit_coupons.py): Ø3.9–4.2 bores, the three z-stacks, the 608 cradle, channel + tongue. Print it first.
- Checks: 49 valid parts; 0 collisions over 41 poses; only intended contacts under 0.8 mm (clearance_rev.json); structural min SF 3.6 (dowel, unchanged); fasteners min SF 4.3; overhang unchanged; 333.3 cm³ in 16 printed pieces.
- fs_gen.py: the LockCollar spec is appended at the END of SPEC, so existing part ids stay stable. The lead screw part is now named "(cut 81.5mm)".
- Onshape (done 2026-10-13, 0 FeatureScript MCP requests; record in source/results_onshape_rev6.json):
  - Slider set to 0 first. Feature Studio 1 updated with a line patch through the browser session REST (POST /featurestudios; writes need the X-XSRF-TOKEN header from the XSRF-TOKEN cookie). Exact SHA-256 matches the local file (e8dd4f49c0a87082).
  - Part Studio: 49 parts, feature OK, all volumes within 0.9 mm³ of local.
  - Assembly 1: lock collar (partId RVOD) inserted at identity and added to "Frame (fixed)" (25 members); 49 instances; 19/19 features OK.
  - Slider: −20.83 → carriage +20.83, fingers ±18.00 (gap 66); +11.2 → carriage −11.20, fingers ∓15.00 (gap 0); −30 clamps. Left at 0, cover visible, mate connectors hidden.
  - Element ids for browser-session REST: Feature Studio 60047d773e42d7742cd036f6, Part Studio c621af76ed54a2221b355024, Assembly 621a9c0dfd69e86e15b36ea6; slider mate featureId MFHyZ2wXcuTOT+Pu3 (values in metres: −0.02083 open, +0.0112 closed, 0 home).
  - evCollision (FS eval): collar only abuts the screw and the 608; 1.0 mm to base and cover. Carriage moved to the open stop: abuts only the base; nut 3.1 mm from the collar.
- Pictures: images/rev6_changes_thrust.png (thrust path, rev 5 vs rev 6), images/rev6_changes_fits.png (layer gaps and fits), images/rev6_thrust_section.png (section through the thrust path). Onshape captures (images/onshape_*.png), build-guide pictures, render_final.png and sections_final.png were all redone for rev 6 on 2026-10-16.
- Still open: collar set-screw holding on Tr8 threads (hand pull test), the motor's axial load rating, and the fit-coupon results.

## If the design changes
Edit design.py (or params.py), then from source/:
- python3 analysis.py; python3 structural.py   (results.json, results_struct.json)
- python3 check.py 41   (writes check_report.json)
- python3 fasteners.py
- python3 clearance_scan.py   (writes clearance_rev.json; about 2 minutes)
- python3 fit_coupons.py   (if a fit value changed; also updates print_parts.json)
- python3 fs_gen.py   (writes source/ and onshape/LeadScrewGripper.fs, always identical)
- python3 fs_roundtrip.py   (rebuilds the .fs specs with CadQuery; writes fs_volumes.json)
- paste the new .fs into Feature Studio 1 and Commit
- python3 export.py; python3 overhang.py; python3 make_docs.py
- python3 guide_render.py; python3 render2.py; python3 section.py   (pictures)

Mate connector order (mc index) is fixed by mateConnectorSpecs in fs_gen.py. Keep it stable, or the assembly mates must be recreated.

## Re-running locally
Set up a Python venv as in the README at the repo root, then: cd source; python3 analysis.py; python3 structural.py; python3 fasteners.py; python3 export.py; python3 make_docs.py
