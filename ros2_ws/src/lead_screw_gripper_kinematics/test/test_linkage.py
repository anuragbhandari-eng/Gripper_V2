"""Checks the linkage math against the CAD numbers (ROS2_HANDOFF.md section 9)
and against the robot exported from Onshape."""
import math
import os
import xml.etree.ElementTree as ET

import numpy as np
import pytest
import yaml

from lead_screw_gripper_kinematics.linkage import (
    CRANK, GAP_MAX, JOINT_NAMES, O1, crank_angle_from_gap, crank_angle_from_joint, gap_from_crank_angle,
    joint_positions, linkage_points)

DESCRIPTION = os.path.join(os.path.dirname(__file__), '..', '..', 'lead_screw_gripper_description')
URDF = os.path.join(DESCRIPTION, 'onshape', 'lead_screw_gripper.urdf')
CONTROLLERS = os.path.join(DESCRIPTION, 'config', 'gripper_controllers.yaml')

# Jaw gap (mm), crank angle (deg), carriage pin Cx (mm), F1 (mm): handoff section 9
POSES = [
    (0, -15.52, -27.49, (26.98, 43.48)),
    (30, 15.55, -16.28, (26.98, 58.48)),
    (60, 53.50, -1.32, (16.66, 73.48)),
    (66, 65.64, 4.55, (11.55, 76.48)),
]


@pytest.mark.parametrize('gap, theta_deg, cx, f1', POSES)
def test_matches_cad_pose_table(gap, theta_deg, cx, f1):
    theta = crank_angle_from_gap(gap / 1000.0)
    _, c, _ = linkage_points(theta)
    f1_now = (O1[0] + CRANK * math.cos(theta), O1[1] + CRANK * math.sin(theta))
    assert math.degrees(theta) == pytest.approx(theta_deg, abs=0.01)
    assert c[0] == pytest.approx(cx, abs=0.01)
    assert f1_now == pytest.approx(f1, abs=0.01)


@pytest.mark.parametrize('gap', [0.0, 0.0123, 0.030, 0.066])
def test_forward_and_inverse_agree(gap):
    assert gap_from_crank_angle(crank_angle_from_gap(gap)) == pytest.approx(gap, abs=1e-12)


@pytest.mark.parametrize('gap', [0.0, 0.025, 0.066])
def test_crank_angle_recovered_from_measured_joints(gap):
    joints = joint_positions(gap)
    theta = crank_angle_from_gap(gap)
    assert crank_angle_from_joint('U', joints['bell_crank_U']) == pytest.approx(theta, abs=1e-12)
    assert crank_angle_from_joint('L', joints['bell_crank_L']) == pytest.approx(theta, abs=1e-12)


def test_joint_order_matches_gazebo_controller():
    with open(CONTROLLERS) as f:
        config = yaml.safe_load(f)
    assert tuple(config['gripper_controller']['ros__parameters']['joints']) == JOINT_NAMES
    assert tuple(joint_positions(0.03).keys()) == JOINT_NAMES


def _rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p), math.sin(p),
                              math.cos(y), math.sin(y))
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def _axis_angle(a, t):
    a = np.asarray(a) / np.linalg.norm(a)
    k = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * k + (1 - math.cos(t)) * k @ k


def _forward_kinematics(q):
    """World pose (4x4) of every link in the exported URDF for joint values q."""
    joints = ET.parse(URDF).getroot().findall('joint')
    poses = {'base_link': np.eye(4)}
    while len(poses) < len(joints) + 1:
        for j in joints:
            parent, child = j.find('parent').get('link'), j.find('child').get('link')
            if parent in poses and child not in poses:
                o = j.find('origin')
                fixed = np.eye(4)
                fixed[:3, :3] = _rpy(*map(float, o.get('rpy').split()))
                fixed[:3, 3] = list(map(float, o.get('xyz').split()))
                move = np.eye(4)
                axis = j.find('axis')
                a = list(map(float, axis.get('xyz').split())) if axis is not None else [0, 0, 1]
                if j.get('type') == 'revolute':
                    move[:3, :3] = _axis_angle(a, q.get(j.get('name'), 0.0))
                elif j.get('type') == 'prismatic':
                    move[:3, 3] = np.asarray(a) * q.get(j.get('name'), 0.0)
                poses[child] = poses[parent] @ fixed @ move
    return poses


@pytest.mark.parametrize('gap', [0.0, 0.010, 0.030, 0.045, 0.060, 0.0605])
def test_loops_close_and_jaws_stay_parallel(gap):
    poses = _forward_kinematics(joint_positions(gap))
    # Both halves of every cut loop (F2 and C, both sides) must meet
    for cut in ('closing_F2_U', 'closing_C_U', 'closing_F2_L', 'closing_C_L'):
        miss = np.linalg.norm(poses[cut + '_1'][:3, 3] - poses[cut + '_2'][:3, 3])
        assert miss * 1000 < 0.01, f'{cut} misses by {miss * 1000:.4f} mm'
    # The fingers translate without turning, and each moves gap/2 from closed
    rest = _forward_kinematics({})
    for finger, sign in (('finger_U_link', 1), ('finger_L_link', -1)):
        assert np.allclose(poses[finger][:3, :3], rest[finger][:3, :3], atol=1e-9)
        assert sign * poses[finger][1, 3] * 1000 == pytest.approx(43.48 + gap * 500, abs=0.01)


@pytest.mark.parametrize('gap', np.linspace(0.0, GAP_MAX, 25))
def test_joint_values_stay_inside_urdf_limits(gap):
    limits = {j.get('name'): (float(j.find('limit').get('lower')), float(j.find('limit').get('upper')))
              for j in ET.parse(URDF).getroot().findall('joint') if j.find('limit') is not None}
    for name, value in joint_positions(gap).items():
        lower, upper = limits[name]
        assert lower <= value <= upper, f'{name} = {value:.6f} is outside [{lower}, {upper}] at {gap * 1000:.2f} mm'
