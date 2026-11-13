"""Linkage math for the lead-screw parallel gripper (rev 6 linkage, unchanged in rev 7), with no ROS code in it.

Ported from gripper_fabrication_rev6/source/params.py and kin.py (rev 7 uses the same numbers).
CAD frame: x along the lead screw toward the jaws, y toward the upper (U) finger, z up,
x = 0 at the fixed pivot O1. Lengths in mm, angles in radians, counterclockwise positive
seen from above. The lower (L) side is the upper side mirrored in y.
"""
import math

# Geometry in mm (params.py with crank length L = 28 mm)
CRANK = 28.0                        # O1-F1 and O2-F2
O1 = (0.0, 1.820360 * CRANK)        # fixed pivot of the bell crank: (0, 50.97)
ARM_D = 0.746771 * CRANK            # O1-D, 90 deg behind O1-F1: 20.91
ROD = 0.809826 * CRANK              # connecting rod D-C: 22.68
PIN_LINE_Y = 0.889803 * CRANK       # carriage pin C slides along y = 24.91
THETA_CLOSED = math.radians(-15.52)  # crank angle with the jaws touching

GAP_MIN = 0.0    # m, jaws closed
GAP_MAX = 0.0605  # m, rev 7 open hard stop (rev 6 was 66 mm)

# The Onshape export (GripperV2 version robot-export-v2) was saved at the open hard stop.
# Every URDF joint reads 0 in that pose, so joint values are measured from it.
THETA_EXPORT = math.asin(GAP_MAX * 1000.0 / (2 * CRANK) + math.sin(THETA_CLOSED))  # 54.37 deg

# URDF joint names, in the order the Gazebo position controller expects them
JOINT_NAMES = ('bell_crank_U', 'front_crank_U', 'finger_U', 'conrod_U',
               'bell_crank_L', 'front_crank_L', 'finger_L', 'conrod_L', 'carriage')


def gap_from_crank_angle(theta):
    """Return the jaw gap (m) for a bell-crank angle theta (rad): the forward direction."""
    return 2 * CRANK * (math.sin(theta) - math.sin(THETA_CLOSED)) / 1000.0


def crank_angle_from_gap(gap_m):
    """Return the bell-crank angle theta (rad) for a jaw gap in metres.

    The jaw gap grows with the crank angle as
        gap = 2 * CRANK * (sin(theta) - sin(THETA_CLOSED))     (gap and CRANK in mm)
    Solving for theta: sin(theta) = gap / (2 * CRANK) + sin(THETA_CLOSED).
    """
    gap_mm = gap_m * 1000.0
    return math.asin(gap_mm / (2 * CRANK) + math.sin(THETA_CLOSED))


def linkage_points(theta):
    """Return (D, C, psi) for crank angle theta.

    D: moving pivot on the bell crank (mm), 90 deg behind the O1-F1 arm.
    C: carriage pin (mm), on the line y = PIN_LINE_Y, behind D.
    psi: angle of the connecting rod from D toward C (rad).
    """
    phi = theta - math.pi / 2
    d = (O1[0] + ARM_D * math.cos(phi), O1[1] + ARM_D * math.sin(phi))
    dy = PIN_LINE_Y - d[1]
    c = (d[0] - math.sqrt(ROD ** 2 - dy ** 2), PIN_LINE_Y)
    psi = math.atan2(c[1] - d[1], c[0] - d[0])
    return d, c, psi


_, _C_EXPORT, _PSI_EXPORT = linkage_points(THETA_EXPORT)


def joint_positions(gap_m):
    """Return {URDF joint name: value} for a jaw gap in metres."""
    return joint_positions_from_crank(crank_angle_from_gap(gap_m))


def crank_angle_from_joint(side, value):
    """Return the bell-crank angle theta (rad) from a measured bell-crank joint value."""
    return THETA_EXPORT - value if side == 'U' else THETA_EXPORT + value


def joint_positions_from_crank(theta):
    """Return {URDF joint name: value} for bell-crank angle theta (rad).

    Revolute values are in rad, the carriage in m, all measured from the export pose.
    Every revolute axis in the export points down (-z), so a positive joint value turns
    the part clockwise seen from above. That is why the counterclockwise angles below
    change sign. The carriage axis points toward the motor (-x).
    """
    _, c, psi = linkage_points(theta)
    d_theta = theta - THETA_EXPORT           # bell crank turn (CCW)
    d_rod = (psi - _PSI_EXPORT) - d_theta    # rod turn relative to the bell crank
    d_carriage = (c[0] - _C_EXPORT[0]) / 1000.0

    return {  # same order as JOINT_NAMES
        # Upper side: the parallelogram turns the front crank with the bell crank, and
        # the finger turns back by the same angle so the jaw only translates.
        'bell_crank_U': -d_theta,
        'front_crank_U': -d_theta,
        'finger_U': d_theta,
        'conrod_U': -d_rod,
        # Lower side: the mirror image, so every turn has the opposite sign.
        'bell_crank_L': d_theta,
        'front_crank_L': d_theta,
        'finger_L': -d_theta,
        'conrod_L': d_rod,
        'carriage': -d_carriage,
    }
