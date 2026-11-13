"""Rev 7 step pictures for the illustrated build guide (scratch; reuses guide_render helpers)."""
import sys, os, numpy as np
SRC = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, SRC); os.chdir(SRC)
import guide_render as G, design as D, render as R
th = G.TH(30)
_cache = {}
def parts():
    if 'p' not in _cache:
        _cache['p'] = {n: G.mesh_of(ops, M) for n, (ops, M) in D.pose(th).items()}
    return _cache['p']
def build(show, new=(), offsets=None, washed=True):
    offsets = offsets or {}; out = []
    for n, m in parts().items():
        if not any(n.startswith(s) for s in show): continue
        for k, off in offsets.items():
            if n.startswith(k): m = m.translate(off, inplace=False); break
        isnew = any(n.startswith(s) for s in new); col = R.color(n)
        out.append((m, (G.HL if washed else col) if isnew else (G.light(col, 0.6) if washed else col), 1.0))
    return out
def sc(name, items, **kw):
    try:
        G.scene(name, items, out=OUT, size=(1200, 800), **kw); print('ok', name, flush=True)
    except Exception as e: print('FAIL', name, repr(e), flush=True)
print(sorted(parts().keys()), flush=True)
cam = dict(cam_dir=(0.7, -1.2, 1.0), zoom=1.3)
GRIP = ('Base', 'Cover', 'Motor', 'LeadScrew', 'LockCollar', 'Bearing608', 'Carriage', 'T8_Nut', 'BellCrank', 'FrontCrank', 'ConRod', 'Finger',
        'SS_', 'Dowel', 'Sleeve', 'LocPin', 'BHS_Cover', 'BHS_Motor', 'BHN_', 'TipBlock', 'Pad', 'BHT_', 'EncPuck', 'Magnet', 'AS5600')
CTRL = ('Protoboard', 'Spacer', 'Pico', 'PicoHeaders', 'TMC2209', 'TMCHeaders', 'Regulator', 'Cap100', 'PDTrigger', 'BHC_')
LID = ('ElecCover', 'BHL_')
sc('overview', build(GRIP + CTRL + LID, washed=False), cam_dir=(0.8, -1.2, 0.9), zoom=1.35)
sc('d3_dowels', build(('Base', 'Dowel', 'LocPin', 'Sleeve'), new=('Dowel', 'LocPin', 'Sleeve'),
   offsets={'Dowel': (0, 0, -22), 'Sleeve': (0, 0, 16), 'LocPin': (0, 0, 14)}), **cam)
sc('d5_carriage', build(('Motor', 'LeadScrew', 'Carriage', 'T8_Nut', 'BHN_', 'Bearing608', 'LockCollar'),
   new=('Carriage', 'T8_Nut', 'BHN_', 'Bearing608', 'LockCollar'), offsets={'LockCollar': (14, 0, 0), 'Bearing608': (30, 0, 0), 'T8_Nut': (0, 0, 0)}),
   cam_dir=(0.6, -1.3, 0.7), zoom=1.1)
drive = ('Base', 'Dowel', 'Sleeve', 'LocPin', 'Motor', 'LeadScrew', 'LockCollar', 'Carriage', 'T8_Nut', 'BHN_', 'Bearing608', 'BHS_Motor_Base')
up = {k: (0, 0, 30) for k in ('Motor', 'LeadScrew', 'LockCollar', 'Carriage', 'T8_Nut', 'BHN_', 'Bearing608')}; up['BHS_Motor_Base'] = (14, 0, 0)
sc('d6_drive', build(drive, new=drive[4:], offsets=up), **cam)
sc('d7_encoder', build(drive + ('EncPuck', 'Magnet', 'AS5600'), new=('EncPuck', 'Magnet', 'AS5600'),
   offsets={'EncPuck': (14, 0, 0), 'Magnet': (20, 0, 0), 'AS5600': (0, 0, 26)}), cam_dir=(1.2, -0.9, 0.9), zoom=1.5)
d7 = drive + ('EncPuck', 'Magnet', 'AS5600')
cam8 = dict(cam_dir=(0.7, -1.2, 1.1), zoom=1.3)
sc('d8a_lower', build(d7 + ('BellCrank_Lower', 'FrontCrank_Lower'), new=('BellCrank_Lower', 'FrontCrank_Lower'),
   offsets={'BellCrank_Lower': (0, 0, 12), 'FrontCrank_Lower': (0, 0, 12)}), **cam8)
sc('d8b_fingers', build(d7 + ('BellCrank_Lower', 'FrontCrank_Lower', 'Finger', 'ConRod'), new=('Finger', 'ConRod'),
   offsets={'Finger': (0, 0, 14), 'ConRod': (0, 0, 14)}), **cam8)
sc('d8c_upper', build(d7 + ('BellCrank', 'FrontCrank', 'Finger', 'ConRod', 'SS_'), new=('BellCrank_Upper', 'FrontCrank_Upper', 'SS_'),
   offsets={'BellCrank_Upper': (0, 0, 12), 'FrontCrank_Upper': (0, 0, 12), 'SS_': (0, 0, 28)}), **cam8)
link = d7 + ('BellCrank', 'FrontCrank', 'Finger', 'ConRod', 'SS_')
sc('d9_tips', build(link + ('TipBlock', 'Pad', 'BHT_'), new=('TipBlock', 'Pad', 'BHT_'),
   offsets={'TipBlock': (0, 0, -16), 'Pad': (0, 0, -16), 'BHT_': (0, 0, -30)}), cam_dir=(1.1, -1.0, -0.55), zoom=1.3)
inside = link + ('TipBlock', 'Pad', 'BHT_')
sc('d10_cover', build(inside + ('Cover',), washed=False, offsets={'Cover': (0, 0, 35)})
   + [(m, G.HL, 1.0) for m, _, _ in build(('BHS_Cover', 'BHS_Motor_Cover'), offsets={'BHS_Cover': (0, 0, 55), 'BHS_Motor_Cover': (14, 0, 35)})], **cam)
closed = inside + ('Cover', 'BHS_Cover', 'BHS_Motor_Cover')
sc('e1_controller', build(closed + CTRL, new=CTRL, offsets={'Spacer': (0, 0, 10), 'BHC_': (0, 0, 40), **{k: (0, 0, 22) for k in CTRL if k not in ('Spacer', 'BHC_')}}),
   cam_dir=(0.5, -1.2, 1.1), zoom=1.3)
sc('e4_lid', build(closed + CTRL + LID, new=LID, offsets={'ElecCover': (0, 0, 30), 'BHL_': (0, 0, 46)}), cam_dir=(0.5, -1.2, 1.1), zoom=1.3)
STAND = ('StandBase', 'Column', 'StandBracket', 'StandClamp', 'StandKnob', 'Adapter', 'BHS_Side')
sc('g_stand', build(closed + CTRL + LID + STAND, washed=False), cam_dir=(1.0, -1.3, 0.5), zoom=1.2)
sc('g_stand_parts', build(STAND, new=('StandClamp', 'StandKnob', 'StandBracket', 'Adapter'), offsets={'StandBracket': (0, 0, 0)}), cam_dir=(1.0, -1.3, 0.5), zoom=1.2)
