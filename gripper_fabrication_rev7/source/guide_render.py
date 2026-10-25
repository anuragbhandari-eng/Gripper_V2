"""Build-guide step renders for rev 6 (pyvista, offscreen; no display or GPU needed).
Run from this folder:  python3 guide_render.py         -> every step image
                       python3 guide_render.py plates  -> only 01_print_plates.png
Writes ../images/build_guide/*.png. Blue = parts added in that step, pale = already installed."""
import os, sys, shutil, tempfile, numpy as np, pyvista as pv
from PIL import Image
import design as D, render as R, check as C
from prims import cq_part
pv.OFF_SCREEN = True
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'images', 'build_guide')
os.makedirs(OUT, exist_ok=True)
TH = lambda g: np.arcsin(g/(2*D.L) + np.sin(D.TH_C))
GOLD = '#c9a24a'
HL = '#2f6fde'   # parts added in this step
def mesh_of(ops, M):
    T = R.tris('x', ops, M)
    pts = T.reshape(-1, 3); n = len(T)
    faces = np.hstack([np.full((n, 1), 3), np.arange(3*n).reshape(n, 3)]).ravel()
    return pv.PolyData(pts, faces).clean()
def cyl(c, d, r, h):
    return pv.Cylinder(center=np.array(c) + np.array(d)*h/2, direction=d, radius=r, height=h, resolution=40)
def light(col, f=0.55):   # washed-out version for "already installed"
    c = np.array(pv.Color(col).float_rgb); return tuple(c + (1-c)*f)
def scene(name, items, cam_dir=(0.9, -1.3, 1.0), zoom=1.25, title=None, size=(1400, 900), focus=None, labels=(), out=OUT):
    """items: list of (mesh, color, opacity). labels: list of (xyz, text)."""
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background('white')
    for m, col, op in items:
        p.add_mesh(m, color=col, opacity=op, smooth_shading=False, specular=0.15, ambient=0.25, diffuse=0.75)
        if op > 0.9:
            fe = m.extract_feature_edges(feature_angle=35, boundary_edges=False, non_manifold_edges=False, manifold_edges=False)
            if fe.n_points: p.add_mesh(fe, color='#202020', line_width=1.0)
    for pos, text in labels:
        p.add_point_labels([pos], [text], font_size=34, point_size=1, shape_color='white', shape_opacity=0.85,
                           text_color='#111111', always_visible=True, show_points=False)
    b = np.array(p.bounds).reshape(3, 2); ctr = b.mean(1) if focus is None else np.array(focus)
    dist = np.linalg.norm(b[:, 1]-b[:, 0])*1.6
    d = np.array(cam_dir, float); d /= np.linalg.norm(d)
    p.camera.position = tuple(ctr + d*dist); p.camera.focal_point = tuple(ctr); p.camera.up = (0, 0, 1)
    p.camera.zoom(zoom)
    if title: p.add_text(title, position='upper_left', font_size=16, color='#111111')
    path = os.path.join(out, f'{name}.png'); p.screenshot(path); p.close()
    if out == OUT: print('wrote ../images/build_guide/' + os.path.basename(path))
    return path
def build(th, show, new=(), offsets=None, washed=True, extra=()):
    """Parts whose name starts with any of `show`; `new` ones in blue, the rest pale (or true colour if washed=False)."""
    offsets = offsets or {}
    out = []
    for n, (ops, M) in D.pose(th).items():
        if not any(n.startswith(s) for s in show): continue
        m = mesh_of(ops, M)
        for k, off in offsets.items():
            if n.startswith(k): m = m.translate(off, inplace=False)
        isnew = any(n.startswith(s) for s in new)
        col = R.color(n)
        out.append((m, (HL if washed else col) if isnew else (light(col, 0.6) if washed else col), 1.0))
    return out + list(extra)
def centre(th, prefix, off=(0, 0, 0)):
    """Centre of a part's bounding box in pose th (+ offset), for labels."""
    for n, (ops, M) in D.pose(th).items():
        if n.startswith(prefix):
            b = np.array(mesh_of(ops, M).bounds).reshape(3, 2); return tuple(b.mean(1) + np.array(off))
