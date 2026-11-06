# Handoff: RViz clip of the rev 7 gripper for the portfolio

**Status 2026-11-05: published. Pushed to portfolio main (e0aea31) on Anurag's request; live at https://anuragbhandari.vercel.app/projects/lead-screw-gripper/ . The "0.01 mm loop closure" sentence was removed at his request. ros2_ws is still uncommitted.**
Branch `gripper-ros2-rviz` (commit 19815ce) was rebuilt from origin/main with the unedited RViz
screen recording (1280x764, 4.8 s, one open-close-open cycle trimmed for the loop, real time).
Then (commit 15a45ca) cropped to the RViz 3D view only (1116x806 at x 667, y 211 of the raw
1800x1074 capture), on Anurag's request; caption updated.
Preview: https://portfolio-j88xylagt-anurag-bhandari-s-projects.vercel.app/projects/lead-screw-gripper/
(needs his Vercel login). Merge to main only on his OK. ros2_ws is still uncommitted.
Recording recipe that worked: Claude app moved to the right half; RViz client resized to 1800x1000;
slider kept on top with `tools/xctl.py above <tk id>` (raise is blocked while RViz has focus);
capture rectangle = visible RViz window only (1800x1074 at the window's title-bar top-left);
slider knob x = 142.5 + 6.05 * gap_mm at its screen y; dragged with xctl.drag.

---
History (written when paused):

## Goal
Put an RViz screen recording of the current (rev 7, GripperV2) gripper on the portfolio page
`src/content/projects/lead-screw-gripper.mdx`, as an unedited RViz capture.

## Anurag's choices (keep them)
- Robot model comes from Onshape via onshape-to-robot, never from design.py/CadQuery.
- The clip must be RViz itself, not edited: full RViz window with the Displays panel and grid,
  TF axes on, the "Jaw gap (mm)" slider window visible and actually driving the jaws, covers on.
  No crop, restyle or slow-motion tricks.
- Preview branch first; never commit to portfolio `main` (it deploys live) without his OK.

## Done
- Onshape GripperV2: new "Robot export" tab (duplicate of Assembly 1, stand/power bank removed,
  13 joint mates renamed dof_/closing_, 5 link_ connectors on part origins). Old tab renamed
  "Robot export (rev 6)". Version `robot-export-v2` (id 5cdac080a8e3ed3cdc956c12). Export cost
  244 API requests; it is cached in ~/.cache/onshape-to-robot, so re-exports cost 0 (check the
  cache count stays 394 before/after).
- Export zero pose = rev 7 open stop (60.5 mm). linkage.py THETA_EXPORT, GAP_MAX 0.0605,
  joint limits in onshape*/config.json updated. 43/43 tests pass (`python3 -m pytest -q test`
  in src/lead_screw_gripper_kinematics).
- `onshape/` = main URDF (links merged, one averaged colour per link).
  `onshape_render/` = same version, every part its own fixed link and colour, covers ON.
  `urdf/lead_screw_gripper_render.urdf.xacro` includes it.
- `rviz/record.rviz` = display.rviz + TF on (scale 0.15, only the 10 real links), opaque model,
  3/4 view, 1800x1000 window. `rviz/render.rviz` = old styled view (no longer wanted).
- `view_gripper.launch.py` now takes `model:=` and `rviz:=`.
- `tools/xctl.py` moves windows and drags the mouse via XTEST (ctypes, no installs).
  `tools/sweep.py` publishes jaw_gap_command cycles (not wanted now: use the slider instead).
- Independent audit done: no blockers; carriage limit fixed to 0.0266.
- Nothing in this ros2_ws is committed (untracked in the V2 repo).

## Portfolio state
- Local `main` was 44 commits behind origin/main. Branch `gripper-ros2-rviz` (pushed,
  commit 318813a) is based on the OLD main and has the old styled clip. It must be redone:
  `git fetch && git checkout -B gripper-ros2-rviz origin/main`, then re-add the section.
- Live page (origin/main) has no "How I checked it" section; put "## How it runs in ROS 2"
  after "What the numbers say" (before "What's in the build"). Live media is white background,
  mechanism clip 1280x528. Add "ROS 2" to skills. Site text must never mention Claude, AI,
  scripts, pipelines, APIs or MCP.
- Section text used before: "I exported the assembly from Onshape to a URDF and wrote a ROS 2
  node that takes one jaw-gap command and sets all nine joints from the same linkage equations
  as the analysis. In the model, the linkage loops close to within 0.01 mm over the whole stroke."
- Build locally: `export PATH=~/miniforge3/envs/portfolio-node/bin:$PATH; npm run build`.
  Push the branch with --force-with-lease (it is our own preview branch). The Vercel preview
  needs his Vercel login, so he checks it.

## Next steps
1. Kill stale ROS processes first (`pgrep -fa "robot_state_publisher|jaw_|rviz2"`; earlier
   sessions left duplicates publishing old models).
2. `ros2 launch lead_screw_gripper_kinematics view_gripper.launch.py rviz:=record.rviz
   model:=lead_screw_gripper_render.urdf.xacro` (slider on by default).
3. Bring RViz to the front (the Claude app covered it last time; ask Anurag to keep it clear).
   RViz frame was 1856x1132 at (32,56). Move the slider client window into RViz's empty lower
   Displays area: `python3 tools/xctl.py move <tk window id> 112 640` (frame lands at 84,616).
   Capture only the RViz frame rectangle so nothing else on screen is recorded:
   `ffmpeg -f x11grab -framerate 30 -video_size 1856x1132 -i :1+32,56 ...`.
4. Drag the real slider knob with xctl.drag (find the knob from a capture) open -> closed -> open;
   tell Anurag beforehand that the mouse will move for ~15 s.
5. Encode (scale to 1280 wide, H.264, faststart, no audio), poster from frame 0, review frames,
   then redo the portfolio branch as above, build, push, ask him to check the preview.
