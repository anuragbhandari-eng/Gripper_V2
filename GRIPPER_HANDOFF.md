# Lead Screw Gripper v2: Design Handoff for Claude Code

Owner: Anurag Bhandari. Updated: 2026-10-24.
Read this whole file before doing anything. Companion image: `docs/offset_pad_sets_concept_v4.png`.

---

## 0. Ground rules (read first)

### Repository and Onshape
- This repo (`Gripper-Claude_Onshape_V2`) is standalone and holds only the v2 design work.
- **Git:** show `git status` and `git diff` before any commit. Commit or push only when Anurag says so, and explain each git command the first time it comes up. Don't add other remotes or reference other repositories.
- **The v2 design goes in the Onshape document `GripperV2`** (ids in section 3). Don't modify the original document "Lead Screw Gripper"; it stays as the rev 6 record.
  - `GripperV2` was created on 2026-10-24 as a copy of the original, through Chrome. It keeps Assembly 1 and its 19 mates, which attach to the feature's named mate connectors.
- **Leave `gripper_fabrication_rev6/` unchanged as the reference.** Do v2 work in a new folder, `gripper_fabrication_rev7/`, starting from a copy of `rev6/source/`.

### Session rules
- **Don't start designing until Anurag says go.** Work one small step at a time and check in after each.
  - **Override (2026-10-24, from Anurag):** commit automatically after each step (local commits; still no push) and don't stop for questions until the complete v2 design is in `GripperV2` in Onshape. Make the calls yourself and list them in the report.
- **Never sign in to anything** (Onshape, GitHub, anything else). Ask him to sign in.
- **No `sudo`.** Show him the command and let him run it in his own terminal.
- **Keep CAD tools out of system Python.** Use the venv `~/.venvs/gripper`, and never install into the system Python that ROS 2 uses.
- **Explain new code and commands in plain words.** He's new to coding and Linux and wants to be able to explain every part himself.
- **Honest numbers, no overclaiming.** Give complete files, not diffs. Keep messages short.
- **Never publish, show or mention the private reference** (`lead_screw_gripper_video.mp4`, `lead screw image.png`, or the reference design they show).

### Design language
Simple and cohesive. Every feature must serve a function. No decorative features and no mixed edge treatments.

### Materials and parts
- **Printed parts are ABS, not PETG** (done in step 2). The material lives in one place, `design.py` (`MAT`, `MAT_SY`, `MAT_SZ`, `MAT_RHO`), and every script reads it from there.
  - Parts are printed at Anurag's university fablab; the spool brand isn't known. So the values are conservative generic ABS: 30 MPa in-plane yield (low end of 30–40), 12 MPa across layers, 1.04 g/cm³.
  - Result vs rev 6: plastic safety factors drop by a third. Structural min SF 3.6 → **2.9** (finger bore at F2 and finger jaw root; now the plastic governs, not the dowel). Fasteners min SF 4.3 → **3.0** (side-wall hole bearing). Gripper mass 763 → 695 g.
  - M3 tightening limit lowered from 0.2 to **0.15 N·m**, so the stress under a button head keeps SF ≈ 2.
  - The generated `.fs` now sets ABS and 1.04 g/cm³ on the printed parts; `GripperV2` needs that update in step 8.
