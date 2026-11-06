# Lead-screw gripper in ROS 2 Jazzy

The rev 6 lead-screw parallel gripper as a ROS 2 robot: a robot description exported from the Onshape assembly, a kinematics node that turns one jaw-gap value into all nine joint positions, and a Gazebo Harmonic simulation with ros2_control that closes on a block, lifts it and sets it down.

Everything here is **simulated**. The gripper has not been built or tested on hardware yet.

| RViz: the node drives the full linkage, 0–66 mm | Gazebo: close, lift 50 mm, hold, release |
| --- | --- |
| ![RViz jaw sweep](docs/media/rviz_jaw_sweep.gif) | ![Gazebo grasp](docs/media/gazebo_grasp.gif) |

## Packages

| Package | What it holds |
| --- | --- |
| `lead_screw_gripper_description` | The robot: Onshape export (`onshape/`), xacro wrappers (`urdf/`), Gazebo controller settings (`config/`), the grasp-test world (`worlds/`), RViz settings, and the phase 3 hand-written model |
| `lead_screw_gripper_kinematics` | Python: the linkage math (`linkage.py`, no ROS), the kinematics node (`jaw_node.py`), the scripted grasp test (`grasp_demo.py`), launch files and tests |

## Build

On Ubuntu 24.04 with ROS 2 Jazzy installed (desktop, `ros-dev-tools`, and `rosdep init` done):

```bash
cd ~/projects/Gripper-Claude_Onshape/ros2_ws
rosdep install --from-paths src --ignore-src -y
colcon build
source install/setup.bash
```

`rosdep` reads the `package.xml` files and installs anything missing: xacro, ros_gz, ros2_control, the controllers and so on. It asks for your password through `sudo`, so run it in a regular terminal (Ctrl+Alt+T), not the Claude app's terminal panel. Source `install/setup.bash` again in every new terminal.

## Run

**RViz with a jaw-gap slider:**

```bash
ros2 launch lead_screw_gripper_kinematics view_gripper.launch.py
```

A small "Jaw gap" window has a slider from 0 to 66 mm; moving it moves the whole linkage. Add `slider:=false` to leave the slider out, then command the gap from a terminal (in metres):

```bash
ros2 topic pub --once /jaw_gap_command std_msgs/msg/Float64 "{data: 0.045}"
```

**Gazebo grasp test** (the prefix runs Gazebo on the NVIDIA GPU):

```bash
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia ros2 launch lead_screw_gripper_kinematics sim_grasp.launch.py
```

After about 8 s the camera moves in. The test starts at 10 s and takes about 15 s. Options: `demo:=false` (just the gripper and the block, command it yourself), `rviz:=true`. Stop with Ctrl+C in the same terminal, and give it a few seconds to close.

To watch the block's height while it runs:

```bash
gz topic -e -t /world/grasp_test/dynamic_pose/info | grep -A8 test_box
```

**Tests** (no ROS needed, about 0.1 s):

```bash
cd src/lead_screw_gripper_kinematics
python3 -m pytest -q test
```

## How it works

### CAD to robot model

