"""Fit-test coupons (rev 6, plus rev 7 plates 13b/13c): print these first, in the real parts' material (design.MAT; ABS since rev 7) with the same printer and settings.
They copy the real fits: pivot bores, the crank/finger layer stack, the 608 cradle with the thrust collar, and the carriage tongue/channel."""
import cadquery as cq, numpy as np, json, os
import design as D
from prims import cq_part, hull_circles, circle_loop, poly_loop

def link(t, holes, boss_to=None):
    """Two-hole link (holes 20 mm apart, R5.5 bosses), thickness t; optional spacer boss on hole 1 up to boss_to."""
    ops = [('add', ('ext', hull_circles([((0, 0), D.R_BOSS), ((20, 0), D.R_BOSS)]), 0, t))]
    if boss_to: ops.append(('add', ('ext', circle_loop((20, 0), D.R_SPACER), t - 0.01, boss_to)))
    top = boss_to or t
    for (x, r) in holes: ops.append(('cut', ('cyl', (x, 0, -1), (x, 0, top + 1), r)))
    return ops

t_low, t_mid, t_up = D.Z_B1 - D.Z_B0, D.Z_M1 - D.Z_M0, D.Z_U1 - D.Z_U0
pieces = {
    # bore gauge: D3.9 dowel press | D4.0 insert & cover dowel | D4.1 snug | D4.2 running; notch marks the D3.9 end
    'bores': [('add', ('box', (-6, -6, 0), (36, 6, t_low))), ('cut', ('cyl', (-6, 0, -1), (-6, 0, t_low + 1), 2.0))] +
             [('cut', ('cyl', (x, 0, -1), (x, 0, t_low + 1), r)) for x, r in ((0, D.R_DOW_PRESS), (10, D.R_INS), (20, D.R_SNUG), (30, D.R_RUN))] +
             [('cut', ('cyl', (x, 4.0, -1), (x, 4.0, t_low + 1), r)) for x, r in ((5, 1.45), (15, 1.55))],   # rev 7.1: Ø3 locating pin press | slip
    # crank pivot stack: lower plate (insert at 0, spacer boss + running bore at 20), middle link, upper plate
    'stack_lower': link(t_low, [(0, D.R_INS), (20, D.R_RUN)], boss_to=D.Z_U0 - D.Z_B0),
    'stack_middle': link(t_mid, [(0, D.R_RUN), (20, D.R_RUN)]),
    'stack_upper': link(t_up, [(0, D.R_SNUG), (20, D.R_RUN)]),
}
# 608 cradle + collar: copy of the base's bearing-block half (printed flat, trough up)
L0, L1 = 0.0, D.X_BLK1 - D.X_BLK0
xb0, xb1 = D.X_BRG0 - D.X_BLK0, D.X_BRG1 - D.X_BLK0
pieces['cradle'] = [('add', ('box', (L0, -D.BLK_HW, 0), (L1, D.BLK_HW, D.Z_S))),
                    ('cut', ('cyl', (L0 - 1, 0, D.Z_S), (xb0 + 0.01, 0, D.Z_S), 8.0)),
                    ('cut', ('cyl', (xb0, 0, D.Z_S), (xb1, 0, D.Z_S), 11.03)),
                    ('cut', ('cyl', (xb1 - 0.01, 0, D.Z_S), (xb1 + 1.0, 0, D.Z_S), 6.3))]
# carriage tongue (11.6 wide) and base channel (12.0 wide, 6.5 deep)
pieces['channel'] = [('add', ('box', (0, -10, 0), (25, 10, 8.5))), ('cut', ('box', (-1, -6.0, 2.0), (26, 6.0, 9.0)))]
pieces['tongue'] = [('add', ('box', (0, -5.8, 0), (20, 5.8, 6.0)))]

layout = {'bores': (0, 0), 'stack_lower': (50, 0), 'stack_middle': (50, 18), 'stack_upper': (50, 36),
          'cradle': (0, 22), 'channel': (85, 0), 'tongue': (85, 28)}
solids, info = [], {}
for n, ops in pieces.items():
    s = cq_part(ops); assert s.isValid() and len(s.Solids()) == 1, n
    bb = s.BoundingBox(); x, y = layout[n]
    solids.append(s.translate((x - bb.xmin, y - bb.ymin, -bb.zmin)))
    info[n] = dict(volume_cm3=round(s.Volume()/1000, 2), bbox=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)])
plate = cq.Compound.makeCompound(solids)
# no overlaps between pieces on the plate
for i in range(len(solids)):
    for j in range(i + 1, len(solids)):
        assert solids[i].intersect(solids[j]).Volume() < 1e-6
cq.exporters.export(plate, '../stl/13_FitTest_coupons.stl', tolerance=0.02, angularTolerance=0.1)
bb = plate.BoundingBox()
# add/refresh the coupons entry in ../print_parts.json (export.py keeps it when it rewrites the file)
pp = '../print_parts.json'
PP = [e for e in (json.load(open(pp)) if os.path.exists(pp) else []) if e['file'] != '13_FitTest_coupons.stl']
PP.append(dict(file='13_FitTest_coupons.stl', qty=1, volume_cm3=round(plate.Volume()/1000, 2), material=D.MAT, mass_g_solid=round(plate.Volume()/1000*D.MAT_RHO, 1),
               bbox_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)], orientation='flat',
               note='print FIRST: fit-test coupons (pin bores, crank/finger layer stack, 608 cradle with collar recess, channel and tongue); not part of the gripper'))
