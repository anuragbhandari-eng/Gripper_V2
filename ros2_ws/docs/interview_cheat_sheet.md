# Interview cheat sheet: lead-screw gripper in ROS 2

Short answers in plain words, all about this gripper. Read it next to the code: `linkage.py` and `jaw_node.py` are short enough to explain line by line.

## The 30-second version

"I designed a lead-screw parallel gripper in Onshape, then brought it into ROS 2 Jazzy. I exported the assembly to a URDF robot description, wrote a closed-form kinematics node for its closed-loop linkage, checked against my CAD numbers to 0.01 mm, and simulated a grasp in Gazebo with ros2_control: it closes on a block, lifts it 50 mm, holds it and sets it down. It's simulation only. The hardware isn't built yet."

## ROS 2 basics

| Term | In one line | In this project |
| --- | --- | --- |
| Node | A running program that takes part in the ROS system | `jaw_kinematics`, `robot_state_publisher`, RViz |
| Topic | A named channel. Nodes publish to it or subscribe to it | `/joint_states`, `/jaw_gap_command` |
| Message | The data type a topic carries | `sensor_msgs/JointState`: joint names and positions |
| Parameter | A node setting you can change while it runs | `jaw_gap` (0–0.066 m), shown as a slider |
| Package | One unit of ROS code or data, with a `package.xml` ID card | `lead_screw_gripper_description`, `lead_screw_gripper_kinematics` |
| Workspace | The folder you build packages in: `src/` is yours, `build/` and `install/` are generated | `ros2_ws/` |
| Underlay / overlay | Base ROS (`/opt/ros/jazzy`) vs. your built packages layered on top when you source `install/setup.bash` | |
| Launch file | A Python script that starts several nodes at once, with settings | `view_gripper.launch.py`, `sim_grasp.launch.py` |
| `ros2 run` vs. `ros2 launch` | One program vs. a whole set | |

**ROS 2 is middleware, not an operating system:** libraries and tools on top of Linux that give robot programs a standard way to talk to each other.

## Robot description

- **URDF:** XML listing the **links** (rigid bodies) and **joints** (how a child link moves relative to its parent: type, origin, axis, limits).
- **A link is a rigid body, not a part:** my bell-crank link holds two plates and two screws, because they move together.
- **xacro:** macros and named values for URDF. My Gazebo file includes the exported URDF and adds pads, a lift joint and ros2_control without editing the export.
- **Frames and origins:** a joint origin places the child's frame on the parent. A visual origin shifts the mesh inside its own link. (Phase 3: the joint at O1 = (0, 0.05097, 0) m, the mesh shifted back by −O1.)
- **The joint zero is the CAD pose you exported from.** Mine is a 41.19 mm jaw gap, because that's where the assembly sat when I saved the version.
- **URDF must be a tree.** My linkage has closed loops (finger on two cranks, conrod between crank and carriage), so the loops are cut at F2 and C. Each cut becomes a pair of marker frames that must coincide.
- **robot_state_publisher** turns joint angles plus the URDF into 3D link positions (TF). **RViz** only draws them. **joint_state_publisher_gui** and my node only publish joint angles.
- **Mimic joints:** a joint that copies another times a factor. They work in RViz (pure math) but are fragile in Gazebo Harmonic, where only the Bullet Featherstone engine supports them. The official demo jammed on my machine. So I command every joint myself.

## CAD to robot (onshape-to-robot)

- Groups in the export assembly become links, `dof_` mates become joints, `closing_` mates cut loops, and `link_` mate connectors name links.
- I export from a **version**: frozen, reproducible, and cacheable. The first export used 150 API requests, re-exports none.
- A custom processor renames links to `<joint>_link`, because Gazebo's SDF needs link and joint names to be unique together.
- The same workflow carries over to SolidWorks (sw_urdf_exporter) or Fusion: links, joints, frames, units, mass properties.

## The kinematics (ME connections)

