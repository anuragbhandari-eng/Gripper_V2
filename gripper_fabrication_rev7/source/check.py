import numpy as np, time, json, sys
import cadquery as cq
from OCP.gp import gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
import design as D
from prims import cq_part

cache = {}
def solid(ops):
    k = id(ops) if False else repr(ops)
    if k not in cache: cache[k] = cq_part(ops)
    return cache[k]
def place(shape, M):
    t = gp_Trsf(); t.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
    return BRepBuilderAPI_Transform(shape.wrapped, t, True).Shape()
def vol(s):
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s, p); return p.Mass()
def bbox(s):
    b = Bnd_Box(); BRepBndLib.Add_s(s, b); return np.array(b.CornerMin().Coord()), np.array(b.CornerMax().Coord())
def common(a, b):
    c = BRepAlgoAPI_Common(a, b); c.Build(); return vol(c.Shape())

ALLOW = {('Base', 'Dowel'): 5.0,    # press fit interference allowed (mm^3)
         ('Motor', 'BHS_Motor'): 60.0,   # M3 thread engaged in the motor's tapped holes (modelled at major dia.)
         ('Carriage', 'BHN_Nut'): 60.0}  # M3 self-tapped into the D2.5 pilots
def allowed(a, b, v):
    for (x, y), lim in ALLOW.items():
        if (a.startswith(x) and b.startswith(y)) or (b.startswith(x) and a.startswith(y)): return v <= lim
    return False

def run(nposes=21, verbose=True):
    t0 = time.time()
    # 1) part validity
    rep = {}
    p0 = D.pose(D.TH_C)
    for n, (ops, M) in p0.items():
        s = solid(ops); ns = len(s.Solids())
        rep[n] = dict(valid=s.isValid(), nsolids=ns, vol=round(s.Volume(), 1))
    bad = {n: v for n, v in rep.items() if not v['valid'] or v['nsolids'] != 1}
    print('parts', len(rep), 'invalid/multi-solid:', bad)
    # 2) collision sweep
    hits = {}
    ths = np.linspace(D.TH_C, D.TH_O, nposes)
    for th in ths:
        parts = D.pose(th)
        placed = {n: place(solid(o), M) for n, (o, M) in parts.items()}
        bbs = {n: bbox(s) for n, s in placed.items()}
        names = list(placed)
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                a, b = names[i], names[j]
                if not (D.MOVING(a) or D.MOVING(b)) and th != ths[0]: continue
                (amin, amax), (bmin, bmax) = bbs[a], bbs[b]
                if np.any(amax < bmin - 1e-6) or np.any(bmax < amin - 1e-6): continue
                v = common(placed[a], placed[b])
                if v > 1e-3 and not allowed(a, b, v):
                    key = tuple(sorted((a, b)))
                    hits.setdefault(key, []).append((round(np.degrees(th), 1), round(v, 2)))
    print('collision pairs:', len(hits))
    for k, v in sorted(hits.items()): print(' ', k, v[:4], '...' if len(v) > 4 else '')
    print('time %.0fs' % (time.time()-t0))
    return rep, hits
if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    rep, hits = run(n)
    json.dump(dict(parts=rep, hits={'|'.join(k): v for k, v in hits.items()}), open('check_report_wide.json' if D.TIP_WIDE else 'check_report.json', 'w'), indent=1)   # rev 7: GRIPPER_TIPSET=wide checks the wide tips

def clearance(nposes=31, thresh=0.6):
    """Min 3D distance between part pairs (moving involved). Reports pairs closer than thresh, min over poses."""
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    res = {}
    for th in np.linspace(D.TH_C, D.TH_O, nposes):
        parts = D.pose(th)
        placed = {n: place(solid(o), M) for n, (o, M) in parts.items()}
        bbs = {n: bbox(s) for n, s in placed.items()}
        names = list(placed)
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                a, b = names[i], names[j]
                if not (D.MOVING(a) or D.MOVING(b)): continue
                (amin, amax), (bmin, bmax) = bbs[a], bbs[b]
                if np.any(amax < bmin - thresh) or np.any(bmax < amin - thresh): continue
                d = BRepExtrema_DistShapeShape(placed[a], placed[b]); d.Perform()
                v = d.Value()
                key = tuple(sorted((a, b)))
                if v < thresh and (key not in res or v < res[key][0]): res[key] = (round(v, 3), round(np.degrees(th), 1))
    return res