def plates():
    """01: every print file laid flat the way it prints, labelled with its file number and quantity, plus the fit-test coupons."""
    import export_orient as EO
    from PIL import ImageDraw, ImageFont
    W, H = 1400, 900
    p = pv.Plotter(off_screen=True, window_size=(W, H)); p.set_background('white')
    cols = {'Base': R.color('Base'), 'Cover': R.color('Cover'), 'Adapter': R.color('Adapter'), 'Carriage': R.color('Carriage'),
            'BellCrank': R.color('BellCrank'), 'FrontCrank': R.color('FrontCrank'), 'ConRod': R.color('ConRod'), 'Finger': R.color('Finger')}
    items = []
    for fn, ops, how, qty, note in EO.PRINT:
        s_ = EO.orient(cq_part(ops), how); vs, fs = s_.tessellate(0.3, 0.5)
        V = np.array([[v.x, v.y, v.z] for v in vs]); F = np.array(fs)
        items.append((fn, qty, pv.PolyData(V, np.hstack([np.full((len(F), 1), 3), F]).ravel()).clean(), cols[fn.split('_')[1]]))
    items.append(('13_FitTest_coupons', 1, pv.read(os.path.join(HERE, '..', 'stl', '13_FitTest_coupons.stl')).clean(), R.color('Carriage')))
    x = 0.0; y = 0.0; rowh = 0.0; col = 0; anchors = []
    for fn, qty, m, colr in items:
        bb = m.bounds; w, d = bb[1]-bb[0], bb[3]-bb[2]
        if col == 5: x = 0.0; y -= rowh + 40; rowh = 0.0; col = 0
        m = m.translate((x - bb[0], y - bb[3], 0), inplace=False)
        p.add_mesh(m, color=colr, smooth_shading=False, ambient=0.25, diffuse=0.75)
        fe = m.extract_feature_edges(feature_angle=35, boundary_edges=False, non_manifold_edges=False, manifold_edges=False)
        if fe.n_points: p.add_mesh(fe, color='#202020', line_width=1.0)
        anchors.append(((x + w/2, y - d - 4, 0), f"{fn.split('_')[0]}  x{qty}" + ('  (print first)' if fn.startswith('13_') else '')))
        x += max(w, 60) + 25; rowh = max(rowh, d); col += 1
    p.enable_parallel_projection(); p.camera_position = 'xy'; p.reset_camera(); p.camera.zoom(1.5); p.render()
    img = Image.fromarray(p.screenshot(return_img=True)); ren = p.renderer
    try: font = ImageFont.truetype('DejaVuSans-Bold.ttf', 22)
    except OSError: font = ImageFont.load_default(size=22)
    dr = ImageDraw.Draw(img)
    for pt, text in anchors:   # labels drawn after rendering, so none get culled
        ren.SetWorldPoint(*pt, 1.0); ren.WorldToDisplay(); px, py, _ = ren.GetDisplayPoint()
        tw = dr.textlength(text, font=font); dr.text((px - tw/2, H - py + 4), text, fill='#111111', font=font)
    p.close(); img.save(os.path.join(OUT, '01_print_plates.png')); print('wrote ../images/build_guide/01_print_plates.png')
