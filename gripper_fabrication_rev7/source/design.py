"""Gripper geometry: every part as CSG ops in its LOCAL frame + pose transforms. Single source of truth.
Assembly frame: X forward (screw axis direction), Y outward (upper side = +Y), Z up from base-plate top.
Origin: X at fixed pivot O1, Y on centerline, Z=0 at base-plate top."""
import numpy as np
from params import make
from kin import geom
from prims import *

P = make(28.0)
L, r, l, YC, h = P['L'], P['r'], P['l'], P['YC'], P['h']
O1 = np.array([0.0, P['YO1']]); V12 = geom(P, 0.0)['O2'] - O1; O2 = O1 + V12
TH_C = P['th_c']; GAP_MAX = 66.0
TH_O = np.arcsin(GAP_MAX/(2*L) + np.sin(TH_C))

# ---------- z stack ----------
Z_BB = -9.0          # base bottom
Z_B0, Z_B1 = 0.3, 6.3      # lower crank plates (6.0 thick)
Z_M0, Z_M1 = 6.5, 14.1     # finger / conrod (7.6 thick = 38 layers of 0.2): 0.2 mm gap below, 0.3 mm above
Z_U0, Z_U1 = 14.4, 18.2    # upper crank plates (3.8 thick); 0.1 mm under the shoulder-screw head seat (18.3)
Z_HD = 21.3                # top of shoulder-screw heads (head 3 mm)
Z_C0, Z_C1 = 22.1, 29.5    # cover
Z_S = 10.3                 # screw axis = finger/conrod mid-plane
Z_JAW = 26.0               # top of jaw extension
CAR_TOP = 21.8
# ---------- holes / hardware ----------
R_RUN = 2.1     # Ø4.2 running fit on 4 mm shoulder/dowel
R_SNUG = 2.05   # Ø4.1 (no relative motion)
R_INS = 2.0     # Ø4.0 hole for M3 heat-set insert (5.7 long)
R_DOW_PRESS = 1.95
R_DOW_CLOSE = 2.0   # cover dowel hole: print Ø4.0, ream 4.0 -> dowel held at both ends
R_M3 = 1.7      # Ø3.4 clearance
R_BOSS = 5.5    # link end boss
R_SPACER = 5.0  # crank spacer boss in M layer
SH_HEAD_R, SH_HEAD_H = 3.5, 3.0   # shoulder screw head Ø7 x 3
# ---------- printed-part material (rev 7: ABS; rev 6 was PETG, 45 MPa, 1.27 g/cm3) ----------
MAT = 'ABS'
MAT_SY = 30.0     # MPa, printed in-plane yield: low end of generic FDM ABS (30-40 MPa); fablab spool, brand unknown
MAT_SZ = 12.0     # MPa, across layers: 0.4 x in-plane, conservative (rev 6 used 20 for PETG)
MAT_RHO = 1.04    # g/cm3

# ---------- X layout ----------
CAR_X0, CAR_X1 = -14.0, 12.0     # carriage body relative to pin C
def s_of_theta(th):
    return geom(P, th)['C'][..., 0]
S_MIN, S_MAX = float(s_of_theta(TH_C)), float(s_of_theta(TH_O))
X_BLK0 = S_MAX + CAR_X1          # bearing block rear face = open hard stop
COLLAR_W, COLLAR_R = 7.0, 7.0    # 8 mm bore shaft collar, OD 14 x 7 wide (e.g. OpenBuilds T8 lock collar)
X_BRG0, X_BRG1 = X_BLK0 + 0.5 + COLLAR_W, X_BLK0 + 7.5 + COLLAR_W   # 608ZZ seat (7 wide); collar sits behind it
X_COL0 = X_BRG0 - COLLAR_W       # collar rear face (0.5 mm in front of the open-stop face)
X_BLK1 = X_BRG1 + 8.0          # 8 mm front wall: room for the cover-bolt inserts (2 mm walls)
X_WALL1 = S_MIN + CAR_X0 - 1.0   # motor wall front face
X_WALL0 = X_WALL1 - 8.0          # motor wall rear face = motor face
MOTOR_LEN = 40.0
X_MOT_REAR = X_WALL0 - MOTOR_LEN
X_AD1 = X_MOT_REAR - 1.0         # adapter front face
X_AD0 = X_AD1 - 14.0             # robot face
SCREW_TIP = X_BRG1              # screw end flush with the 608 front face; the 1 mm front recess gives +-0.5 mm cut tolerance before the tip could rub the lip
SCREW_LEN = SCREW_TIP - X_WALL0
Y_RAIL0, Y_RAIL1 = 24.5, 31.5   # adapter side walls >= 1.37 mm around the M6 counterbores
POST_C = O1 + 15.0*np.array([np.cos(np.radians(150)), np.sin(np.radians(150))])

