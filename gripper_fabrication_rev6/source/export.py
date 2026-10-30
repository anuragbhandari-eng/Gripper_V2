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
info = []
for fn, ops, how, qty, note in PRINT:
    s = orient(cq_part(ops), how); bb = s.BoundingBox()
    cq.exporters.export(s, f'{OUT}/stl/{fn}.stl', tolerance=0.02, angularTolerance=0.1)
    info.append(dict(file=fn + '.stl', qty=qty, volume_cm3=round(s.Volume()/1000, 2), mass_g_solid_PETG=round(s.Volume()/1000*1.27, 1),
                     bbox_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)], orientation=how, note=note))
pp = f'{OUT}/print_parts.json'   # keep entries written by other scripts (Fit test coupons x1 from fit_coupons.py)
keep = [e for e in (json.load(open(pp)) if os.path.exists(pp) else []) if e['file'] not in {i['file'] for i in info}]
json.dump(info + keep, open(pp, 'w'), indent=1)   # export order, then the fit-test plate
# assembly STEP at gap 30 (each part a named component) + closed/open
for gap in (0, 30, 66):
    th = np.arcsin(gap/(2*D.L) + np.sin(D.TH_C))
    asm = cq.Assembly(name=f'LeadScrewGripper_gap{gap}')
    for n, (ops, M) in D.pose(th).items():
        sh = cq.Shape.cast(C.place(C.solid(ops), M))
        asm.add(sh, name=n, color=cq.Color(*[int(R.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)] ) if (R := __import__('render').color(n)) else None)
    asm.save(f'{OUT}/step/LeadScrewGripper_assembly_gap{gap}mm.step')
print(json.dumps(info, indent=0)[:1500])