def steps():
    th30 = TH(30)
    SCR = ('BHS_', 'BHN_')   # the 16 M3 button heads
    allp = ('Base', 'Cover', 'Adapter', 'Motor', 'LeadScrew', 'LockCollar', 'Bearing608', 'Carriage', 'T8_Nut', 'BellCrank', 'FrontCrank', 'ConRod',
            'Finger', 'SS_', 'Dowel') + SCR
    # 00 exploded overview
    ex = {'Cover': (0, 0, 45), 'BHS_Cover': (0, 0, 62), 'BHS_Motor_Cover': (0, 0, 45), 'Adapter': (-30, 0, 0), 'BHS_Side': (-30, 0, 0),
          'BellCrank_Upper': (0, 0, 22), 'FrontCrank_Upper': (0, 0, 22), 'SS_': (0, 0, 32), 'Finger': (0, 0, 10), 'ConRod': (0, 0, 10)}
    scene('00_exploded', build(th30, allp, new=allp, offsets=ex), cam_dir=(0.8, -1.3, 0.9), zoom=1.35)
    # 02 heat-set inserts (step 1): base, carriage, lower crank plates, adapter -> one 2x2 sheet
    tmp = tempfile.mkdtemp()
    base = mesh_of(D.base(), np.eye(4)); items = [(base, R.color('Base'), 1.0)]
    for (bx, by) in [(D.MW_BOLT_X, D.MW_BOLT_Y), (D.MW_BOLT_X, -D.MW_BOLT_Y), (D.BLK_BOLT[0], D.BLK_BOLT[1]), (D.BLK_BOLT[0], -D.BLK_BOLT[1])]:
        items.append((cyl((bx, by, D.Z_S - 5.7), (0, 0, 1), 2.3, 5.7), GOLD, 1.0))
    for sgn in (1, -1):
        items.append((cyl((D.POST_C[0], sgn*D.POST_C[1], D.Z_C0 - 5.7), (0, 0, 1), 2.3, 5.7), GOLD, 1.0))
    a = scene('02a', items, cam_dir=(0.6, -1.0, 1.4), zoom=0.95, out=tmp, labels=[((D.MW_BOLT_X, D.MW_BOLT_Y, D.Z_S+3), 'motor wall (2)'), ((D.BLK_BOLT[0], 18, D.Z_S+3), 'bearing block (2)'), ((D.POST_C[0], D.POST_C[1], D.Z_C0+3), 'posts (2)')])
    car = mesh_of(D.carriage(), np.eye(4)); items = [(car, R.color('Carriage'), 1.0)]
    for sgn in (1, -1): items.append((cyl((0, sgn*D.YC, D.Z_B1 - 5.7), (0, 0, 1), 2.3, 5.7), GOLD, 1.0))
    b = scene('02b', items, cam_dir=(1.0, -1.6, 0.25), zoom=0.95, out=tmp, labels=[((0, -D.YC, D.Z_B1 + 3.5), 'carriage ears (2)')])
    bcl = mesh_of(D.bc_plate(True), np.eye(4)); fcl = mesh_of(D.fc_plate(True), np.eye(4)).translate((45, -10, 0), inplace=False)
    items = [(bcl, R.color('BellCrank'), 1.0), (fcl, R.color('FrontCrank'), 1.0),
             (cyl((D.L, 0, D.Z_B1-5.7), (0, 0, 1), 2.3, 5.7), GOLD, 1.0), (cyl((0, -D.r, D.Z_B1-5.7), (0, 0, 1), 2.3, 5.7), GOLD, 1.0),
             (cyl((45 + D.L, -10, D.Z_B1-5.7), (0, 0, 1), 2.3, 5.7), GOLD, 1.0)]
    c = scene('02c', items, cam_dir=(0.3, -1.0, 1.5), zoom=1.0, out=tmp, labels=[((D.L, 0, 9), 'F1'), ((0, -D.r, 9), 'D'), ((45 + D.L, -10, 9), 'F2')])
    ad = mesh_of(D.adapter(), np.eye(4)); items = [(ad, R.color('Adapter'), 1.0)]
    for sgn in (1, -1):
        for zr in D.AD_SCREW_Z: items.append((cyl((D.X_AD0 + 7, sgn*D.AD_HW, zr), (0, -sgn, 0), 2.3, 5.7), GOLD, 1.0))
    d = scene('02d', items, cam_dir=(0.9, -1.4, 0.5), zoom=0.75, out=tmp, labels=[((D.X_AD0 + 7, -D.AD_HW, D.AD_SCREW_Z[1] + 6), 'adapter sides (4)')])
    sheet = Image.new('RGB', (1400, 900), 'white')
    for i, f in enumerate((a, b, c, d)):
        sheet.paste(Image.open(f).convert('RGB').resize((700, 450), Image.LANCZOS), ((i % 2)*700, (i // 2)*450))
    sheet.save(os.path.join(OUT, '02_inserts.png')); print('wrote ../images/build_guide/02_inserts.png')
    shutil.rmtree(tmp)
    # 03 dowels into the base (step 2)
    scene('03_dowels', build(th30, ('Base', 'Dowel'), new=('Dowel',), offsets={'Dowel': (0, 0, 14)}), cam_dir=(0.7, -1.2, 1.0), zoom=1.3)
    # 04 nut into the carriage from the front + its 2 button heads (step 4)
    car_items = [(car, R.color('Carriage'), 1.0), (mesh_of(D.nut(), np.eye(4)).translate((18, 0, 0), inplace=False), R.color('T8_Nut'), 1.0)]
    for sgn in (1, -1):
        car_items.append((cyl((D.POCKET_X0 + 0.1 + D.NUT_FL_T + 30, sgn*D.NUT_SCREW_Y, D.Z_S), (-1, 0, 0), 2.85, 1.65), '#1b1b1b', 1.0))
        car_items.append((cyl((D.POCKET_X0 + 0.1 + D.NUT_FL_T + 30 - 1.65 - 8, sgn*D.NUT_SCREW_Y, D.Z_S), (1, 0, 0), 1.5, 8), '#555555', 1.0))
    scene('04_nut_into_carriage', car_items, cam_dir=(1.2, -0.8, 0.7), zoom=1.0)
    # 05 carriage, lock collar and 608 onto the cut motor screw (step 5), exploded along the axis
    off5 = {'LockCollar': (14, 0, 0), 'Bearing608': (30, 0, 0)}
    scene('05_screw_carriage_bearing', build(th30, ('Motor', 'LeadScrew', 'Carriage', 'T8_Nut', 'BHN_', 'Bearing608'),
          new=('Carriage', 'T8_Nut', 'BHN_', 'Bearing608'), offsets=off5, washed=False)
          + [(m, HL, 1.0) for m, _, _ in build(th30, ('LockCollar',), offsets=off5)],
          cam_dir=(0.6, -1.3, 0.7), zoom=1.1,
          labels=[(centre(th30, 'LockCollar', (14, 0, 14)), 'lock collar'), (centre(th30, 'Bearing608', (30, 0, -18)), '608ZZ')])
    # 06 drive into the base + 2 lower motor screws (step 6)
    drive = ('Base', 'Dowel', 'Motor', 'LeadScrew', 'LockCollar', 'Carriage', 'T8_Nut', 'BHN_', 'Bearing608', 'BHS_Motor_Base')
    up = {k: (0, 0, 30) for k in ('Motor', 'LeadScrew', 'LockCollar', 'Carriage', 'T8_Nut', 'BHN_', 'Bearing608')}
    up['BHS_Motor_Base'] = (14, 0, 0)
    scene('06_drive_in_base', build(th30, drive, new=drive[2:], offsets=up), cam_dir=(0.7, -1.2, 1.0), zoom=1.3)
    # 07a lower plates on the dowels (step 7)
    scene('07a_lower_plates', build(th30, drive + ('BellCrank_Lower', 'FrontCrank_Lower'), new=('BellCrank_Lower', 'FrontCrank_Lower'),
          offsets={'BellCrank_Lower': (0, 0, 12), 'FrontCrank_Lower': (0, 0, 12)}), cam_dir=(0.7, -1.2, 1.1), zoom=1.3)
    # 07b fingers + conrods
    scene('07b_fingers_conrods', build(th30, drive + ('BellCrank_Lower', 'FrontCrank_Lower', 'Finger', 'ConRod'), new=('Finger', 'ConRod'),
          offsets={'Finger': (0, 0, 14), 'ConRod': (0, 0, 14)}), cam_dir=(0.7, -1.2, 1.1), zoom=1.3)
    # 07c upper plates + shoulder screws
    scene('07c_upper_plates_screws', build(th30, drive + ('BellCrank', 'FrontCrank', 'Finger', 'ConRod', 'SS_'), new=('BellCrank_Upper', 'FrontCrank_Upper', 'SS_'),
          offsets={'BellCrank_Upper': (0, 0, 12), 'FrontCrank_Upper': (0, 0, 12), 'SS_': (0, 0, 28)}), cam_dir=(0.7, -1.2, 1.1), zoom=1.3)
    # 08 cover onto the dowels, then its 6 screws and the 2 upper motor screws (step 8)
    inside = tuple(x for x in allp if x not in ('Cover', 'Adapter', 'BHS_')) + ('BHS_Motor_Base',)
    scene('08_cover', build(th30, inside + ('Cover',), washed=False, offsets={'Cover': (0, 0, 35)})
          + [(m, HL, 1.0) for m, _, _ in build(th30, ('BHS_Cover', 'BHS_Motor_Cover'), offsets={'BHS_Cover': (0, 0, 55), 'BHS_Motor_Cover': (14, 0, 35)})],
          cam_dir=(0.7, -1.2, 1.0), zoom=1.3)
    # 09 adapter on the robot first, gripper slides on, 4 side screws (step 9)
    grip = tuple(x for x in allp if x not in ('Adapter', 'BHS_')) + ('BHS_Motor', 'BHS_Cover')
    side = {'BHS_Side_Base_U': (40, 14, 0), 'BHS_Side_Cover_U': (40, 14, 0), 'BHS_Side_Base_L': (40, -14, 0), 'BHS_Side_Cover_L': (40, -14, 0)}
    g = build(th30, grip, washed=False, offsets={k: (40, 0, 0) for k in grip})
    s = [(m, HL, 1.0) for m, _, _ in build(th30, ('BHS_Side',), offsets=side)]
    scene('09_adapter', g + s + [(mesh_of(D.adapter(), np.eye(4)), R.color('Adapter'), 1.0)], cam_dir=(0.4, -1.3, 0.7), zoom=1.3)
if __name__ == '__main__':
    if sys.argv[-1] != 'plates': steps()
    plates()
