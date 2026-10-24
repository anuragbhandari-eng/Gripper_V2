import numpy as np, matplotlib, sys, os; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_UniformAbscissa
from OCP.TopoDS import TopoDS
import design as D, check as C, render as R
def edges_at(shape, z):
    sec = BRepAlgoAPI_Section(shape, gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1))); sec.Build()
    out = []; ex = TopExp_Explorer(sec.Shape(), TopAbs_EDGE)
    while ex.More():
        e = TopoDS.Edge_s(ex.Current()); c = BRepAdaptor_Curve(e)
        a = GCPnts_UniformAbscissa(c, 40, 1e-3)
        pts = [c.Value(a.Parameter(i)).Coord() for i in range(1, a.NbPoints()+1)] if a.IsDone() else []
        out.append(np.array(pts)); ex.Next()
    return out
gaps = [0, 30, 66]; zs = [(3.3, 'B layer z=3.3'), (10.0, 'M layer z=10'), (16.0, 'U layer z=16'), (20.0, 'heads/jaw z=20')]
fig, axs = plt.subplots(len(zs), 3, figsize=(15, 4.3*len(zs)))
for j, g in enumerate(gaps):
    th = np.arcsin(g/(2*D.L) + np.sin(D.TH_C)); parts = D.pose(th)
    placed = {n: C.place(C.solid(o), M) for n, (o, M) in parts.items()}
    for i, (z, lab) in enumerate(zs):
        ax = axs[i, j]
        for n, s in placed.items():
            for e in edges_at(s, z):
                if len(e): ax.plot(e[:, 0], e[:, 1], '-', color=R.color(n), lw=0.9)
        ax.set_aspect('equal'); ax.set_xlim(-60, 105); ax.set_ylim(-85, 85); ax.grid(alpha=.2)
        ax.set_title(f'{lab}, gap {g} mm', fontsize=9)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images', 'sections_final.png')
plt.tight_layout(); plt.savefig(OUT, dpi=70); print('wrote', OUT)
