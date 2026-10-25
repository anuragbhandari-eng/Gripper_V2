"""Tiny CSG description shared by CadQuery (local checks) and FeatureScript (Onshape).
Profile loop: start point + list of segments ('L', p) or ('A', mid, p) (3-point arc). Units mm.
Ops per part: list of (op, prim) op in {'add','cut'}; prim:
  ('ext', loop, z0, z1)               extrude XY loop between z0..z1
  ('cyl', p0(xyz), p1(xyz), r)        cylinder between two points
  ('box', (x0,y0,z0), (x1,y1,z1))"""
import numpy as np
def PT(x, y): return (float(x), float(y))

def circle_loop(c, r):
    c = np.array(c, float)
    return dict(start=PT(*(c+[r, 0])), segs=[('A', PT(*(c+[0, r])), PT(*(c-[r, 0]))), ('A', PT(*(c-[0, r])), PT(*(c+[r, 0])))])

def poly_loop(pts):
    return dict(start=PT(*pts[0]), segs=[('L', PT(*p)) for p in list(pts[1:])+[pts[0]]])

def hull_circles(circles):
    """Convex hull of circles [(c,r),...] (r may be 0 for points) -> loop of tangent lines + arcs (CCW)."""
    import itertools
    C = [(np.array(c, float), float(r)) for c, r in circles]
    # sample-based hull to find which circles and in what order, then exact tangents
    pts = []; owner = []
    for i, (c, r) in enumerate(C):
        n = 720 if r > 0 else 1
        for a in np.linspace(0, 2*np.pi, n, endpoint=False):
            pts.append(c + r*np.array([np.cos(a), np.sin(a)])); owner.append(i)
    pts = np.array(pts)
    from scipy.spatial import ConvexHull
    h = ConvexHull(pts).vertices  # CCW
    seq = []
    for v in h:
        if not seq or seq[-1] != owner[v]: seq.append(owner[v])
    if len(seq) > 1 and seq[0] == seq[-1]: seq.pop()
    # exact outer tangent between consecutive circles (CCW hull => tangent on right side going i->j)
    def tangent(i, j):
        (c1, r1), (c2, r2) = C[i], C[j]
        d = c2-c1; L = np.linalg.norm(d); u = d/L
        a = np.arcsin((r1-r2)/L) if L > 0 else 0
        # normal pointing outward (right of direction for CCW traversal)
        rot = lambda v, t: np.array([v[0]*np.cos(t)-v[1]*np.sin(t), v[0]*np.sin(t)+v[1]*np.cos(t)])
        n = rot(u, -np.pi/2 + a)
        n = rot(u, -(np.pi/2 - a))
        return c1 + r1*n, c2 + r2*n
    T = [tangent(seq[k], seq[(k+1) % len(seq)]) for k in range(len(seq))]
    segs = []; start = None
    for k in range(len(seq)):
        p_in = T[k-1][1]; p_out = T[k][0]; c, r = C[seq[k]]
        if start is None: start = PT(*p_in)
        if r > 0 and np.linalg.norm(p_out-p_in) > 1e-6:
            a0 = np.arctan2(*(p_in-c)[::-1]); a1 = np.arctan2(*(p_out-c)[::-1])
            da = (a1-a0) % (2*np.pi)
            am = a0+da/2; mid = c+r*np.array([np.cos(am), np.sin(am)])
            segs.append(('A', PT(*mid), PT(*p_out)))
        segs.append(('L', PT(*T[k][1])))
    return dict(start=start, segs=segs)

def arc_band_loop(c, r_in, r_out, a0, a1):
    """Annular sector around c from angle a0 to a1 (rad, CCW) with round end caps (swept circle)."""
    c = np.array(c, float); rm = (r_in+r_out)/2; w = (r_out-r_in)/2
    pt = lambda r, a: c + r*np.array([np.cos(a), np.sin(a)])
    am = (a0+a1)/2
    e1 = pt(rm, a1); e0 = pt(rm, a0)
    u1 = np.array([np.cos(a1), np.sin(a1)]); t1 = np.array([-np.sin(a1), np.cos(a1)])
    u0 = np.array([np.cos(a0), np.sin(a0)]); t0 = np.array([-np.sin(a0), np.cos(a0)])
    segs = [('A', PT(*pt(r_out, am)), PT(*pt(r_out, a1))),
            ('A', PT(*(e1+w*t1)), PT(*pt(r_in, a1))),
            ('A', PT(*pt(r_in, am)), PT(*pt(r_in, a0))),
            ('A', PT(*(e0-w*t0)), PT(*pt(r_out, a0)))]
    return dict(start=PT(*pt(r_out, a0)), segs=segs)

def mirror_loop(loop):
    """Mirror Y -> -Y (reverses orientation; fine for extrusion)."""
    m = lambda p: (p[0], -p[1])
    return dict(start=m(loop['start']), segs=[(s[0],)+tuple(m(p) for p in s[1:]) for s in loop['segs']])

