#!/usr/bin/env bash
# Re-export the gripper from Onshape (GripperV2 version robot-export-v2, see config.json).
# Needs: ~/.venvs/gripper with onshape-to-robot, and API keys in ~/.config/onshape/keys.env.
# The first export of a version costs API requests (robot-export-v2: 244). Later runs read from
# ~/.cache/onshape-to-robot and cost none.
set -euo pipefail
cd "$(dirname "$0")"
set -a
source ~/.config/onshape/keys.env
set +a
PYTHONPATH="$PWD" ~/.venvs/gripper/bin/onshape-to-robot .

# The exporter keeps old merged meshes; delete any the new URDF no longer uses
for f in assets/merged/*.stl; do
    grep -q "$(basename "$f")" lead_screw_gripper.urdf || rm -v "$f"
done