- ABS shrinks and warps more than PETG. Reprint the fit coupons in ABS on the fablab printer and retune the fits from them. Print in an enclosure, part-cooling fan low or off, brim on the base and cover.
- **Pads are printed TPU 95A** (Anurag's printer handles TPU).
- **Buy parts that arrive quickly from Amazon US.** Prefer fast-delivery listings, and give the exact search terms or a link plus the price.

---

## 1. Goal

v2 upgrades the rev 6 gripper so it can be **built, run from ROS 2, and shown in a portfolio**: grasps on varied objects, simulation, and side-by-side sim-to-real.

**Hard constraint: the linkage geometry stays fixed.** That means pivots O1/O2/F1/F2/D/C, crank lengths, the conrod and the carriage pin line. Fingertips, housing details, drivetrain parts, mounts and electronics may change.

---

## 2. What's in this repo

| Path | What it is |
|---|---|
| `README.md` | Repo overview and Python setup |
| `GRIPPER_HANDOFF.md` | This file |
| `docs/offset_pad_sets_concept_v4.png` | Concept image: narrow and wide tip sets, pads extended 12 mm |
| `gripper_fabrication_rev6/` | **Current design (rev 6). Read only; it's the reference.** |
| `rev6/HANDOFF.md` | CAD history, Onshape details, and **the regeneration pipeline (what to rerun after a change)**. Read it. |
| `rev6/DESIGN_REPORT.md` | Full design report: kinematics, motor and driver sizing, structural checks, assumptions, and a jaw-gap → carriage table |
| `rev6/source/design.py` + `params.py` | **Single source of truth** (Python + CadQuery CSG ops). `params.py` holds the reference ratios. |
| `rev6/source/` (other scripts) | `kin.py` kinematics; `analysis.py` force model; `structural.py`, `fasteners.py` checks; `check.py` validity and collisions over N poses; `clearance_scan.py`; `overhang.py`; `fit_coupons.py`; `fs_gen.py` generates the FeatureScript from design.py; `fs_roundtrip.py` rebuilds the .fs specs and writes volumes; `export.py`; `make_docs.py`; `guide_render.py`, `render2.py`, `section.py` |
| `rev6/source/*.json` | Results: `results.json`, `results_struct.json`, `results_fasteners.json`, `check_report.json`, `clearance_rev.json`, `overhang_report.json`, `fs_volumes.json`, `results_onshape_rev6.json` |
| `rev6/onshape/LeadScrewGripper.fs` | Generated FeatureScript, identical to what's in Feature Studio 1 |
| `rev6/BOM.csv`, `print_parts.json`, `images/` | BOM, print list, renders. STL/STEP aren't stored: regenerate with `export.py` |

---

## 3. Rev 6 facts to keep in mind

All lengths in mm, in the CAD frame:
- **Axes:** x runs along the screw toward the jaws, y is lateral (the U finger is on +y; L mirrors y), z is up, z = 0 is the top of the base plate.
- **Origin:** O1 at x = 0. Screw axis at y = 0, z = 10.3.
- **Layers (z):** lower crank plates 0.3–6.3; finger and conrod 6.5–14.1; upper plates 14.4–18.2; raised jaw block up to 26; cover 22.1–29.5.

### Linkage (fixed)

| Item | Value |
|---|---|
| O1 | (0, 50.97) |
| O2 | (32.27, 21.09) |
| Crank length | 28 |
| Bell-crank arm O1–D | 20.91, 90° behind O1–F1 |
| Conrod D–C | 22.68 |
| Carriage pin line | y = 24.91 |
| Crank angle θ | −15.52° (closed) to 65.64° (66 mm hard stop) |

- Jaw gap = 56·(sin θ − sin(−15.52°)).
- Carriage pin Cx goes −27.49 → +4.55: 32.0 mm of travel.
- Each finger also moves 16.5 mm fore-aft in total, reversing near a 15 mm gap. Fully open sits 15.4 mm behind closed.
- Mechanical advantage (grip per jaw ÷ screw force): 0.35 closed, 0.75 at 60 mm, 1.36 fully open.

### Finger (design.py; local frame at F1; the finger translates without rotating)
- Variables: `FACE_Y` (jaw face line), `JAW_X0 = 37` (heel), `JAW_X1 = 70` (end of the serrated face), `TIP = (74, −40)`, `EXT_X0` (start of the raised jaw block, about x = 41 in the generated .fs).
- r3 nose, heel and top corner. Serrations are V-grooves at 2 mm pitch, 0.8 mm deep.
- **The heel sits at x = 37 so it clears the O2 spacer sweep by ≥ 1.18 mm, even with 1° overtravel.** Any v2 change near the heel must keep that clearance.

### Drive and limits
- Tr8x2 screw (2 mm lead) cut to 81.5 mm. Thrust path: screw → Ø8 lock collar → 608ZZ → front lip of the bearing block (block at X 16.55–39.05; 608 seat at X 24.05–31.05; screw end flush with the 608 face at 31.05).
- TMC2209 driver at **0.45 A RMS (a safety limit)**: 174.6 N stall force at that current, against a **200 N** structural design case. Lowest safety factor is 3.6 (dowel bending); fasteners 4.3.
- **Homing plan:** stall into the 66 mm hard stop, back off 1 mm, then cap commanded opening at 60 mm.
- At the open stop the carriage abuts only the base.
- The **two slots through base and cover are the motor-screw access slots.** Keep them.

### Onshape (original document; don't edit it)
- https://cad.onshape.com/documents/95059d2be7659a57baadd94c
- Feature Studio `60047d773e42d7742cd036f6`, Part Studio `c621af76ed54a2221b355024`, Assembly `621a9c0dfd69e86e15b36ea6`.
- 49 parts. 19 mate features, with one slider (−20.83 mm open … +11.2 mm closed, relative to the 30 mm pose).

### Onshape `GripperV2` (the v2 document; edit only this one)
- https://cad.onshape.com/documents/21eb00e5286d05130362fe39 (workspace `68767ad57d3e567f86546d97`)
- Feature Studio `fde66efd92d58004e5d8d280`, Part Studio `f5d5018b17c7abc84df66214`, Assembly 1 `b8167d0fe4641b107965a991`.
- Also copied: the assembly "Robot export" `38318d1f8e8ae84b4e65fae0` (24 mate features) and two BOM tabs.
- Checked at creation: 49 parts, 19 mate features in Assembly 1, and Feature Studio code identical to `rev6/onshape/LeadScrewGripper.fs` (SHA-256 starts `e8dd4f49c0a87082`).

### ROS 2
A ROS 2 version for v2 is a later phase. Where it lives is Anurag's decision, made when that phase starts.

---

## 4. Agreed v2 changes

### A. Drivetrain: Tr8x2 → Tr8x8
- Same NEMA17 40 mm external linear stepper, with the **Tr8x8** (4-start, 8 mm lead) screw version, cut to 81.5 mm.
- Tr8x8 brass nut. It must match the 22 mm flange and 10.2 mm body, and the 4 flange holes; verify on the listing.
- Effects: full stroke drops to 4 revolutions (about 0.4 s at 600 rpm); the screw becomes back-drivable (efficiency about 0.6–0.66); the grip is no longer held with power off.
- **Re-run `analysis.py` and `structural.py` with the new lead.** Thrust per amp drops by roughly half, so the driver current can be raised. Keep screw force at or below the 200 N design case and report the new grip-per-jaw numbers.
- Update the homing and steps-per-mm notes: 1600 → 400 steps/mm at 1/16 microstepping.

### B. Bolt-on tip blocks, two offset sets (see the concept image)
- **Split each finger at the raised-jaw-block edge (about x = 41).** The seam can't move back: the F2 boss and the heel clearance sit behind it.
- Tip blocks fasten with **2× M3 into heat-set inserts** in the finger body. Choose the screw direction and placement, and add them to the `FASTENERS` list in design.py.
- **Narrow set:** contact face on the current face line. Range 0–66 mm.
- **Wide set:** face **10 mm farther out per side**. Range about **20–86 mm**.
- **Length:** both sets extend **12 mm forward**, so the face runs from about x 41 to **83** (about 42 mm long instead of about 30).
  - Narrow tip keeps the current nose shape, shifted forward.
  - Wide tip ends **blunt**, about 8 mm thick at the end. A sharp wedge would be too weak.
- **Contact face:** 2 mm printed TPU 95A, held mechanically (a slide-in dovetail is planned; no glue). No serrations.
- **Must fix:** with the wide set, the finger body just behind the seam (heel region x 37–41, on the old face line) sits about 10 mm proud of the wide face. Trim it back on both fingers and keep the ≥ 1.18 mm O2-spacer clearance.
- Add a **"Tip set" (Narrow / Wide)** dialog option to the generated feature. The gap readout should then show the true face-to-face gap for the chosen set.
- **Checks:** both sets through `check.py` (all poses), the clearance scan, tip-block strength at the seam, and the narrow set at gap 0.
- **Trade-offs to report:** the gripper is 12 mm longer, and pin loads are roughly 15–20% higher when gripping at the far tip.

### C. Position encoder at the screw's front end
- AS5600 board with a 6×2.5 mm diametric magnet on the screw end, held by a printed centering cap. Air gap 0.5–3 mm.
- Board goes in a **pocket in the bearing block's front**, ahead of the 608 (about X 31.05–39.05). Mind the front lip that carries the thrust: re-check its safety factor. Add a wire exit.
- The AS5600 is single-turn, so firmware counts turns (4 revolutions over the full stroke with Tr8x8).

### D. Controller mount and cabling
- Raspberry Pi Pico + TMC2209 on the **cover top**: bosses or heat-set inserts, an optional minimal lid, and a cable exit with strain relief. Route the motor cable.
- **ROS 2 link:** USB serial from the Pico.
- **Power:** 3S LiPo, about 650 mAh, XT30 plug, through a switch and a ~3 A fuse to the TMC2209 motor supply.
  - LiPo packs have no protection board. The Pico reads the pack voltage through a divider and disables the driver below about 10.5 V (3.5 V per cell). Charge only with a balance charger.
  - The Pico runs from USB, and from a small 5 V buck on the pack fed into VSYS through a Schottky diode, so both can be connected at once. Confirm against the "Powering Pico" section of the Pico datasheet.
  - Battery placement (stand base or cover) is decided in this step.

### E. Keep fs_gen and GripperV2 stable
- **Append new SPEC entries at the END** so existing part ids stay stable.
- Keep the `mateConnectorSpecs` order.
- The carriage must stay an `ext` op.
- Existing feature instances keep their old dialog values after a code change. Set them, then confirm with Mass properties.

### F. Bench stand (no robot arm for now)
- A stand that holds the gripper for bench demos and sim-to-real tests.
- Proposed: mount it through the existing ISO 9409-50-4-M6 adapter face, so the same gripper later bolts to an arm unchanged.
- Propose jaw orientation, height and footprint to Anurag before designing.

---

## 5. Decisions (answered 2026-10-24)

1. **Onshape `GripperV2`:** a copy of the original, created through Chrome. Done; ids in section 3.
2. **Power:** a small, light battery: 3S LiPo (~650 mAh, XT30), plus a balance charger, since Anurag doesn't have one. The 12 V adapter idea is dropped. Details in 4D.
3. **Load cell:** dropped.
4. **Pad material:** printed TPU 95A, held mechanically. Final shape in step B.
5. **Robot arm:** none for now. Plan for a bench stand (4F).
6. **Print material:** ABS, not PETG (see "Materials and parts" in section 0).
7. **Parts sourcing:** Amazon US, choosing items that deliver quickly.

---

## 6. Workflow and step order

**Local check loop first, for every revision** (pipeline in `rev6/HANDOFF.md`, run inside `rev7/source/`):
- `analysis.py`, `structural.py`
- `check.py 41`
- `fasteners.py`
- `clearance_scan.py`
- `overhang.py`
- `fit_coupons.py` (if fits change)
- `fs_gen.py`, then `fs_roundtrip.py` (compare volumes)
- renders

Every part must be one valid solid, with zero collisions over all poses and printable with no supports. Look at the renders.

**Onshape, only after local checks pass, and only in `GripperV2`:**
- **Route:** Claude in Chrome on cad.onshape.com, with Anurag logged in.
- **Updating the Feature Studio:**
  - Paste through the Ace editor, or patch through browser-session REST (`POST /featurestudios`, with the `X-XSRF-TOKEN` header from the `XSRF-TOKEN` cookie). Both cost 0 FeatureScript MCP requests.
  - Read the code back, compare its hash against the local file, then Commit.
- **Volumes:** compare Part Studio volumes against local.
- **FeatureScript MCP:** **5 API requests or fewer per session**, counted on his Onshape API counter. Ask before using more. `test_feature` costs about 9 requests: don't use it without asking.
- **FeatureScript gotchas:** version 3083; `box` is a reserved word; a checkbox default needs `"Default" : true`; never import the Part Studio from the Feature Studio.

**Steps (check in after each):**
1. Copy `rev6/source/` → `rev7/source/` and confirm the pipeline reproduces rev 6 results unchanged.
2. **ABS:** switch the material constants to ABS, re-run the structural and fastener checks, and update the print notes. Anurag prints the fit coupons in ABS; retune the fits from his results.
3. **B:** tip blocks + TPU pads, both sets → checks + renders → show Anurag.
4. **C:** encoder pocket and magnet cap.
5. **D:** controller mount, battery wiring and cable exits.
6. **F:** bench stand.
7. **A:** Tr8x8 constants, re-run analysis and structural checks, update the docs.
8. Onshape `GripperV2`: Feature Studio, Part Studio and assembly checks.
9. Later, and only where Anurag says: ROS 2 for v2 (joint limits and tip-set offsets, export from `GripperV2`).

---

## 6a. Status (2026-10-24): v2 design complete, local and in `GripperV2`

Steps 1–8 are done and committed on `v2/handoff-decisions` (not pushed). Full numbers: `gripper_fabrication_rev7/DESIGN_REPORT.md` (section 1a has the v2 summary and the Pico wiring table). Onshape record: `rev7/source/results_onshape_rev7.json`.

- **Checks:** 72 valid parts, 0 collisions over 41 poses for both tip sets (`check.py 41`; run `GRIPPER_TIPSET=wide python3 check.py 41` for the wide set, which writes `*_wide.json`). Only intended contacts under 0.8 mm.
- **Structure (ABS 30 MPa, 200 N screw-force limit, far-tip grip at the 66 mm stop):** min SF 1.7 (finger bore and boss at F2, tip screws). At the 60 mm firmware cap these rows are 1.81× higher (≥ 3.0). Tongue alone carries the seam moment at SF 2.7. Fasteners min SF 2.3.
- **Drive:** Tr8x8, driver 0.70 A RMS (stall 78–110 N), grip ≥ 26.8 N per jaw, 400 steps/mm, full stroke 0.4 s, not self-locking.
- **Onshape `GripperV2`:** Feature Studio updated (SHA-256 `05ef67f130b2d4b1`), 72 parts within 1.3 mm³ of local, dialog has Tip set + Include bench stand. Assembly 1: 72 instances, 21/21 features OK, new groups "Finger U + tip" / "Finger L + tip", slider verified at both limits, left at 0. FeatureScript MCP requests used: 0.

**Calls made without asking (Anurag said not to stop for questions):**
1. Tip joint: finger keeps a 20 mm tongue; tip block slides up onto it, 2× M3×16 from the top into inserts in the tongue. Pad: one TPU pad for both sets, 45° dovetail key sliding in from the rear.
2. Wide offset kept at 10 mm. Side effect: the F2 boss (3–14 mm behind the seam) sits 1.9 mm proud of the wide pad face. A 7 mm offset would clear it (gap 14–80).
3. Encoder: screw cut 3 mm shorter (78.5 mm); printed puck with the magnet inside the 608 bore; board in a slot across the block. The block bolts moved to rear ears because the board spans their old position.
4. Controller: protoboard on 4 M3×10 standoffs into inserts in the cover top (the cover prints top-down, so no printed bosses). Strain relief = zip ties to the board grid.
5. Bench stand: gripper hangs jaws-down from a 2020 × 400 column; printed head bracket (M6×20 into nuts) and base with battery tray.
6. Driver current is computed in `structural.py` (lowest 0.05 A step that meets the 25 N grip target).
7. Found and fixed: `prims.mirror_ops` mirrored `extx` profiles in z instead of y (first used by the pad dovetail).

**Still open (for Anurag):**
- Print `13_FitTest_coupons.stl` in ABS at the fablab and report the fits; retune `R_RUN`, `R_SNUG`, the 608 seat etc. from the results.
- Buy parts (section 7 / BOM.csv). Check on receipt: AS5600 board ≤ 23 × 23 mm with the chip centred; Tr8x8 nut flange and holes; motor screw ≥ 78.5 mm usable.
- Firmware (Pico): STEP/DIR/EN, UART config, stall homing, AS5600 turn counting, battery cut-off at 10.5 V. Pin map in the report.
- ROS 2 phase: update the "Robot export" assembly with the tip parts.

## 7. Planned purchased parts (approximate, Amazon US)

| Item | ~Cost |
|---|---|
| NEMA17 40 mm linear stepper, Tr8x8 screw + brass nut | $20 |
| TMC2209 + Raspberry Pi Pico | $12 |
| AS5600 board + 6×2.5 mm diametric magnet | $5 |
| M3 heat-set inserts + screws | $5 |
| TPU 95A filament for pads (1 spool) | $20 |
| 3S LiPo, ~650 mAh, XT30 | $15–20 |
| LiPo balance charger | $25–35 |
| Switch, ~3 A fuse, XT30 pigtail + extension, 5 V buck, Schottky diode, divider resistors | $15 |
| 50 × 70 mm protoboard, 4× M3×10 standoffs | $10 |
| 2020 extrusion 400 mm, M5 T-nuts + screws, 4× M6×20 + M6 nuts | $20 |
| M3×16 button heads (4) and 4 more heat-set inserts | in the M3 kit |
