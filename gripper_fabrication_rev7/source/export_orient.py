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
    ('01_Base', D.base(), 'flat', 1, 'bottom face on bed; 4 walls, 30% gyroid'),
    ('02_Cover', D.cover(), 'flip_x', 1, 'flat top face on bed'),
    ('03_Adapter_ISO9409-50-4-M6', D.adapter(), 'front_down', 1, 'gripper-side face on bed, spigot up'),
    ('04_Carriage', D.carriage(), 'rear_down', 1, 'rear face on bed, nut recess up; no supports; 100% infill around inserts and nut-screw pilots'),
    ('05_BellCrank_Lower_A', D.bc_plate(True), 'flat', 1, 'spacer boss up'),
    ('06_BellCrank_Lower_B_mirrored', mirror_ops(D.bc_plate(True)), 'flat', 1, 'mirror of 05 (other side)'),
    ('07_BellCrank_Upper', D.bc_plate(False), 'flat', 2, 'same part both sides (flip one)'),
    ('08_FrontCrank_Lower', D.fc_plate(True), 'flat', 2, 'spacer boss up'),
    ('09_FrontCrank_Upper', D.fc_plate(False), 'flat', 2, ''),
    ('10_ConRod', D.conrod(), 'flat', 2, ''),
    ('11_Finger_A', D.finger(), 'flat', 1, 'jaw block up'),
    ('12_Finger_B_mirrored', mirror_ops(D.finger()), 'flat', 1, 'mirror of 11'),
]