The Onshape document has a `Robot export` assembly, a copy of Assembly 1 marked up for [onshape-to-robot](https://github.com/Rhoban/onshape-to-robot):

- Each Group (frame, bell crank, front crank, carriage) becomes one link, because those parts move as one rigid body.
- Mates named `dof_…` become joints: the bell crank, front crank, finger and conrod revolutes on each side, plus the carriage slider.
- URDF can only describe a tree, but each side has two closed loops. They are cut at F2 (front crank to finger) and at C (conrod to carriage) by mates named `closing_…`. The export turns each cut into a pair of marker frames, which must sit on top of each other in any valid pose.

The export reads frozen version `robot-export-v1`. Settings are in `onshape/config.json`; re-run it with `onshape/export.sh`. The first export of a version uses about 150 Onshape API requests. Later runs read `~/.cache/onshape-to-robot` and use none. The export's zero pose (every joint at 0) is a **41.19 mm jaw gap**, because that is where the assembly sat when the version was saved.

### Kinematics node

The gripper has one degree of freedom. `linkage.py` turns a jaw gap into all nine joint values in closed form:

1. **Inverse kinematics:** gap = 2·L·(sin θ − sin θ_closed) with L = 28 mm, solved for the bell-crank angle θ.
2. **Loop closure:** the parallelogram O1–F1–F2–O2 turns the front crank by θ too, and turns the finger back by −θ, so the jaw translates without rotating. The offset slider-crank gives the carriage pin: C_x = D_x − √(22.68² − (24.91 − D_y)²).
3. **Joint conventions:** every revolute axis in the export points down (−z), so counterclockwise angles change sign. The lower side mirrors the upper side.

`test/test_linkage.py` checks this against the CAD: the four poses in `ROS2_HANDOFF.md` section 9 (θ, C_x and F1 within 0.01 mm and 0.01°). It also runs forward kinematics on the exported URDF at six jaw gaps, checking that all four loops close within 0.01 mm and that the fingers never rotate.

### Simulation

`urdf/lead_screw_gripper_gazebo.urdf.xacro` wraps the export with:

- a fixed rail and a `lift` slide, so a grasp can be tested against gravity;
- 2 mm box pads on the jaw faces (35 × 19.5 mm, measured from the finger mesh). The pads are the only collision shapes, which keeps contact fast and stable;
- ros2_control with `gz_ros2_control`, a position command on every joint.

Gazebo's physics engine does not close the linkage loops, so the node does. In sim mode only the upper bell crank is driven toward the target, and its torque cap sets the grip force. Every other joint is commanded from the **measured** upper crank angle, the way the parallelogram and the shared carriage tie them together in the real gripper. Driving all nine joints separately made a blocked finger twist, and let the block drift sideways and rotate out of the grip.

## Results

From the Gazebo test, run twice with the same numbers both times:

| Check | Result |
| --- | --- |
| Jaws close on the 30 mm block | Stop at 15.0 mm / 15.0 mm from the centreline |
| Fingers stay parallel under load | 0.00° tilt (about 1° for an instant at first contact) |
| Lift 50 mm | Block rises 50.0 mm (50.0 → 100.0 mm), no slip |
| Hold 3 s | Height steady, block tilt ≤ 0.1° |
| Set down and release | Block back at 50.0 mm, still standing |

### Limits, honestly

- **Simulated, not measured.** No hardware exists yet.
- **The grip force is an input, not a result.** The upper bell crank's torque cap (3 N·m) was chosen to give about 35 N per jaw, near the design's predicted ≥33 N. The simulation shows that a grip of that size holds a 50 g block. It does not check the 33 N prediction itself.
- **The loops are closed in software.** In Gazebo the follower joints are position-controlled from the measured crank angle; the physics engine does not enforce them.
- **Masses** come from Onshape mass properties with printed parts treated as solid: 1.09 kg in total. Real prints at 30–40% infill will be lighter.
- **The motor and lead screw are not modelled as actuators.** The jaw speed is limited to the predicted full stroke in 1.6 s.

## Troubleshooting

- **`sudo` fails in the Claude app's terminal** with "no new privileges": use a regular terminal (Ctrl+Alt+T).
- **ROS errors about Python 3.13 or missing modules:** conda's `base` environment is active. Run `conda deactivate`. Auto-activation is off on this laptop.
- **Gazebo is slow:** use the NVIDIA prefix shown above. `nvidia-smi` should list `gz sim gui` while it runs.
- **Windows stay open after Ctrl+C:** wait a few seconds, then close RViz with ✕ and choose "Close without Saving".
- **`robot_state_publisher` warns about root link inertia** (RViz view only): harmless. KDL ignores the base link's mass, and RViz still draws everything correctly.
