import numpy as np, os, json, cadquery as cq
import design as D, check as C
from prims import cq_part, mirror_ops
OUT = '..'
os.makedirs(OUT + '/stl', exist_ok=True); os.makedirs(OUT + '/step', exist_ok=True)
def orient(shape, how):
    s = shape
    if how == 'flip_x': s = s.rotate((0, 0, 0), (1, 0, 0), 180)
    if how == 'front_down': s = s.rotate((0, 0, 0), (0, 1, 0), 90)
    if how == 'side_py_down': s = s.rotate((0, 0, 0), (1, 0, 0), -90)
    if how == 'side_my_down': s = s.rotate((0, 0, 0), (1, 0, 0), 90)
    if how == 'rear_down': s = s.rotate((0, 0, 0), (0, 1, 0), -90)
    bb = s.BoundingBox()
    return s.translate((-(bb.xmin+bb.xmax)/2, -(bb.ymin+bb.ymax)/2, -bb.zmin))
PRINT = [  # file, ops, orientation, qty, note
    ('01 Base', D.base(), 'flat', 1, 'bottom face on bed; 4 walls, 30% gyroid'),
    ('02 Cover', D.cover(), 'flip_x', 1, 'flat top face on bed'),
    ('03 Adapter ISO9409-50', D.adapter(), 'front_down', 1, 'gripper-side face on bed, spigot up'),
    ('04 Carriage', D.carriage(), 'rear_down', 1, 'rear face on bed, nut recess up; no supports; 100% infill around inserts and nut-screw pilots'),
    ('05 BellCrank Lower U', D.bc_plate(True), 'flat', 1, 'spacer boss up'),
    ('06 BellCrank Lower L', mirror_ops(D.bc_plate(True)), 'flat', 1, 'mirror of 05 (other side)'),
    ('07 BellCrank Upper U+L', D.bc_plate(False), 'flat', 2, 'same part both sides (flip one)'),
    ('08 FrontCrank Lower U+L', D.fc_plate(True), 'flat', 2, 'spacer boss up'),
    ('09 FrontCrank Upper U+L', D.fc_plate(False), 'flat', 2, ''),
    ('10 ConRod U+L', D.conrod(), 'flat', 2, ''),
    ('11 Finger U', D.finger(), 'flat', 1, 'tongue forward; M layer only since rev 7'),
    ('12 Finger L', mirror_ops(D.finger()), 'flat', 1, 'mirror of 11'),
    # rev 7: bolt-on tip sets (13 is the fit-coupon plate from fit_coupons.py)
    ('14 Tip block U narrow', D.tip_block(False), 'flat', 1, 'narrow set; floor down, tongue pocket opens upward'),
    ('15 Tip block L narrow', mirror_ops(D.tip_block(False)), 'flat', 1, 'mirror of 14'),
    ('16 Tip block U wide', D.tip_block(True), 'flat', 1, 'wide set; floor down, tongue pocket opens upward'),
    ('17 Tip block L wide', mirror_ops(D.tip_block(True)), 'flat', 1, 'mirror of 16'),
    ('18 Pad TPU U+L', mirror_ops(D.pad(False)), 'side_py_down', 4, 'TPU 95A, contact face on bed; 2 per tip set (same pad fits both)'),
    ('19 Encoder magnet puck', D.enc_puck(), 'rear_down', 1, 'magnet pocket up; glue to the screw end'),
    ('20 Stand head bracket', D.stand_bracket(), 'rear_down', 1, 'bench stand; back face on bed, nut pockets and column hole open upward'),
    ('21 Stand base', D.stand_base(), 'front_down', 1, 'bench stand; table face on bed, column socket up'),
    ('22 Stand desk clamp U', D.desk_clamp(), 'side_my_down', 1, 'desk clamp; lying on its side, nut slot up, 100% infill at the corners'),
    ('23 Stand desk clamp L', mirror_ops(D.desk_clamp()), 'side_py_down', 1, 'mirror of 22'),
    ('24 Stand clamp pad U+L', D.clamp_pad(), 'rear_down', 2, 'desk side down; felt on it is optional'),
    ('26 Electronics cover', D.elec_cover(), 'flip_x', 1, 'top face on bed, no supports; 2 M3 x 8 into the cover-top inserts'),
    ('25 Controller spacer rear+front U+L', D.ctrl_spacer(), 'flat', 4, 'end on bed, 100% infill; 4 mm tall, replaces the brass standoffs (M3 x 10 through board and spacer into the cover insert)'),
]
info = []
for fn, ops, how, qty, note in PRINT:
    s = orient(cq_part(ops), how); bb = s.BoundingBox()
    cq.exporters.export(s, f'{OUT}/stl/{fn}.stl', tolerance=0.02, angularTolerance=0.1)
    info.append(dict(file=fn + '.stl', qty=qty, volume_cm3=round(s.Volume()/1000, 2), material=(mat := D.PAD_MAT if 'pad' in fn.lower() else D.MAT), mass_g_solid=round(s.Volume()/1000*(D.PAD_RHO if mat == D.PAD_MAT else D.MAT_RHO), 1),
                     bbox_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)], orientation=how, note=note))
pp = f'{OUT}/print_parts.json'   # keep entries written by other scripts (13 Fit test coupons from fit_coupons.py)
keep = [e for e in (json.load(open(pp)) if os.path.exists(pp) else []) if e['file'] not in {i['file'] for i in info}]
json.dump(sorted(info + keep, key=lambda e: e['file']), open(pp, 'w'), indent=1)
# assembly STEP at gap 30 (each part a named component) + closed/open
for gap in (0, 30, D.GAP_MAX):
    th = np.arcsin(gap/(2*D.L) + np.sin(D.TH_C))
    asm = cq.Assembly(name=f'LeadScrewGripper_gap{gap}')
    for n, (ops, M) in D.pose(th).items():
        sh = cq.Shape.cast(C.place(C.solid(ops), M))
        asm.add(sh, name=n, color=cq.Color(*[int(R.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)] ) if (R := __import__('render').color(n)) else None)
    asm.save(f'{OUT}/step/LeadScrewGripper_assembly_gap{gap}mm.step')
print(json.dumps(info, indent=0)[:1500])