- **Closed-form inverse kinematics:** gap = 2·L·(sin θ − sin θ_closed) → θ = asin(gap / (2L) + sin θ_closed). One degree of freedom, so there's no iterative solver.
- **Vector loop equation (Kinematics of Machines):** the link vectors around a closed loop sum to zero, which gives 2 equations per loop for the unknown angles.
- **Parallelogram four-bar:** equal opposite links, so the coupler (finger) translates without rotating: curvilinear translation. Front crank = θ, finger = −θ relative to the bell crank.
- **Offset slider-crank:** the conrod is the hypotenuse of a right triangle, so C_x = D_x − √(l² − (y_C − D_y)²). The transmission angle stays between 59° and 90°, far from toggle.
- **Side effect:** the fingers also move 16.5 mm fore-aft over the stroke. A "two sliding fingers" model would miss that, and the exact model shows it.
- **Right-hand rule:** the exported joint axes point down (−z), so a positive joint value turns clockwise seen from above. The node flips signs.
- **Coordinate transforms:** p_local = Rᵀ(p_world − o), used to place the jaw pads in the finger frame.
- **Verified:** tests match my CAD pose table to 0.01 mm and 0.01°, and all four loops close within 0.01 mm across the stroke.

## Simulation and ros2_control

- **Physics engine:** the part of Gazebo that computes forces, joints and contacts. I use the default DART engine.
- **ros2_control** splits the **controller** (decides commands) from the **hardware interface** (talks to the device). In sim the hardware interface is `gz_ros2_control`. For the real gripper, I'd swap in an interface for the Pico and TMC2209 and keep the controllers.
- **Controllers:** `JointGroupPositionController` for the linkage and the lift, plus `joint_state_broadcaster` for `/joint_states`.
- **Position control in Gazebo is a first-order lag:** velocity = gain × error × rate, so the time constant is T = 1/(0.1 × 1000 Hz) = 10 ms.
- **Collision:** only 2 mm box pads on the jaw faces. Full meshes are slow and jittery for contact.

## Debugging stories (good interview material)

1. **The mimic joint demo jammed.** I checked the docs and issues and found that only Bullet Featherstone supports mimic constraints in Harmonic. I tested plain position control with the cart demo, then dropped mimic joints in Gazebo.
2. **Gazebo rejected the robot.** Links and joints shared names, which URDF allows but SDF doesn't. Fixed with a rename processor, with no new CAD version and no API requests.
3. **The lift joint wouldn't move.** It started exactly on its lower limit and stayed stuck. I moved the limit below the start position.
4. **The fingers twisted under load.** With nine independent joints, a blocked jaw's finger kept turning to its command. Fix: drive one crank and compute the followers from its measured angle, which is what the parallelogram does physically. (Kinematic constraint vs. actuation.)
5. **The block drifted sideways.** Two independent jaws pushing with equal capped force is a **neutral equilibrium**. The real gripper's shared carriage couples them. Fix: the lower crank mirrors the upper one.
6. **The grip was too weak.** With the finger held rigid, the crank torque acts through a ~78 mm lever, not the 28 mm crank arm (virtual work). I set the torque cap to give about 35 N per jaw.

## Honest framing

- "Simulated", "verified against CAD", "predicted". Never "tested" or "measured" for anything not done on hardware.
- The simulated grip force is a **chosen input** near the predicted ≥33 N, not a check of that prediction.
- Masses are from Onshape with solid prints (1.09 kg). Real prints will be lighter.

## Numbers to remember

Stroke 0–66 mm (commanded max 60 mm) · crank L = 28 mm · O1 = (0, 50.97) mm · crank angle −15.52° to 65.64° · carriage 32 mm (16 screw turns, Tr8×2) · 1600 steps/mm · full stroke 1.6 s predicted · grip ≥33 N per jaw predicted · test block 30 mm, 50 g, lifted 50.0 mm with no slip.
