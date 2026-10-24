# Lead Screw Gripper v2

Design work for version 2 of a lead-screw-driven parallel gripper: a parametric Python/CadQuery model that generates Onshape FeatureScript, with local checks for collisions, clearances, structure and printability.

**Start here:** read [`GRIPPER_HANDOFF.md`](GRIPPER_HANDOFF.md). It holds the goal, the rules, the agreed v2 changes and the step order.

## Layout

| Path | What it is |
|---|---|
| `GRIPPER_HANDOFF.md` | v2 plan and rules (read first) |
| `docs/offset_pad_sets_concept_v4.png` | Concept: narrow and wide bolt-on tip sets |
| `gripper_fabrication_rev6/` | Rev 6 baseline, kept as the reference. Don't edit it. |
| `gripper_fabrication_rev6/source/` | Parametric model and checks. `design.py` + `params.py` are the single source of truth; `fs_gen.py` writes the FeatureScript |
| `gripper_fabrication_rev6/DESIGN_REPORT.md` | Rev 6 design and validation report |
| `gripper_fabrication_rev6/HANDOFF.md` | Rev 6 history and the regenerate-after-a-change pipeline |
| `gripper_fabrication_rev6/onshape/LeadScrewGripper.fs` | Generated FeatureScript for Onshape |
| `gripper_fabrication_rev7/` | v2 work (created in step 1 of the handoff) |

STL, STEP and build-guide images aren't stored. Regenerate them with `export.py` (run it before `fit_coupons.py`) and `guide_render.py`.

## Setup (Ubuntu)

Keep CAD tools out of the system Python:

```bash
python3 -m venv ~/.venvs/gripper
source ~/.venvs/gripper/bin/activate
pip install cadquery numpy scipy matplotlib pyvista
```

Run the scripts from inside a `source/` folder, for example `cd gripper_fabrication_rev6/source && python3 check.py 41`. Run `deactivate` when you're done.
