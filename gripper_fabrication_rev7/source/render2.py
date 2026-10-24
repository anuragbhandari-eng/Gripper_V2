import numpy as np, matplotlib, sys, os; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import design as D, render as R
STAND = ('Stand', 'Column', 'Battery')
def scene(ax, th, hide=(), elev=28, azim=-55, title='', rot=None):
    allT, allC = [], []
    for n, (ops, M) in D.pose(th).items():
        if any(n.startswith(h) for h in hide): continue
        T = R.tris(n, ops, M)
        if rot is not None: T = T @ rot.T
        allT.append(T)
        nrm = np.cross(T[:, 1]-T[:, 0], T[:, 2]-T[:, 0]); nrm /= (np.linalg.norm(nrm, axis=1)[:, None]+1e-12)
        ld = np.array([0.3, -0.6, 0.75]); ld /= np.linalg.norm(ld)
        sh = 0.40 + 0.60*np.abs(nrm @ ld)
        base = np.array(matplotlib.colors.to_rgb(R.color(n)))
        allC.append(np.clip(base[None, :]*sh[:, None], 0, 1))
    T = np.vstack(allT); Cc = np.vstack(allC)
    ax.add_collection3d(Poly3DCollection(T, facecolors=Cc, edgecolor='none'))
    A = T.reshape(-1, 3); mn, mx = A.min(0), A.max(0); c = (mn+mx)/2; rr = (mx-mn).max()/2*0.85
    ax.set_xlim(c[0]-rr, c[0]+rr); ax.set_ylim(c[1]-rr, c[1]+rr); ax.set_zlim(c[2]-rr, c[2]+rr)
    ax.view_init(elev, azim); ax.set_axis_off(); ax.set_title(title, fontsize=11)
    try: ax.set_box_aspect((1, 1, 1))
    except Exception: pass
th = lambda g: np.arcsin(g/(2*D.L) + np.sin(D.TH_C))
fig = plt.figure(figsize=(16, 11))
scene(fig.add_subplot(2, 2, 1, projection='3d'), th(30), hide=STAND, title='Assembled, jaw gap 30 mm')
scene(fig.add_subplot(2, 2, 2, projection='3d'), th(66), hide=('Cover',) + STAND, elev=55, azim=-70, title='Cover removed, fully open (66 mm)')
scene(fig.add_subplot(2, 2, 3, projection='3d'), th(0), hide=('Cover',) + STAND, elev=55, azim=-70, title='Cover removed, closed (0 mm)')
scene(fig.add_subplot(2, 2, 4, projection='3d'), th(30), hide=('Cover', 'Base', 'Adapter', 'Motor', 'Dowel', 'BHS_', 'AS5600', 'Protoboard', 'Pico', 'TMC2209', 'Buck', 'Standoff') + STAND, elev=35, azim=-125, title='Mechanism only (links, carriage, screw, nut, collar)')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images', 'render_final.png')
plt.tight_layout(); plt.savefig(OUT, dpi=75); print('wrote', OUT)
# rev 7: the gripper on its bench stand, jaws down (gripper +x shown as down)
fig = plt.figure(figsize=(8, 10))
scene(fig.add_subplot(1, 1, 1, projection='3d'), th(30), elev=12, azim=-35, title='Bench stand, jaws down, gap 30 mm',
      rot=np.array([[0, 0, 1.0], [0, 1.0, 0], [-1.0, 0, 0]]))
OUT2 = os.path.join(os.path.dirname(OUT), 'render_stand.png')
plt.tight_layout(); plt.savefig(OUT2, dpi=75); print('wrote', OUT2)
