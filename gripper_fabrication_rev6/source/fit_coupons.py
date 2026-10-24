"""Fit-test coupons (rev 6): print these first, in PETG with the same settings as the real parts.
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
             [('cut', ('cyl', (x, 0, -1), (x, 0, t_low + 1), r)) for x, r in ((0, D.R_DOW_PRESS), (10, D.R_INS), (20, D.R_SNUG), (30, D.R_RUN))],
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
PP.append(dict(file='13_FitTest_coupons.stl', qty=1, volume_cm3=round(plate.Volume()/1000, 2), mass_g_solid_PETG=round(plate.Volume()/1000*1.27, 1),
               bbox_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)], orientation='flat',
               note='print FIRST: fit-test coupons (pin bores, crank/finger layer stack, 608 cradle with collar recess, channel and tongue); not part of the gripper'))
json.dump(sorted(PP, key=lambda e: e['file']), open(pp, 'w'), indent=1)
print(json.dumps(dict(pieces=info, plate_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)],
                      total_cm3=round(sum(v['volume_cm3'] for v in info.values()), 1)), indent=1))