json.dump(sorted(PP, key=lambda e: e['file']), open(pp, 'w'), indent=1)
print(json.dumps(dict(pieces=info, plate_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)],
                      total_cm3=round(sum(v['volume_cm3'] for v in info.values()), 1)), indent=1))

# ---------- rev 7.1 (design review item 11): coupons for the rev 7 fits, cut straight from the real parts ----------
def _cut(shape, x0, x1, y0=-200, y1=200, z0=-50, z1=60):
    return shape.intersect(cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0)))
rev7 = {   # name: (shape, note)
    'tongue_stub': _cut(cq_part(D.finger()), D.SEAM_X - 4, D.TONGUE_X1 + 1),               # tongue + its 2 insert holes
    'pocket_stub': _cut(cq_part(D.tip_block(False)), D.SEAM_X - 1, D.TONGUE_X1 + 4),        # pocket, floor screws, groove + snap step
    'enc_slot': _cut(cq_part(D.base()), D.X_BRG1 - 1.0, D.X_BLK1, -D.BLK_HW - 1, D.BLK_HW + 1, -3, D.Z_S),   # AS5600 slot half
    'm6_nut': cq_part([('add', ('box', (-10, -10, 0), (10, 10, 12))), ('cut', ('cyl', (0, 0, -1), (0, 0, 13), 3.3)),
                       ('cut', ('ext', D.hex_loop(0, 0, 10.2), -1, 8.0))]),                    # bracket nut pocket, open at the bottom as printed
    'col_socket': cq_part([('add', ('box', (-16, -16, 0), (16, 16, 10))),
                           ('cut', ('ext', D.rrect_loop(-10.2, -10.2, 10.2, 10.2, 0.5), -1, 11))]),   # 2020 column fit
    'puck': cq_part(D.enc_puck()).rotate((0, 0, 0), (0, 1, 0), -90),                        # magnet puck standing (pocket up): try it in a 608
}
sol7, info7 = [], {}
xcur = 0.0
for n, s7 in rev7.items():
    s7 = s7 if not hasattr(s7, 'Solids') or len(s7.Solids()) == 1 else s7.Solids()[0]
    assert s7.isValid() and len(s7.Solids()) == 1, n
    bb = s7.BoundingBox()
    sol7.append(s7.translate((xcur - bb.xmin, -bb.ymin, -bb.zmin))); xcur += bb.xlen + 5.0
    info7[n] = dict(volume_cm3=round(s7.Volume()/1000, 2), bbox=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)])
plate7 = cq.Compound.makeCompound(sol7)
cq.exporters.export(plate7, '../stl/13b_FitTest_rev7.stl', tolerance=0.02, angularTolerance=0.1)
pad7 = _cut(cq_part(D.pad(False)), D.PAD_X[0] - 1, D.TONGUE_X1 + 4)
pad7 = pad7.rotate((0, 0, 0), (1, 0, 0), 90); b7 = pad7.BoundingBox(); pad7 = pad7.translate((-b7.xmin, -b7.ymin, -b7.zmin))   # contact face on the bed
cq.exporters.export(pad7, '../stl/13c_FitTest_pad_TPU95A.stl', tolerance=0.02, angularTolerance=0.1)
PP = [e for e in json.load(open(pp)) if e['file'] not in ('13b_FitTest_rev7.stl', '13c_FitTest_pad_TPU95A.stl')]
bb7, bp7 = plate7.BoundingBox(), pad7.BoundingBox()
PP.append(dict(file='13b_FitTest_rev7.stl', qty=1, volume_cm3=round(plate7.Volume()/1000, 2), material=D.MAT, mass_g_solid=round(plate7.Volume()/1000*D.MAT_RHO, 1),
               bbox_mm=[round(bb7.xlen, 1), round(bb7.ylen, 1), round(bb7.zlen, 1)], orientation='flat',
               note='print FIRST (rev 7 fits): tongue stub + tip-block pocket stub (install the 2 inserts, then test the slide fit and the M3x10 screws), AS5600 slot (1.6 mm board), M6 nut pocket, 2020 column socket, magnet puck (try it in a 608); not part of the gripper'))
PP.append(dict(file='13c_FitTest_pad_TPU95A.stl', qty=1, volume_cm3=round(pad7.Volume()/1000, 2), material=D.PAD_MAT, mass_g_solid=round(pad7.Volume()/1000*D.PAD_RHO, 1),
               bbox_mm=[round(bp7.xlen, 1), round(bp7.ylen, 1), round(bp7.zlen, 1)], orientation='face_down',
               note='print FIRST in TPU 95A: pad stub with the snap barb, for the pocket stub groove (it should snap in and not pull out by hand)'))
json.dump(sorted(PP, key=lambda e: e['file']), open(pp, 'w'), indent=1)
print(json.dumps(dict(rev7_pieces=info7, rev7_plate_mm=[round(bb7.xlen, 1), round(bb7.ylen, 1), round(bb7.zlen, 1)]), indent=1))
