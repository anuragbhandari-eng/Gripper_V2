# Resume bullet: draft for you to rewrite

Pick one, then rewrite it in your own words. Each one only claims what the repo can back up. Everything is "simulated"; nothing says "tested" or "measured".

**One line (fits under the gripper entry):**

- Brought my lead-screw gripper into ROS 2 Jazzy: exported the Onshape assembly to URDF, built a closed-form kinematics node for its closed-loop linkage (matches CAD within 0.01 mm), and simulated a grasp-and-lift in Gazebo with ros2_control.

**Shorter:**

- Modeled my gripper in ROS 2 (URDF from Onshape, linkage kinematics node, Gazebo + ros2_control grasp simulation).

**If you want two bullets:**

- Exported a 49-part Onshape assembly to a ROS 2 robot description, cutting the linkage's closed loops into a URDF tree.
- Wrote a closed-form kinematics node (one jaw gap → nine joint positions) and verified it against CAD within 0.01 mm. Simulated a 50 mm grasp-and-lift in Gazebo Harmonic.

## Before you use one

- **Only claim what you can explain.** Much of the code was written for you after you switched plans in phase 6, so an interviewer may ask about any line. Go through `docs/interview_cheat_sheet.md` and the two short Python files first. If a verb like "wrote" doesn't feel true yet, "built" or "developed" fits work you directed and understand.
- Keep "simulated". The grip force in Gazebo is a chosen setting, not a result.
- The portfolio rules (no mention of AI, scripts or automation on the site) don't apply here. How you describe your process on the resume is your call; just keep it truthful.