def mirror_ops(ops):
    out = []
    for op, pr in ops:
        if pr[0] == 'ext': out.append((op, ('ext', mirror_loop(pr[1]), pr[2], pr[3])))
        elif pr[0] == 'cyl': out.append((op, ('cyl', (pr[1][0], -pr[1][1], pr[1][2]), (pr[2][0], -pr[2][1], pr[2][2]), pr[3])))
        elif pr[0] == 'box':
            (x0, y0, z0), (x1, y1, z1) = pr[1], pr[2]
            out.append((op, ('box', (x0, -y1, z0), (x1, -y0, z1))))
        elif pr[0] == 'extx':   # loop is in (Y, Z): mirror its first coordinate
            m = lambda p: (-p[0], p[1]); lp = pr[1]
            out.append((op, ('extx', dict(start=m(lp['start']), segs=[(s[0],) + tuple(m(p) for p in s[1:]) for s in lp['segs']]), pr[2], pr[3])))
    return out

def clean_loop(loop, tol=1e-4):
    """Drop zero-length segments; ensure loop closes exactly on start."""
    cur = np.array(loop['start']); segs = []
    for sg in loop['segs']:
        end = np.array(sg[-1])
        if np.linalg.norm(end-cur) < tol: continue
        if sg[0] == 'A':
            mid = np.array(sg[1])
            if np.linalg.norm(mid-cur) < tol or np.linalg.norm(mid-end) < tol: sg = ('L', sg[2])
        segs.append(sg); cur = end
    if np.linalg.norm(cur-np.array(loop['start'])) > tol: segs.append(('L', loop['start']))
    else:
        last = segs[-1]; segs[-1] = last[:-1] + (loop['start'],)
    return dict(start=loop['start'], segs=segs)

# ---------------- CadQuery compile ----------------
def cq_prim(pr):
    import cadquery as cq
    if pr[0] == 'ext':
        loop, z0, z1 = clean_loop(pr[1]), pr[2], pr[3]
        w = cq.Workplane('XY', origin=(0, 0, z0)).moveTo(*loop['start'])
        for s in loop['segs']:
            w = w.lineTo(*s[1]) if s[0] == 'L' else w.threePointArc(s[1], s[2])
        return w.close().extrude(z1-z0).val()
    if pr[0] == 'extx':   # loop in (Y,Z) extruded along X from x0 to x1
        loop, x0, x1 = clean_loop(pr[1]), pr[2], pr[3]
        w = cq.Workplane('YZ', origin=(x0, 0, 0)).moveTo(*loop['start'])
        for s in loop['segs']:
            w = w.lineTo(*s[1]) if s[0] == 'L' else w.threePointArc(s[1], s[2])
        return w.close().extrude(x1-x0).val()
    if pr[0] == 'cyl':
        p0, p1, r = np.array(pr[1]), np.array(pr[2]), pr[3]
        d = p1-p0; h = np.linalg.norm(d)
        return cq.Solid.makeCylinder(r, h, cq.Vector(*p0), cq.Vector(*(d/h)))
    if pr[0] == 'box':
        (x0, y0, z0), (x1, y1, z1) = pr[1], pr[2]
        return cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, cq.Vector(x0, y0, z0))

def cq_part(ops):
    shape = None
    for op, pr in ops:
        s = cq_prim(pr)
        if shape is None: shape = s; continue
        shape = shape.fuse(s).clean() if op == 'add' else shape.cut(s).clean()
    return shape

def rrect_loop(x0, y0, x1, y1, r):
    """Rounded rectangle (CCW), corner radius r."""
    r = min(r, (x1-x0)/2 - 1e-3, (y1-y0)/2 - 1e-3)
    c45 = r*(1-np.cos(np.pi/4))
    return dict(start=PT(x0+r, y0), segs=[
        ('L', PT(x1-r, y0)), ('A', PT(x1-c45, y0+c45), PT(x1, y0+r)),
        ('L', PT(x1, y1-r)), ('A', PT(x1-c45, y1-c45), PT(x1-r, y1)),
        ('L', PT(x0+r, y1)), ('A', PT(x0+c45, y1-c45), PT(x0, y1-r)),
        ('L', PT(x0, y0+r)), ('A', PT(x0+c45, y0+c45), PT(x0+r, y0))])

def chamfer_square_loop(cx, cy, half, ch):
    """Square of half-width `half` with 45 deg corner chamfers `ch` (NEMA body)."""
    h = half
    pts = [(cx-h+ch, cy-h), (cx+h-ch, cy-h), (cx+h, cy-h+ch), (cx+h, cy+h-ch), (cx+h-ch, cy+h), (cx-h+ch, cy+h), (cx-h, cy+h-ch), (cx-h, cy-h+ch)]
    return poly_loop(pts)

def hex_loop(cx, cy, af):
    """Hexagon with across-flats af."""
    R = af/np.sqrt(3)
    return poly_loop([(cx+R*np.cos(np.radians(30+60*k)), cy+R*np.sin(np.radians(30+60*k))) for k in range(6)])
