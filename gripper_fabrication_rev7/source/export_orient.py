import cadquery as cq, design as D
from prims import cq_part, mirror_ops
def orient(shape, how):
    s = shape
    if how == 'flip_x': s = s.rotate((0, 0, 0), (1, 0, 0), 180)
    if how == 'front_down': s = s.rotate((0, 0, 0), (0, 1, 0), 90)
    if how == 'side_py_down': s = s.rotate((0, 0, 0), (1, 0, 0), -90)
    if how == 'rear_down': s = s.rotate((0, 0, 0), (0, 1, 0), -90)
    bb = s.BoundingBox()
    return s.translate((-(bb.xmin+bb.xmax)/2, -(bb.ymin+bb.ymax)/2, -bb.zmin))
PRINT = [  # file, ops, orientation, qty, note
    ('Base x1', D.base(), 'flat', 1, 'bottom face on bed; 4 walls, 30% gyroid'),
    ('Cover x1', D.cover(), 'flip_x', 1, 'flat top face on bed'),
    ('Adapter ISO9409-50 x1', D.adapter(), 'front_down', 1, 'gripper-side face on bed, spigot up'),
    ('Carriage x1', D.carriage(), 'rear_down', 1, 'rear face on bed, nut recess up; no supports; 100% infill around inserts and nut-screw pilots'),
    ('BellCrank Lower U x1', D.bc_plate(True), 'flat', 1, 'spacer boss up'),
    ('BellCrank Lower L x1', mirror_ops(D.bc_plate(True)), 'flat', 1, 'mirror of BellCrank Lower U (other side)'),
    ('BellCrank Upper U+L x2', D.bc_plate(False), 'flat', 2, 'same part both sides (flip one)'),
    ('FrontCrank Lower U+L x2', D.fc_plate(True), 'flat', 2, 'spacer boss up'),
    ('FrontCrank Upper U+L x2', D.fc_plate(False), 'flat', 2, ''),
    ('ConRod U+L x2', D.conrod(), 'flat', 2, ''),
    ('Finger U x1', D.finger(), 'flat', 1, 'jaw block up'),
    ('Finger L x1', mirror_ops(D.finger()), 'flat', 1, 'mirror of Finger U'),
]
