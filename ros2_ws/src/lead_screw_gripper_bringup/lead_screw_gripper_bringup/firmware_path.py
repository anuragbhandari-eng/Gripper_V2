"""Find the firmware folder that holds gripper_core.py and hal_sim.py, and make it importable."""
import os
import sys


def add_firmware_to_path():
    """Installed package: share/lead_screw_gripper_bringup/firmware. Source tree: gripper_fabrication_rev7/firmware."""
    candidates = []
    try:
        from ament_index_python.packages import get_package_share_directory
        candidates.append(os.path.join(get_package_share_directory('lead_screw_gripper_bringup'), 'firmware'))
    except Exception:  # not installed or not sourced: fall back to the source tree
        pass
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(here, '..', '..', '..', '..', 'gripper_fabrication_rev7', 'firmware'))
    for path in candidates:
        if os.path.isfile(os.path.join(path, 'gripper_core.py')):
            path = os.path.realpath(path)
            if path not in sys.path:
                sys.path.insert(0, path)
            return path
    raise ImportError('gripper_core.py not found in ' + ', '.join(candidates))