def zc(p, z): return (float(p[0]), float(p[1]), float(z))

# ================= links (local frames) =================
def bc_plate(lower):
    """Bell crank plate. Local: origin O1, +x toward F1, D at (0,-r)."""
    pts = [((0, 0), R_BOSS), ((L, 0), R_BOSS), ((0, -r), R_BOSS)]
    z0, z1 = (Z_B0, Z_B1) if lower else (Z_U0, Z_U1)
    ops = [('add', ('ext', hull_circles(pts), z0, z1))]
    if lower:
        ops.append(('add', ('ext', circle_loop((0, 0), R_BOSS), z1 - 0.01, Z_U0)))  # spacer through M layer, flush with the bosses
        ops += [('cut', ('cyl', (0, 0, z0-1), (0, 0, Z_U0+1), R_RUN)),
                ('cut', ('cyl', (L, 0, z0-1), (L, 0, z1+1), R_INS)),
                ('cut', ('cyl', (0, -r, z0-1), (0, -r, z1+1), R_INS))]
    else:
        ops += [('cut', ('cyl', (0, 0, z0-1), (0, 0, z1+1), R_RUN)),
                ('cut', ('cyl', (L, 0, z0-1), (L, 0, z1+1), R_SNUG)),
                ('cut', ('cyl', (0, -r, z0-1), (0, -r, z1+1), R_SNUG))]
    return ops

def fc_plate(lower):
    """Front crank plate. Local: origin O2, +x toward F2."""
    z0, z1 = (Z_B0, Z_B1) if lower else (Z_U0, Z_U1)
    ops = [('add', ('ext', hull_circles([((0, 0), R_BOSS), ((L, 0), R_BOSS)]), z0, z1))]
    if lower:
        ops.append(('add', ('ext', circle_loop((0, 0), R_SPACER), z1 - 0.01, Z_U0)))
        ops += [('cut', ('cyl', (0, 0, z0-1), (0, 0, Z_U0+1), R_RUN)),
                ('cut', ('cyl', (L, 0, z0-1), (L, 0, z1+1), R_INS))]
    else:
        ops += [('cut', ('cyl', (0, 0, z0-1), (0, 0, z1+1), R_RUN)),
                ('cut', ('cyl', (L, 0, z0-1), (L, 0, z1+1), R_SNUG))]
    return ops

def conrod():
    """Local: origin C, +x toward D."""
    return [('add', ('ext', hull_circles([((0, 0), R_BOSS), ((l, 0), R_BOSS)]), Z_M0, Z_M1)),
            ('cut', ('cyl', (0, 0, Z_M0-1), (0, 0, Z_M1+1), R_RUN)),
            ('cut', ('cyl', (l, 0, Z_M0-1), (l, 0, Z_M1+1), R_RUN))]

