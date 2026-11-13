# Lead-Screw Parallel Gripper (v2, rev 7)

A 3D-printable parallel gripper for robot arms with an ISO 9409 flange. One NEMA 17 stepper turns a Tr8×8 lead screw; mirrored bell-crank and parallelogram linkages keep both jaws parallel over a 0–60 mm stroke (20–80 mm with the wide tips). Predicted grip: at least 26 N per jaw at a 0.7 A current limit, against 21 N needed for a 500 g part.

**Status:** a first prototype was printed and assembled; some parts rubbed, so it is being reprinted. The ROS 2 side runs in simulation and against a simulated Pico. Nothing has been measured on hardware yet.

## Layout

| Path | What it is |
|---|---|
| `gripper_fabrication_rev7/` | The design: parametric model and checks (`source/`), `DESIGN_REPORT.md`, `BOM.csv`, print list, Onshape FeatureScript, images |
| `gripper_fabrication_rev7/firmware/` | Raspberry Pi Pico firmware: `bench.py` (bring-up tests and stand-alone demo) and the ROS 2 firmware (`ros_main.py`, `gripper_core.py`, `hal_pico.py`), with laptop tests |
| `docs/BUILD_AND_TEST_GUIDE.md` | Assembly and bench-test steps |
| `docs/offset_pad_sets_concept_v4.png` | Concept: narrow and wide bolt-on tip sets |
| `ros2_ws/` | ROS 2 Jazzy workspace: robot description from Onshape, linkage kinematics, Gazebo grasp test, ros2_control hardware interface. See [`ros2_ws/README.md`](ros2_ws/README.md) |

STL, STEP and build-guide images aren't stored. Regenerate them with `export.py` (run it before `fit_coupons.py`) and `guide_render.py` in `gripper_fabrication_rev7/source/`. The rev 6 baseline is in the git history.

## Setup (Ubuntu)

Keep CAD tools out of the system Python:

```bash
python3 -m venv ~/.venvs/gripper
source ~/.venvs/gripper/bin/activate
pip install cadquery numpy scipy matplotlib pyvista
```

Run the scripts from inside `gripper_fabrication_rev7/source/`, for example `python3 check.py 41`. Run `deactivate` when you're done.
