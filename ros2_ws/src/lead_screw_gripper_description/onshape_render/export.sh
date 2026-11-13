#!/usr/bin/env bash
# Same export as ../onshape/export.sh with each part kept as its own mesh in its own colour
# (merging averages a link into one colour) and on its own fixed link (RViz shows only one colour
# per link), for recordings that look like the CAD. Reads the same version from the cache, so it
# costs no API requests once ../onshape/export.sh has run.
set -euo pipefail
cd "$(dirname "$0")"
set -a
source ~/.config/onshape/keys.env
set +a
PYTHONPATH="$PWD/../onshape" ~/.venvs/gripper/bin/onshape-to-robot .

# The exporter keeps old merged meshes; delete any the new URDF no longer uses
for f in assets/*.stl; do
    grep -q "$(basename "$f")" lead_screw_gripper_render.urdf || rm -v "$f"
done