# finger (upper side). Local: origin F1 (translation only).
F2L = V12
FACE_Y = -h
# JAW_X0: back edge moved forward so the finger clears the O2 spacer sweep (>= 1 mm) with one
# straight edge instead of clearance bites. JAW_X1: end of the serrated face.
JAW_X0, JAW_X1, TIP = 37.0, 70.0, (74.0, -40.0)
TOP_PT = (52.0, -12.0)
EXT_X0 = 41.0
TOOTH_P, TOOTH_D = 2.0, 0.8
def _jaw_profile(x_from):
    """Jaw outline from x_from forward: serrated face, tip, top edge back to x_from (loop of lines)."""
    pts = []
    n = int((JAW_X1 - x_from)//TOOTH_P)
    xs = x_from
    pts.append((x_from, FACE_Y))
    for k in range(n):
        pts.append((xs + TOOTH_P/2, FACE_Y + TOOTH_D)); pts.append((xs + TOOTH_P, FACE_Y)); xs += TOOTH_P
    pts.append((JAW_X1, FACE_Y)); pts.append(TIP); pts.append(TOP_PT)
    # top edge line from F1 top (0,5.5) to TOP_PT, evaluated at x_from
    y_top = 5.5 + (TOP_PT[1]-5.5)*x_from/TOP_PT[0]
    pts.append((x_from, y_top))
    return pts

TOP_C, TOP_R = (TOP_PT[0] - 0.9, TOP_PT[1] - 2.85), 3.0
TIP_C, TIP_R = (TIP[0] - 2.0, TIP[1] - 0.4), 2.0   # (v2, kept for reference)
NOSE_C, NOSE_R = (JAW_X1 + 1.0, FACE_Y + 3.0), 3.0  # rounded nose, tangent to the jaw face, front at x = 74
HEEL_C, HEEL_R = (JAW_X0, FACE_Y + 3.0), 3.0        # rounded heel where the back edge meets the face
def _serration_cut():
    """V-grooves cut into the jaw face: tips at FACE_Y, groove roots 0.8 mm deep, 2 mm pitch."""
    pts = [(JAW_X0 - 0.5, FACE_Y - 1.0), (JAW_X1 + 0.5, FACE_Y - 1.0), (JAW_X1 + 0.5, FACE_Y), (JAW_X1, FACE_Y)]
    x = JAW_X1
    while x - TOOTH_P >= JAW_X0 - 1e-6:
        pts.append((x - TOOTH_P/2, FACE_Y + TOOTH_D)); pts.append((x - TOOTH_P, FACE_Y)); x -= TOOTH_P
    pts.append((JAW_X0 - 0.5, FACE_Y))
    return poly_loop(pts)

def _body_edge_y(x):
    """y of the finger body's outer edge (tangent of the F1 boss and the TOP_C corner) at x."""
    c2 = np.array(TOP_C); dd = np.linalg.norm(c2); u = c2/dd; p = np.array([-u[1], u[0]])
    a = (R_BOSS - TOP_R)/dd; n = a*u + np.sqrt(1 - a*a)*p
    return (R_BOSS - n[0]*x)/n[1]
def finger():
    """Convex outline: F1 and F2 bosses, r3 top corner, r3 nose, r3 heel; serrated face; raised jaw block."""
    body = hull_circles([((0, 0), R_BOSS), (tuple(F2L), R_BOSS), (TOP_C, TOP_R), (NOSE_C, NOSE_R), (HEEL_C, HEEL_R)])
    jaw = hull_circles([((EXT_X0, FACE_Y), 0), (NOSE_C, NOSE_R), (TOP_C, TOP_R), ((EXT_X0, _body_edge_y(EXT_X0)), 0)])
    ops = [('add', ('ext', body, Z_M0, Z_M1)),
           ('add', ('ext', jaw, Z_M1 - 0.01, Z_JAW)),
           ('cut', ('ext', _serration_cut(), Z_M0 - 1, Z_JAW + 1)),
           ('cut', ('cyl', (0, 0, Z_M0-1), (0, 0, Z_JAW+1), R_RUN)),
           ('cut', ('cyl', (F2L[0], F2L[1], Z_M0-1), (F2L[0], F2L[1], Z_JAW+1), R_RUN))]
    return ops

# ================= carriage (local: origin at (C_x, 0, 0)) =================
NUT_FL_R, NUT_FL_T, NUT_BODY_R, NUT_LEN = 11.0, 3.5, 5.1, 15.0
POCKET_X0 = 5.8; POCKET_X1 = POCKET_X0 + NUT_FL_T + 0.2
def ear_loop():
    y0, y1, rr = 11.0, YC + R_BOSS, R_BOSS
    return dict(start=PT(CAR_X0, y0), segs=[('L', PT(CAR_X1, y0)), ('L', PT(CAR_X1, y1 - rr)),
            ('A', PT(CAR_X1 - rr + rr*np.cos(np.pi/4), y1 - rr + rr*np.sin(np.pi/4)), PT(CAR_X1 - rr, y1)),
            ('L', PT(CAR_X0 + rr, y1)),
            ('A', PT(CAR_X0 + rr - rr*np.cos(np.pi/4), y1 - rr + rr*np.sin(np.pi/4)), PT(CAR_X0, y1 - rr)),
            ('L', PT(CAR_X0, y0))])
NUT_SCREW_Y = 8.0   # flange holes used at 3 and 9 o'clock (D3.5 holes on PCD 16)
def carriage():
    """Prints rear face down (no supports). Nut goes in from the front: body into the bore, flange into the
    open front recess, held by 2x M3x8 button heads self-tapped into D2.5 pilots (axial retention + anti-rotation).
    Open-stop faces at x = CAR_X1: side strips, ears and tongue."""
    ops = [('add', ('ext', poly_loop([(CAR_X0, -13.0), (CAR_X1, -13.0), (CAR_X1, 13.0), (CAR_X0, 13.0)]), 0, CAR_TOP))]   # ext (not box): keeps the Onshape part identity
    for sgn in (1, -1):
        el = ear_loop() if sgn > 0 else mirror_loop(ear_loop())
        ops += [('add', ('ext', el, 0, Z_B1)), ('add', ('ext', el, Z_U0, Z_U1))]
    ops.append(('add', ('box', (CAR_X0, -5.8, -6.0), (CAR_X1, 5.8, 0.01))))          # tongue (runs in the base channel)
    ops += [('cut', ('cyl', (CAR_X0-1, 0, Z_S), (POCKET_X0+0.01, 0, Z_S), NUT_BODY_R + 0.3)),          # nut bore (float +-0.3)
            ('cut', ('box', (POCKET_X0, -NUT_FL_R-0.3, Z_S-NUT_FL_R-0.3), (CAR_X1+1, NUT_FL_R+0.3, CAR_TOP+1)))]  # flange recess
    for sgn in (1, -1):
        ops.append(('cut', ('cyl', (POCKET_X0-7.0, sgn*NUT_SCREW_Y, Z_S), (POCKET_X0+0.01, sgn*NUT_SCREW_Y, Z_S), 1.25)))
    for sgn in (1, -1):
        ops += [('cut', ('cyl', (0, sgn*YC, -1), (0, sgn*YC, Z_B1+0.01), R_INS)),
                ('cut', ('cyl', (0, sgn*YC, Z_U0-0.01), (0, sgn*YC, Z_U1+1), R_SNUG))]
    return ops

# ================= ground: base & cover =================
def plate_outline():
    pts = [((X_AD0 + 4, Y_RAIL1-4), 4.0), ((X_AD0 + 4, -(Y_RAIL1-4)), 4.0),
           (tuple(POST_C), 7.0), ((POST_C[0], -POST_C[1]), 7.0),
           (tuple(O1), 8.0), ((O1[0], -O1[1]), 8.0),
           (tuple(O2), 7.5), ((O2[0], -O2[1]), 7.5),
           ((X_BLK1 - 2, 12.0), 2.0), ((X_BLK1 - 2, -12.0), 2.0)]
    return hull_circles(pts)

MW_BOLT_Y = 26.0; MW_BOLT_X = (X_WALL0 + X_WALL1)/2
BLK_BOLT = (X_BRG1 + 3.5, 8.5)   # rev 6: inboard, so the block's front corners can be R6
BLK_HW = 13.5   # 2.47 mm wall round the 608
BLK_FRONT_R = 6.0   # rev 6: R6 front corners keep >= 1.3 mm from the front cranks at full close (block is 4.5 mm longer)
def block_loop():
    return hull_circles([((X_BLK0 + 2.0, BLK_HW - 2.0), 2.0), ((X_BLK0 + 2.0, -BLK_HW + 2.0), 2.0),
                         ((X_BLK1 - BLK_FRONT_R, BLK_HW - BLK_FRONT_R), BLK_FRONT_R), ((X_BLK1 - BLK_FRONT_R, -BLK_HW + BLK_FRONT_R), BLK_FRONT_R)])
MOTOR_HOLE = 15.5
AD_SCREW_Z = (4.0, 16.5)   # adapter side screws (base wall, cover wall): >= 4 mm from the M6 counterbores
def _common_ground(lower):
    z0, z1 = (Z_BB, 0.0) if lower else (Z_C0, Z_C1)
    ops = [('add', ('ext', plate_outline(), z0, z1))]
    # side walls beside the adapter block (base: up to Z_S, cover: down to Z_S), flush with the plate outline;
    # they carry the adapter side screws in the band that is clear of the M6 bolts and counterbores
    band, cutz, slotz = ((-0.01, Z_S), (0.0, Z_S + 1), (z0 - 1, Z_S + 1)) if lower else \
                        ((Z_S, Z_C0 + 0.01), (Z_S - 1, Z_C0), (Z_S - 1, z1 + 1))
    ops += [('add', ('ext', plate_outline(), band[0], band[1])),
            ('cut', ('box', (X_AD1, -100.0, cutz[0]), (X_BLK1 + 50.0, 100.0, cutz[1])))]
    # U-slot for the motor body (open at the rear; adapter block sits in it), through plate and side walls
    ops.append(('cut', ('ext', rrect_loop(X_AD0 - 10, -Y_RAIL0, X_WALL0, Y_RAIL0, 2.0), slotz[0], slotz[1])))
    # motor wall half, bearing block half
    if lower:
        ops += [('add', ('ext', rrect_loop(X_WALL0, -Y_RAIL1, X_WALL1, Y_RAIL1, 2.0), z0, Z_S)),
                ('add', ('ext', block_loop(), -0.01, Z_S))]
    else:
        ops += [('add', ('ext', rrect_loop(X_WALL0, -Y_RAIL1, X_WALL1, Y_RAIL1, 2.0), Z_S, z1)),
                ('add', ('ext', block_loop(), Z_S, Z_C0 + 0.01))]
    # posts (on base, rising to cover)
    if lower:
        for sgn in (1, -1):
            ops.append(('add', ('ext', circle_loop((POST_C[0], sgn*POST_C[1]), 5.0), -0.01, Z_C0)))
    # --- cuts ---
    ops += [('cut', ('cyl', (X_WALL0-1, 0, Z_S), (X_WALL0 + 2.5, 0, Z_S), 11.2)),          # motor pilot recess
            ('cut', ('cyl', (X_WALL0-1, 0, Z_S), (X_WALL1 + 1, 0, Z_S), 6.0)),            # screw clearance
            ('cut', ('cyl', (X_BRG0, 0, Z_S), (X_BRG1, 0, Z_S), 11.03)),                 # 608 seat
            ('cut', ('cyl', (X_BLK0-1, 0, Z_S), (X_BRG0+0.01, 0, Z_S), 8.0)),            # rear lip hole (thrust collar runs inside it)
            ('cut', ('cyl', (X_BRG1-0.01, 0, Z_S), (X_BRG1 + 1.0, 0, Z_S), 6.3))]        # front recess: clears the 608 inner ring and the screw end; the lip backs the outer ring (grip thrust)
    zm = Z_S - MOTOR_HOLE if lower else Z_S + MOTOR_HOLE
    for sgn in (1, -1):
        ops.append(('cut', ('cyl', (X_WALL0-1, sgn*MOTOR_HOLE, zm), (X_WALL1+1, sgn*MOTOR_HOLE, zm), R_M3)))
        # screw access slot in front of the wall, through the plate and the whole wall half (base and cover alike).
        # r0.5 corners leave a flat seat 6 mm wide for the D5.7 button head, 3.5 mm into the wall (M3x8 into the motor).
        ops.append(('cut', ('ext', rrect_loop(X_WALL1 - 3.5, sgn*MOTOR_HOLE - 3.5, X_WALL1 + 15, sgn*MOTOR_HOLE + 3.5, 0.5), slotz[0], slotz[1])))
    # dowel holes
    for c in (O1, O2):
        for sgn in (1, -1):
            if lower: ops.append(('cut', ('cyl', (c[0], sgn*c[1], -6.2), (c[0], sgn*c[1], 1.0), R_DOW_PRESS)))
            else: ops.append(('cut', ('cyl', (c[0], sgn*c[1], Z_C0-1), (c[0], sgn*c[1], 26.4), R_DOW_CLOSE)))
    # bolt holes: wall joint, block joint, posts
    bolts = [(MW_BOLT_X, MW_BOLT_Y), (MW_BOLT_X, -MW_BOLT_Y), (BLK_BOLT[0], BLK_BOLT[1]), (BLK_BOLT[0], -BLK_BOLT[1]),
             tuple(POST_C), (POST_C[0], -POST_C[1])]
    for (bx, by) in bolts:
        if lower:
            ztop = Z_C0 if (abs(by) > 40) else Z_S
            ops.append(('cut', ('cyl', (bx, by, ztop - 6.5), (bx, by, ztop + 1), R_INS)))
        else:
            ops.append(('cut', ('cyl', (bx, by, Z_S - 1 if abs(by) < 40 else Z_C0 - 1), (bx, by, Z_C1 + 1), R_M3)))
            ops.append(('cut', ('cyl', (bx, by, Z_C1 - 3.2), (bx, by, Z_C1 + 1), 3.1)))   # counterbore Ø6.2
    # carriage channel (base only) and adapter side-screw holes in rails
    if lower:
        ops.append(('cut', ('box', (X_WALL1, -6.0, -6.5), (X_BLK0, 6.0, 0.0))))
    zr = AD_SCREW_Z[0] if lower else AD_SCREW_Z[1]
    for sgn in (1, -1):
        ops.append(('cut', ('cyl', (X_AD0 + 7.0, sgn*(Y_RAIL1 + 4), zr), (X_AD0 + 7.0, sgn*(Y_RAIL0 - 1), zr), R_M3)))
        ops.append(('cut', ('cyl', (X_AD0 + 7.0, sgn*(Y_RAIL1 + 4), zr), (X_AD0 + 7.0, sgn*(Y_RAIL1 - 3.2), zr), 3.1)))
    return ops

def base(): return _common_ground(True)
def cover(): return _common_ground(False)

# ================= adapter (ISO 9409-1-50-4-M6) =================
AD_HW, AD_HZ = 24.3, 29.5   # 1.37 mm wall round the M6 counterbores; 1.45 mm skin over the pin hole
def adapter():
    ops = [('add', ('extx', rrect_loop(-AD_HW, Z_S - AD_HZ, AD_HW, Z_S + AD_HZ, 6.0), X_AD0, X_AD1)),
           ('add', ('cyl', (X_AD0 - 3.0, 0, Z_S), (X_AD0 + 0.01, 0, Z_S), 15.72))]   # spigot Ø31.44 (fits 31.5 H7)
    for a in (45, 135, 225, 315):
        y, z = 25*np.cos(np.radians(a)), Z_S + 25*np.sin(np.radians(a))
        ops += [('cut', ('cyl', (X_AD0 - 4, y, z), (X_AD1 + 1, y, z), 3.3)),
                ('cut', ('cyl', (X_AD0 + 6.0, y, z), (X_AD1 + 1, y, z), 5.25))]
    ops.append(('cut', ('cyl', (X_AD0 - 4, 0, Z_S + 25), (X_AD0 + 6, 0, Z_S + 25), 3.05)))   # Ø6 H7 pin hole (ream)
    for sgn in (1, -1):
        for zr in AD_SCREW_Z:
            ops.append(('cut', ('cyl', (X_AD0 + 7.0, sgn*(AD_HW + 1), zr), (X_AD0 + 7.0, sgn*(AD_HW - 6.5), zr), R_INS)))
    return ops

# ================= purchased parts (simplified) =================
def motor():
    return [('add', ('extx', chamfer_square_loop(0, Z_S, 21.15, 4.5), X_MOT_REAR, X_WALL0)),
            ('add', ('cyl', (X_WALL0 - 0.01, 0, Z_S), (X_WALL0 + 2.0, 0, Z_S), 11.0)),
            ('cut', ('cyl', (X_WALL0 - 5, 15.5, Z_S + 15.5), (X_WALL0 + 1, 15.5, Z_S + 15.5), 1.25)),
            ('cut', ('cyl', (X_WALL0 - 5, -15.5, Z_S + 15.5), (X_WALL0 + 1, -15.5, Z_S + 15.5), 1.25)),
            ('cut', ('cyl', (X_WALL0 - 5, 15.5, Z_S - 15.5), (X_WALL0 + 1, 15.5, Z_S - 15.5), 1.25)),
            ('cut', ('cyl', (X_WALL0 - 5, -15.5, Z_S - 15.5), (X_WALL0 + 1, -15.5, Z_S - 15.5), 1.25))]
def leadscrew():
    return [('add', ('cyl', (X_WALL0 + 2.0, 0, Z_S), (SCREW_TIP, 0, Z_S), 4.0))]
def nut():   # local carriage frame; flange in pocket at POCKET_X0+0.1
    fx = POCKET_X0 + 0.1
    return [('add', ('cyl', (fx, 0, Z_S), (fx + NUT_FL_T, 0, Z_S), NUT_FL_R)),
            ('add', ('cyl', (fx - (NUT_LEN - NUT_FL_T), 0, Z_S), (fx + 0.01, 0, Z_S), NUT_BODY_R)),
            ('cut', ('cyl', (fx - 20, 0, Z_S), (fx + 10, 0, Z_S), 4.0))] + \
           [('cut', ('cyl', (fx - 1, yy, Z_S + zz), (fx + NUT_FL_T + 1, yy, Z_S + zz), 1.75))
            for yy, zz in ((8.0, 0), (-8.0, 0), (0, 8.0), (0, -8.0))]
def collar():   # thrust collar on the screw, front face against the 608 inner ring (grip thrust -> 608 -> front lip)
    return [('add', ('cyl', (X_COL0, 0, Z_S), (X_BRG0, 0, Z_S), COLLAR_R)),
            ('cut', ('cyl', (X_COL0 - 1, 0, Z_S), (X_BRG0 + 1, 0, Z_S), 4.0))]
def bearing608():
    return [('add', ('cyl', (X_BRG0, 0, Z_S), (X_BRG1, 0, Z_S), 11.0)),
            ('cut', ('cyl', (X_BRG0 - 1, 0, Z_S), (X_BRG1 + 1, 0, Z_S), 4.0))]
def dowel(c, sgn):
    return [('add', ('cyl', (c[0], sgn*c[1], -6.0), (c[0], sgn*c[1], 26.0), 2.0))]   # ISO 8734 4 x 32
def shoulder_screw():   # local: axis at origin, shoulder seat at z=Z_B1
    S = 12.0
    return [('add', ('cyl', (0, 0, Z_B1 - 4.5), (0, 0, Z_B1 + 0.01), 1.5)),
            ('add', ('cyl', (0, 0, Z_B1), (0, 0, Z_B1 + S), 2.0)),
            ('add', ('cyl', (0, 0, Z_B1 + S), (0, 0, Z_B1 + S + SH_HEAD_H), SH_HEAD_R)),
            ('cut', ('ext', hex_loop(0, 0, 2.0), Z_B1 + S + 1.2, Z_B1 + S + SH_HEAD_H + 1))]

BH_DK, BH_K = 5.7, 1.65
def button_screw(seat, axis, length):
    """ISO 7380 M3 button head. seat = centre of the head's bearing face, axis = unit vector into the joint."""
    s, a = np.array(seat, float), np.array(axis, float)
    T = lambda v: tuple(float(c) for c in v)
    return [('add', ('cyl', T(s - a*BH_K), T(s), BH_DK/2)),
            ('add', ('cyl', T(s - a*0.01), T(s + a*length), 1.5)),
            ('cut', ('cyl', T(s - a*(BH_K + 0.01)), T(s - a*(BH_K - 1.0)), 1.15))]   # socket (round stand-in for the 2.0 hex)
# upper-side (+y) instances; each is mirrored to -y. Static ones in the assembly frame, the nut screw in the carriage frame.
FASTENERS = [  # name, seat, axis, length, frame
    ('BHS_Motor_Base',  (X_WALL1 - 3.5, MOTOR_HOLE, Z_S - MOTOR_HOLE), (-1, 0, 0), 8.0, 'ground'),
    ('BHS_Motor_Cover', (X_WALL1 - 3.5, MOTOR_HOLE, Z_S + MOTOR_HOLE), (-1, 0, 0), 8.0, 'ground'),
    ('BHS_Cover_Wall',  (MW_BOLT_X, MW_BOLT_Y, Z_C1 - 3.2), (0, 0, -1), 20.0, 'ground'),
    ('BHS_Cover_Block', (BLK_BOLT[0], BLK_BOLT[1], Z_C1 - 3.2), (0, 0, -1), 20.0, 'ground'),
    ('BHS_Cover_Post',  (POST_C[0], POST_C[1], Z_C1 - 3.2), (0, 0, -1), 8.0, 'ground'),
    ('BHS_Side_Base',   (X_AD0 + 7.0, Y_RAIL1 - 3.2, AD_SCREW_Z[0]), (0, -1, 0), 8.0, 'ground'),
    ('BHS_Side_Cover',  (X_AD0 + 7.0, Y_RAIL1 - 3.2, AD_SCREW_Z[1]), (0, -1, 0), 8.0, 'ground'),
    ('BHN_Nut',         (POCKET_X0 + 0.1 + NUT_FL_T, NUT_SCREW_Y, Z_S), (-1, 0, 0), 8.0, 'car'),
]

# ================= poses =================
def rotz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
def Tm(R=np.eye(3), t=(0, 0, 0)):
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; return M
MIR = np.diag([1, -1, 1, 1.0])   # Y mirror (applied to already-mirrored geometry, so we instead mirror ops)

def pose(th):
    """Return dict name -> (ops, 4x4 transform). Lower side = mirrored ops with mirrored transforms."""
    g = geom(P, th); F1 = g['F1']; D = g['D']; C = g['C']
    rod_ang = np.arctan2(D[1] - C[1], D[0] - C[0])
    parts = {}
    def add(name, ops, M):
        parts[name + '_U'] = (ops, M)
        Mm = MIR @ M @ MIR
        parts[name + '_L'] = (mirror_ops(ops), Mm)
    add('BellCrank_Lower', bc_plate(True), Tm(rotz(th), (O1[0], O1[1], 0)))
    add('BellCrank_Upper', bc_plate(False), Tm(rotz(th), (O1[0], O1[1], 0)))
    add('FrontCrank_Lower', fc_plate(True), Tm(rotz(th), (O2[0], O2[1], 0)))
    add('FrontCrank_Upper', fc_plate(False), Tm(rotz(th), (O2[0], O2[1], 0)))
    add('ConRod', conrod(), Tm(rotz(rod_ang), (C[0], C[1], 0)))
    add('Finger', finger(), Tm(np.eye(3), (F1[0], F1[1], 0)))
    for nm, pt in (('SS_F1', F1), ('SS_F2', g['F2']), ('SS_D', D), ('SS_C', C)):
        add(nm, shoulder_screw(), Tm(np.eye(3), (pt[0], pt[1], 0)))
    parts['Carriage'] = (carriage(), Tm(np.eye(3), (C[0], 0, 0)))
    parts['T8_Nut'] = (nut(), Tm(np.eye(3), (C[0], 0, 0)))
    for nm, ops in (('Base', base()), ('Cover', cover()), ('Adapter', adapter()), ('Motor', motor()),
                    ('LeadScrew', leadscrew()), ('Bearing608', bearing608()), ('LockCollar', collar())):
        parts[nm] = (ops, np.eye(4))
    for nm, seat, ax, ln, frame in FASTENERS:
        add(nm, button_screw(seat, ax, ln), Tm(np.eye(3), (C[0], 0, 0)) if frame == 'car' else np.eye(4))
    for c, nm in ((O1, 'O1'), (O2, 'O2')):
        parts['Dowel_' + nm + '_U'] = (dowel(c, 1), np.eye(4)); parts['Dowel_' + nm + '_L'] = (dowel(c, -1), np.eye(4))
    return parts

MOVING = lambda n: any(n.startswith(k) for k in ('BellCrank', 'FrontCrank', 'ConRod', 'Finger', 'SS_', 'Carriage', 'T8_Nut', 'BHN_'))
PRINTED = ['Base', 'Cover', 'Adapter', 'Carriage', 'BellCrank_Lower_U', 'BellCrank_Upper_U', 'FrontCrank_Lower_U',
           'FrontCrank_Upper_U', 'ConRod_U', 'Finger_U', 'Finger_L']
if __name__ == '__main__':
    print('theta open %.2f deg; S %.2f..%.2f; blk %.2f..%.2f; wall %.2f..%.2f; adapter %.2f..%.2f; screw len %.1f'
          % (np.degrees(TH_O), S_MIN, S_MAX, X_BLK0, X_BLK1, X_WALL0, X_WALL1, X_AD0, X_AD1, SCREW_LEN))
    print('POST', POST_C, 'O2', O2)
