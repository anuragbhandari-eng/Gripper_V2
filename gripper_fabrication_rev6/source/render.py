import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import design as D, check as C
COL = {'Base': '#3d424a', 'Cover': '#4b515a', 'Adapter': '#2f343a', 'Carriage': '#8d939b', 'Finger': '#e8742a',
       'BellCrank': '#c9cdd2', 'FrontCrank': '#c9cdd2', 'ConRod': '#b4b9bf', 'SS_': '#1b1b1b', 'Motor': '#222326',
       'LeadScrew': '#c4c6c8', 'T8_Nut': '#c9a24a', 'Bearing608': '#a9adb2', 'Dowel': '#dcdcdc'}
def color(n):
    for k, v in COL.items():
        if n.startswith(k): return v
    return '#999999'
def tris(n, ops, M):
    s = C.solid(ops); vs, fs = s.tessellate(0.3, 0.5)
    V = np.array([[v.x, v.y, v.z] for v in vs]); V = (M[:3, :3] @ V.T).T + M[:3, 3]
    return V[np.array(fs)]
def draw(ax, th, hide=(), elev=30, azim=-60, title=''):
    parts = D.pose(th)
    allv = []
    for n, (ops, M) in parts.items():
        if any(n.startswith(hh) for hh in hide): continue
        T = tris(n, ops, M); allv.append(T.reshape(-1, 3))
        pc = Poly3DCollection(T, facecolor=color(n), edgecolor='none', alpha=1.0)
        # simple lambert shading
        nrm = np.cross(T[:, 1]-T[:, 0], T[:, 2]-T[:, 0]); nrm /= (np.linalg.norm(nrm, axis=1)[:, None]+1e-12)
        ld = np.array([0.4, -0.5, 0.8]); ld /= np.linalg.norm(ld)
        sh = 0.45 + 0.55*np.abs(nrm @ ld)
        base = np.array(matplotlib.colors.to_rgb(color(n)))
        pc.set_facecolor(np.clip(base[None, :]*sh[:, None], 0, 1)); ax.add_collection3d(pc)
    A = np.vstack(allv); mn, mx = A.min(0), A.max(0); c = (mn+mx)/2; rr = (mx-mn).max()/2
    ax.set_xlim(c[0]-rr, c[0]+rr); ax.set_ylim(c[1]-rr, c[1]+rr); ax.set_zlim(c[2]-rr, c[2]+rr)
    ax.view_init(elev, azim); ax.set_axis_off(); ax.set_title(title, fontsize=9)
    try: ax.set_box_aspect((1, 1, 1))
    except Exception: pass
if __name__ == '__main__':
    import sys
    fig = plt.figure(figsize=(16, 10))
    gaps = [0.0, 30.0, 66.0]
    ths = [np.arcsin(g/(2*D.L) + np.sin(D.TH_C)) for g in gaps]
    for i, (g, th) in enumerate(zip(gaps, ths)):
        ax = fig.add_subplot(2, 3, i+1, projection='3d'); draw(ax, th, hide=('Cover',), elev=90, azim=-90, title=f'top, cover hidden, gap {g:.0f} mm')
    ax = fig.add_subplot(2, 3, 4, projection='3d'); draw(ax, ths[1], elev=28, azim=-55, title='iso, assembled, gap 30')
    ax = fig.add_subplot(2, 3, 5, projection='3d'); draw(ax, ths[2], hide=('Cover', 'Base', 'Adapter', 'Motor'), elev=35, azim=-120, title='links + carriage, gap 66')
    ax = fig.add_subplot(2, 3, 6, projection='3d'); draw(ax, ths[0], elev=-25, azim=-50, title='underside, gap 0')
    plt.tight_layout(); plt.savefig(sys.argv[1] if len(sys.argv) > 1 else 'render.png', dpi=80)
