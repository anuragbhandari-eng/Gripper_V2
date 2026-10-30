"""Gripper geometry: every part as CSG ops in its LOCAL frame + pose transforms. Single source of truth.
Assembly frame: X forward (screw axis direction), Y outward (upper side = +Y), Z up from base-plate top.
Origin: X at fixed pivot O1, Y on centerline, Z=0 at base-plate top."""
import os
import numpy as np
from params import make
from kin import geom
from prims import *

P = make(28.0)
L, r, l, YC, h = P['L'], P['r'], P['l'], P['YC'], P['h']
O1 = np.array([0.0, P['YO1']]); V12 = geom(P, 0.0)['O2'] - O1; O2 = O1 + V12
# rev 7.2 (finishing pass): open hard stop at 60.5 mm, just past the 60 mm firmware cap (was 66). The last 6 mm were
# never used, and there the linkage's advantage (and every pin load in the 200 N limit case) climbs steeply.
TH_C = P['th_c']; GAP_MAX = 60.5
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
R_DOW_CLOSE = 2.0   # (rev 6: cover dowel hole, print Ø4.0 and ream; replaced in rev 7.1 by the bonded sleeve below)
# rev 7.1 (design review item 3): the dowel top is held by a 4 x 6 x 6 bronze sleeve bonded with epoxy into an
# oversize cover hole while the cover sits on the dowels, so it is supported at both ends with zero clearance no
# matter how the printed parts shrink; wax on the dowel tops lets the cover come off again.
DOW_Z = (-9.0, 29.5)                 # rev 7.2b: hardened 4 x 40 cut to 38.5, pressed through the base: flush with the base
                                     # underside and the cover top, 9 mm of press fit (was 6.5)
SLV_RI, SLV_RO, SLV_L, R_SLV_HOLE = 2.0, 3.0, 6.0, 3.2   # sleeve ID/OD radii, length; cover hole (0.2 mm epoxy gap)
R_M3 = 1.7      # Ø3.4 clearance
R_BOSS = 5.5    # link end boss
R_SPACER = 5.0  # crank spacer boss in M layer
SH_HEAD_R, SH_HEAD_H = 3.5, 3.0   # shoulder screw head Ø7 x 3
LEAD, USTEP = 8.0, 16              # rev 7 (v2 change A): Tr8x8 (4-start, 8 mm lead; rev 6 Tr8x2); 1/16 microstepping
STEPS_PER_MM = 200*USTEP/LEAD      # 400 (rev 6: 1600)
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
MOTOR_LEN = 40.0                  # layout length (adapter sits 1 mm behind it)
MOTOR_BODY = 38.7                 # the bought motor (YEJMKJ N17-Y42-39-SG240) is 1.3 mm shorter: 2.3 mm gap to the adapter
X_MOT_REAR = X_WALL0 - MOTOR_LEN
X_AD1 = X_MOT_REAR - 1.0         # adapter front face
X_AD0 = X_AD1 - 14.0             # robot face
# rev 7 (v2 change C): AS5600 encoder at the screw's front end. The screw is cut 3 mm shorter, so a printed puck holding
# a 6 x 2.5 diametric magnet fills the end of the 608 bore (magnet face flush with the 608 front face). The board stands
# across the block front, chip facing the magnet, in a slot split between base and cover (like the 608 cradle).
ENC_CUT = 3.0                     # screw end this far inside the 608 bore (cut -0.5/+0: never long)
SCREW_TIP = X_BRG1 - ENC_CUT
MAG_D, MAG_T = 6.0, 2.5
ENC_GAP, ENC_CHIP_T, ENC_PCB_T, ENC_PCB_W = 0.8, 1.75, 1.6, 23.0   # magnet face to chip face (AS5600: 0.5-3 mm); SOIC-8; board
X_CHIP = X_BRG1 - 0.1 + ENC_GAP   # chip face (magnet face sits 0.1 inside the 608 face)
X_PCB0 = X_CHIP + ENC_CHIP_T      # board back face (chip side) on the ledge in front of the lip
X_SLOT0, X_SLOT1 = X_PCB0, X_PCB0 + ENC_PCB_T + 0.2
ENC_SLOT_H = ENC_PCB_W/2 + 0.2    # slot half-size (y and z)
ENC_WIN_R = 8.5                   # window through the lip for the chip; the lip still backs the whole 608 outer ring
ENC_RELIEF = 9.8                  # square relief, 1 mm deep, for parts on the chip side of the board
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
# ---------- rev 7: bolt-on tip blocks (v2 change B) ----------
# The finger splits at the raised-jaw edge (x = 41); the F2 boss and the O2-spacer clearance sit behind the seam.
# Two tip sets bolt onto the same finger body: narrow (pad face on the rev 6 face line, gap 0-60.5) and wide (pad face
# 10 mm further out per side, gap 20-80.5). Both run 12 mm further forward than rev 6. The pad is the same for both.
TIP_WIDE = os.environ.get('GRIPPER_TIPSET', 'narrow') == 'wide'   # which set the local checks place
SEAM_X = EXT_X0
TIP_EXT, WIDE_OFS, PAD_T, TIP_R = 12.0, 10.0, 2.0, 3.0
FACE_X1 = NOSE_C[0] + TIP_EXT                 # 83: end of the contact face (nose tangent)
SEAM_Y0 = FACE_Y + WIDE_OFS + 1.5             # finger edge at the seam: 1.5 mm behind the wide pad face
EDGE_S = _body_edge_y(1.0) - _body_edge_y(0.0)   # slope of the finger's outer edge
# Rev 7.1 (design review items 1-2): the tip block and pad are centred on the pin plane z = Z_S, so a normal grip puts
# no twist on the finger; the tongue rises from the finger body to the block top (13.55 mm) and runs 2.8 mm under the
# outer edge, so its root section is about 16 x 13.5 mm (the rev 7.0 tongue was 9 x 7.6 mm and was overstressed).
TIP_Z = (Z_S - 9.75, Z_S + 9.75)               # tip block and pad height (19.5 mm, as rev 6)
TONGUE_X1, TONGUE_Y0, TONGUE_INSET = SEAM_X + 15.0, -27.3, 2.8   # tongue front, face-side edge, gap under the outer edge
TIP_SCREW_X = (45.5, 52.5)                      # 2x M3x10 from below into inserts at the tongue's mid-depth (neutral axis)
PAD_X = (SEAM_X + TIP_R + 0.5, FACE_X1 - 0.5)   # pad length: heel tangent to nose tangent, 0.5 mm in at each end
PAD_ZC, PAD_KEY = Z_S, (5.0, 8.0, 1.5)          # pad dovetail: mouth width, root width, depth (45 deg flanks)
PAD_MAT, PAD_RHO = 'TPU', 1.21                   # TPU 95A, g/cm3

def tip_face_y(wide):
    """Rigid contact face of a tip block (finger frame); the 2 mm pad sits in front of it."""
    return FACE_Y + PAD_T + (WIDE_OFS if wide else 0.0)

PAD_SNAP = (1.1, 1.05, 3.0)   # rev 7.1 (review item 4): groove entrance depth, key depth, barb length at the key's rear
def _pad_key_loop(yf, s, depth=None):
    """Dovetail section in (y, z) at the face yf, opening into the block; s = gap to the groove (0 for the groove);
    depth cuts it shallower along the same 45 deg flanks."""
    wm, wb, d = PAD_KEY
    y0, y1 = yf - 0.01, yf + (d if depth is None else depth) - 2*s
    k = 1.0/np.cos(np.arctan((wb - wm)/2/d))          # flank gap s measured square to the slanted flank
    hw = lambda y: (wm + (wb - wm)*(y - y0)/(d + 0.01))/2 - k*s
    return poly_loop([(y0, PAD_ZC - hw(y0)), (y1, PAD_ZC - hw(y1)), (y1, PAD_ZC + hw(y1)), (y0, PAD_ZC + hw(y0))])

def tongue_top(x):   # tongue edge under the outer edge (parallel to it)
    return _body_edge_y(x) - TONGUE_INSET
def tip_screw_y(x):  # tip screws sit at the tongue's mid-depth
    return (tongue_top(x) + TONGUE_Y0)/2
def _tongue_loop(c=0.0, x0=SEAM_X - 0.5):
    """Tongue outline (c = 0) or its pocket in the tip block (c = slide gap). Tongue front corners chamfered 0.6 so
    they clear the printed pocket corners."""
    k = c*np.hypot(1, EDGE_S); x1 = TONGUE_X1 + c; y0 = TONGUE_Y0 - c
    if c > 0:
        return poly_loop([(x0, y0), (x1, y0), (x1, tongue_top(x1) + k), (x0, tongue_top(x0) + k)])
    return poly_loop([(x0, y0), (x1 - 0.6, y0), (x1, y0 + 0.6), (x1, tongue_top(x1) - 0.6), (x1 - 0.6, tongue_top(x1 - 0.6)), (x0, tongue_top(x0))])

def finger():
    """Finger body (rev 7): F1 and F2 bosses back to the seam at x = 41, plus the tongue that carries a tip block.
    The heel is trimmed to 1.5 mm behind the wide pad face, so the back edge now runs F1 boss -> F2 boss, further
    from the O2 spacer than rev 6. The tongue rises from the M layer to the tip-block top: the finger still prints
    flat (nothing overhangs). Inserts for the tip screws are pressed into the tongue's underside."""
    body = hull_circles([((0, 0), R_BOSS), (tuple(F2L), R_BOSS), ((SEAM_X, SEAM_Y0), 0), ((SEAM_X, _body_edge_y(SEAM_X)), 0)])
    ops = [('add', ('ext', body, Z_M0, Z_M1)),
           ('add', ('ext', _tongue_loop(), Z_M0, TIP_Z[1])),
           ('cut', ('cyl', (0, 0, Z_M0-1), (0, 0, Z_M1+1), R_RUN)),
           ('cut', ('cyl', (F2L[0], F2L[1], Z_M0-1), (F2L[0], F2L[1], Z_M1+1), R_RUN))]
    ops += [('cut', ('cyl', (x, tip_screw_y(x), Z_M0 - 1), (x, tip_screw_y(x), Z_M0 + 6.5), R_INS)) for x in TIP_SCREW_X]
    return ops

def tip_block(wide):
    """Bolt-on tip block (finger frame), z TIP_Z, centred on the pin plane. Slides up onto the finger's tongue (the
    pocket is open at the top and the rear, with a floor under the tongue); 2x M3x10 from below through the floor into
    the tongue inserts. Narrow: rev 6 nose moved 12 mm forward. Wide: blunt end about 8 mm thick, top edge continuing
    the finger's outer edge. Pad dovetail groove along the face, open at the rear (x = 41). Prints flat, floor down."""
    yf = tip_face_y(wide); yh = yf + TIP_R
    if wide:
        front = [((FACE_X1, yh), TIP_R), ((FACE_X1, _body_edge_y(FACE_X1) - TIP_R*np.hypot(1, EDGE_S)), TIP_R)]
    else:
        front = [((FACE_X1, yh), TIP_R), ((TOP_C[0] + TIP_EXT, TOP_C[1] + TIP_EXT*EDGE_S), TOP_R)]
    outline = hull_circles([((SEAM_X + TIP_R, yh), TIP_R)] + front + [((SEAM_X, _body_edge_y(SEAM_X)), 0)])
    c = 0.15   # slide fit round the tongue
    ops = [('add', ('ext', outline, TIP_Z[0], TIP_Z[1])),
           ('cut', ('ext', _tongue_loop(c, SEAM_X - 2), Z_M0, TIP_Z[1] + 1)),
           ('cut', ('extx', _pad_key_loop(yf, 0.0, PAD_SNAP[0]), SEAM_X - 1, PAD_X[0] - 0.1)),   # shallow entrance
           ('cut', ('extx', _pad_key_loop(yf, 0.0), PAD_X[0] - 0.1, PAD_X[1] - 2.0))]               # full-depth groove
    for x in TIP_SCREW_X:
        y = tip_screw_y(x)
        ops += [('cut', ('cyl', (x, y, TIP_Z[0] - 1), (x, y, Z_M0 + 0.01), R_M3)),
                ('cut', ('cyl', (x, y, TIP_Z[0] - 1), (x, y, TIP_Z[0] + 1.8), 3.1))]
    return ops

def pad(wide):
    """TPU 95A contact pad, 2 mm thick, full jaw height; its dovetail key slides into the tip block's groove from the
    rear before the tip block goes on. A full-depth barb on the key's rear end squeezes through the groove's shallow
    entrance and then catches on its step, so the pad can't slide back out. The same pad fits both sets."""
    yf = tip_face_y(wide); xb = PAD_X[0] + PAD_SNAP[2]
    return [('add', ('box', (PAD_X[0], yf - PAD_T, TIP_Z[0]), (PAD_X[1], yf, TIP_Z[1]))),
            ('add', ('extx', _pad_key_loop(yf, 0.05), PAD_X[0], xb)),                          # barb
            ('add', ('extx', _pad_key_loop(yf, 0.05, PAD_SNAP[1] + 0.1), xb - 0.01, PAD_X[1] - 2.5))]

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
    # rev 7.2: 0.4 mm relief round the tongue's rear end, the bed side: elephant's foot there would bind in the channel
    ops += [('cut', ('box', (CAR_X0 - 1, 5.4, -6.5), (CAR_X0 + 0.4, 6.5, -0.2))),
            ('cut', ('box', (CAR_X0 - 1, -6.5, -6.5), (CAR_X0 + 0.4, -5.4, -0.2))),
            ('cut', ('box', (CAR_X0 - 1, -6.5, -6.5), (CAR_X0 + 0.4, 6.5, -5.6)))]
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
BLK_BOLT = (X_BLK0 + 5.0, 16.0)   # rev 7: on ears at the rear of the block (rev 6 had them at the front, where the encoder board now sits)
BLK_EAR_R = 4.0                    # ear 1 mm in front of the open-stop face, >= 2.3 mm from the O2 crank bosses
LOC_PIN = (X_BLK0 + 2.45, 11.0, 8.0)   # rev 7.1 (review item 12): 2x Ø3 x 16 dowels register the base and cover halves of
                                       # the bearing block (split 608 seat); pressed into the base half, slip in the cover
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
    for sgn in (1, -1):   # rev 7: block-bolt ears
        ear = hull_circles([((BLK_BOLT[0], sgn*BLK_BOLT[1]), BLK_EAR_R), ((BLK_BOLT[0], sgn*(BLK_HW - BLK_EAR_R)), BLK_EAR_R)])
        ops.append(('add', ('ext', ear, -0.01, Z_S) if lower else ('ext', ear, Z_S, Z_C0 + 0.01)))
    for sgn in (1, -1):   # rev 7.1: locating pins across the block split (press in the base, slip in the cover)
        px, py, ph = LOC_PIN
        ops.append(('cut', ('cyl', (px, sgn*py, Z_S - ph - 0.3), (px, sgn*py, Z_S + 0.01), 1.45)) if lower else
                   ('cut', ('cyl', (px, sgn*py, Z_S - 0.01), (px, sgn*py, Z_S + ph + 0.3), 1.55)))
    # posts (on base, rising to cover)
    if lower:
        for sgn in (1, -1):
            ops.append(('add', ('ext', circle_loop((POST_C[0], sgn*POST_C[1]), 5.0), -0.01, Z_C0)))
    # --- cuts ---
    ops += [('cut', ('cyl', (X_WALL0-1, 0, Z_S), (X_WALL0 + 2.5, 0, Z_S), 11.2)),          # motor pilot recess
            ('cut', ('cyl', (X_WALL0-1, 0, Z_S), (X_WALL1 + 1, 0, Z_S), 6.0)),            # screw clearance
            ('cut', ('cyl', (X_BRG0, 0, Z_S), (X_BRG1, 0, Z_S), 11.03)),                 # 608 seat
            ('cut', ('cyl', (X_BLK0-1, 0, Z_S), (X_BRG0+0.01, 0, Z_S), 8.0)),            # rear lip hole (thrust collar runs inside it)
            ('cut', ('cyl', (X_BRG1-0.01, 0, Z_S), (X_PCB0 - 1.0, 0, Z_S), ENC_WIN_R)),   # rev 7: chip window; the lip still backs the 608 outer ring (grip thrust)
            ('cut', ('box', (X_PCB0 - 1.0, -ENC_RELIEF, Z_S - ENC_RELIEF), (X_PCB0 + 0.01, ENC_RELIEF, Z_S + ENC_RELIEF))),   # relief for chip-side parts
            ('cut', ('box', (X_SLOT0, -ENC_SLOT_H, Z_S - ENC_SLOT_H), (X_SLOT1, ENC_SLOT_H, Z_S + ENC_SLOT_H)))]   # AS5600 board slot
    if not lower:   # encoder wires leave straight up through the cover, next to the controller
        ops.append(('cut', ('box', (X_SLOT0 - 0.3, -5.0, Z_S), (X_SLOT1 + 0.3, 5.0, Z_C1 + 1))))
        for hx, hy in CTRL_HOLES:   # rev 7: inserts for the controller spacers, pressed into the cover top
            ops.append(('cut', ('cyl', (hx, hy, Z_C1 - 6.5), (hx, hy, Z_C1 + 1), R_INS)))
        for hx, hy in LID_HOLES:    # rev 7.2: inserts for the electronics cover screws
            for sgn in (1, -1):
                ops.append(('cut', ('cyl', (hx, sgn*hy, Z_C1 - 6.5), (hx, sgn*hy, Z_C1 + 1), R_INS)))
    zm = Z_S - MOTOR_HOLE if lower else Z_S + MOTOR_HOLE
    for sgn in (1, -1):
        ops.append(('cut', ('cyl', (X_WALL0-1, sgn*MOTOR_HOLE, zm), (X_WALL1+1, sgn*MOTOR_HOLE, zm), R_M3)))
        # screw access slot in front of the wall, through the plate and the whole wall half (base and cover alike).
        # r0.5 corners leave a flat seat 6 mm wide for the D5.7 button head, 3.5 mm into the wall (M3x8 into the motor).
        ops.append(('cut', ('ext', rrect_loop(X_WALL1 - 3.5, sgn*MOTOR_HOLE - 3.5, X_WALL1 + 15, sgn*MOTOR_HOLE + 3.5, 0.5), slotz[0], slotz[1])))
    # dowel holes
    for c in (O1, O2):
        for sgn in (1, -1):
            if lower: ops.append(('cut', ('cyl', (c[0], sgn*c[1], DOW_Z[0] - 0.2), (c[0], sgn*c[1], 1.0), R_DOW_PRESS)))
            else: ops.append(('cut', ('cyl', (c[0], sgn*c[1], Z_C0-1), (c[0], sgn*c[1], Z_C1 + 1), R_SLV_HOLE)))   # sleeve bonded in
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
    return [('add', ('extx', chamfer_square_loop(0, Z_S, 21.15, 4.5), X_WALL0 - MOTOR_BODY, X_WALL0)),
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
def enc_puck():
    """Printed magnet puck (rev 7): slides into the 608 bore in front of the screw end and is glued to it (turns with
    the screw); the magnet sits in its front pocket, 0.1 mm inside the 608 face."""
    xm = X_BRG1 - 0.1
    return [('add', ('cyl', (SCREW_TIP, 0, Z_S), (xm, 0, Z_S), 3.95)),
            ('cut', ('cyl', (xm - MAG_T, 0, Z_S), (xm + 1, 0, Z_S), MAG_D/2 + 0.05))]
def magnet():   # 6 x 2.5 diametric NdFeB, glued into the puck
    xm = X_BRG1 - 0.1
    return [('add', ('cyl', (xm - MAG_T, 0, Z_S), (xm, 0, Z_S), MAG_D/2))]
def as5600():   # AS5600 module, simplified: 23 x 23 board, SOIC-8 chip facing the magnet
    h = ENC_PCB_W/2
    return [('add', ('box', (X_PCB0, -h, Z_S - h), (X_PCB0 + ENC_PCB_T, h, Z_S + h))),
            ('add', ('box', (X_CHIP, -2.5, Z_S - 3.0), (X_PCB0 + 0.01, 2.5, Z_S + 3.0)))]
def dowel(c, sgn):
    return [('add', ('cyl', (c[0], sgn*c[1], DOW_Z[0]), (c[0], sgn*c[1], DOW_Z[1]), 2.0))]   # hardened 4 x 40 cut to 38.5
def loc_pin():   # Ø3 x 16 locating pin across the bearing-block split, +y side: an M3 x 16 screw with its head cut off
    px, py, ph = LOC_PIN
    return [('add', ('cyl', (px, py, Z_S - ph), (px, py, Z_S + ph), 1.5))]
def sleeve(c):   # bronze sleeve 4 x 6 x 6 on the dowel top, bonded into the cover (local: +y side)
    return [('add', ('cyl', (c[0], c[1], Z_C0), (c[0], c[1], Z_C0 + SLV_L), SLV_RO)),
            ('cut', ('cyl', (c[0], c[1], Z_C0 - 1), (c[0], c[1], Z_C0 + SLV_L + 1), SLV_RI))]
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
# ================= rev 7: controller on the cover top (v2 change D) =================
# Pico + TMC2209 (both in header sockets), 7805 + 1N5817 for the Pico, motor-power divider, 100 uF at VM and the USB-C
# PD trigger board on one 50 x 70 mm protoboard (drill its corners to 3.2 mm on a 44 x 64 mm pattern). It sits on 4
# printed 10 mm spacers, held by 4 M3 x 16 through the board into heat-set inserts in the cover top; the encoder wires
# come up through the slit just in front of it. Cables are zip-tied to the board's grid holes for strain relief.
# rev 7.2b (compact): the 50 x 70 protoboard is cut to 48 x 60, the 7805 and the 100 uF lie flat, and the board sits on
# 4 mm spacers (room for the solder joints underneath). The driver's heatsink is now the tallest part.
CTRL_C, CTRL_SIZE, CTRL_HOLE = (0.0, 0.0), (48.0, 60.0), (21.0, 27.0)   # board centre (x, y), size, hole offsets
CTRL_HOLE_X = (CTRL_C[0] - 12.5, CTRL_C[0] + CTRL_HOLE[0])   # the rear pair sits between the Pico's socket rows (screw it before plugging the Pico in)
CTRL_HOLES = [(hx, CTRL_C[1] + sy*CTRL_HOLE[1]) for hx in CTRL_HOLE_X for sy in (-1, 1)]
Z_PCB = Z_C1 + 4.0                                   # board underside (4 mm printed spacers)
def protoboard():
    (cx, cy), (w, l) = CTRL_C, CTRL_SIZE
    return [('add', ('box', (cx - w/2, cy - l/2, Z_PCB), (cx + w/2, cy + l/2, Z_PCB + 1.6)))] + \
           [('cut', ('cyl', (hx, hy, Z_PCB - 1), (hx, hy, Z_PCB + 3), 1.6)) for hx, hy in CTRL_HOLES]
def spacer(x):   # printed spacer (Controller spacer rear+front U+L x4) between the cover top and the board, +y side
    y = CTRL_C[1] + CTRL_HOLE[1]
    return [('add', ('cyl', (x, y, Z_C1), (x, y, Z_PCB), 2.75)),
            ('cut', ('cyl', (x, y, Z_C1 - 1), (x, y, Z_PCB + 1), 1.7))]
def ctrl_spacer():   # the same spacer at the origin, for printing
    return [('add', ('cyl', (0, 0, 0), (0, 0, Z_PCB - Z_C1), 2.75)), ('cut', ('cyl', (0, 0, -1), (0, 0, Z_PCB - Z_C1 + 1), 1.7))]
# rev 7.2 (finishing pass): printed electronics cover over the controller, held by 2 M3 x 8 into 2 inserts in the cover
# top. Notches at the rim let the motor, encoder and two USB-C cables in, a window over the Pico's USB end leaves the
# BOOTSEL button reachable, and slots over the driver let its heat out. Prints top face down, no supports.
LID = (-27.0, 27.0, 33.0, 2.0, Z_PCB + 1.6 + 18.6)    # x0, x1, half-width, wall, inner top (1 mm over the driver heatsink)
LID_HOLES = [(-10.0, 37.5)]                           # +y side (mirrored): flange screw into a cover-top insert
def elec_cover():
    x0, x1, hw, w, zi = LID; hx, hy = LID_HOLES[0]
    ops = [('add', ('ext', rrect_loop(x0, -hw, x1, hw, 4.0), Z_C1, zi + w)),
           ('cut', ('ext', rrect_loop(x0 + w, -hw + w, x1 - w, hw - w, 2.0), Z_C1 - 1, zi)),
           ('add', ('box', (hx - 6.0, hw - w, Z_C1), (hx + 6.0, hy + 4.0, Z_C1 + 4.0))),                  # screw flanges
           ('add', ('box', (hx - 6.0, -hy - 4.0, Z_C1), (hx + 6.0, -hw + w, Z_C1 + 4.0))),
           ('cut', ('cyl', (hx, hy, Z_C1 - 1), (hx, hy, Z_C1 + 5), R_M3)),
           ('cut', ('cyl', (hx, -hy, Z_C1 - 1), (hx, -hy, Z_C1 + 5), R_M3)),
           ('cut', ('box', (x0 - 1, -8.0, Z_C1 - 1), (x0 + w + 1, 8.0, Z_C1 + 5.0))),                     # motor cable
           ('cut', ('box', (x1 - w - 1, -6.0, Z_C1 - 1), (x1 + 1, 6.0, Z_C1 + 5.0))),                     # encoder wires
           ('cut', ('box', (1.0, -hw - 1, Z_C1 - 1), (13.0, -hw + w + 1, Z_PCB + 1.6 + 8.0))),           # USB-C to the trigger
           ('cut', ('box', (-19.0, -hw - 1, Z_C1 - 1), (-6.0, -hw + w + 1, Z_PCB + 1.6 + SOCK_H + 7.0))), # USB-C to the Pico
           ('cut', ('box', (-23.5, -24.0, zi - 1), (-2.5, -6.0, zi + w + 1)))]                           # BOOTSEL window
    for xs in (6.0, 10.5, 15.0):                                                                        # driver vents
        ops.append(('cut', ('box', (xs, 5.0, zi - 1), (xs + 2.0, 21.0, zi + w + 1))))
    return ops
LID_SCREWS = [('BHL_Lid', (LID_HOLES[0][0], LID_HOLES[0][1], Z_C1 + 4.0), (0, 0, -1), 8.0)]
# M3 x 10 button heads through the board and spacer into the cover inserts (+y side, mirrored): 4.4 mm into the insert
CTRL_SCREWS = [(nm, (x, CTRL_C[1] + CTRL_HOLE[1], Z_PCB + 1.6), (0, 0, -1), 10.0)
               for nm, x in (('BHC_Ctrl_R', CTRL_HOLE_X[0]), ('BHC_Ctrl_F', CTRL_HOLE_X[1]))]
def _strip(xc, y0, y1, z0, h):   # header strip (plastic body), one row along y
    return ('add', ('box', (xc - 1.27, y0, z0), (xc + 1.27, y1, z0 + h + 0.01)))   # sits on the board, overlaps the module
SOCK_H = 8.5 + 2.5   # female header socket on the protoboard + the module's own male-header spacer (rev 7.2: socketed)
PICO_X = (CTRL_C[0] - 23.0, CTRL_C[0] - 2.0)
TMC_XY = (CTRL_C[0] + 4.0, 3.0)
def pico():   # Pico-compatible board (USB-C) plugged into 2x 20-pin sockets, long axis along y, USB at the -y end
    zb = Z_PCB + 1.6; z0, (x0, x1) = zb + SOCK_H, PICO_X; xc = (x0 + x1)/2
    return [('add', ('box', (x0, -25.5, z0), (x1, 25.5, z0 + 1.0))),
            ('add', ('box', (xc - 4.5, -26.8, z0 + 1.0), (xc + 4.5, -19.5, z0 + 4.2)))]
def pico_headers():   # its 2 header rows: female sockets soldered to the protoboard + the Pico's male-header spacers
    zb = Z_PCB + 1.6; xc = sum(PICO_X)/2
    return [_strip(xc - 8.89, -25.4, 25.4, zb, SOCK_H - 0.01), _strip(xc + 8.89, -25.4, 25.4, zb, SOCK_H - 0.01)]   # rows 17.78 apart
def tmc2209():   # StepStick-size TMC2209 module (BTT V1.3) plugged into 2x 8-pin sockets, with its heatsink
    zb = Z_PCB + 1.6; z0, (x0, y0) = zb + SOCK_H, TMC_XY
    return [('add', ('box', (x0, y0, z0), (x0 + 15.24, y0 + 20.32, z0 + 1.6))),
            ('add', ('box', (x0 + 3.1, y0 + 5.2, z0 + 1.6), (x0 + 12.1, y0 + 14.2, z0 + 6.6)))]
def tmc_headers():
    zb = Z_PCB + 1.6; (x0, y0) = TMC_XY; xc = x0 + 7.62
    return [_strip(xc - 6.35, y0, y0 + 20.32, zb, SOCK_H - 0.01), _strip(xc + 6.35, y0, y0 + 20.32, zb, SOCK_H - 0.01)]   # rows 12.7 apart
def regulator():   # L7805 in TO-220 lying flat (legs bent down at 90 deg), tab toward the -y edge: 9 V -> 5 V -> VSYS
    zb = Z_PCB + 1.6; x0, y0 = 13.8, CTRL_C[1] - CTRL_SIZE[1]/2 + 6.6   # 10.2 wide (x); tab 6.4 + body 9.2 long (y); clear of the corner screw
    return [('add', ('box', (x0, y0 + 6.4, zb + 1.0), (x0 + 10.2, y0 + 15.6, zb + 5.5))),           # body
            ('add', ('box', (x0, y0, zb + 1.0), (x0 + 10.2, y0 + 6.41, zb + 2.3))),                  # tab
            ('add', ('box', (x0 + 2.0, y0 + 15.59, zb), (x0 + 8.2, y0 + 17.5, zb + 2.0))),          # legs, bent down
            ('cut', ('cyl', (x0 + 5.1, y0 + 3.2, zb), (x0 + 5.1, y0 + 3.2, zb + 3.0), 1.8))]
def cap100():   # 100 uF 35 V electrolytic across VM and GND, standing next to the driver (12 mm, below its heatsink)
    zb = Z_PCB + 1.6
    return [('add', ('cyl', (19.0, -1.4, zb), (19.0, -1.4, zb + 12.0), 4.0))]
def pd_trigger():   # USB-C PD trigger board set to 9 V, taped flat to the board, its socket just past the -y edge
    zb = Z_PCB + 1.6; ye = CTRL_C[1] - CTRL_SIZE[1]/2
    return [('add', ('box', (1.0, ye, zb + 1.0), (13.0, ye + 26.0, zb + 2.2))),
            ('add', ('box', (2.5, ye - 1.5, zb + 2.19), (11.5, ye + 5.9, zb + 5.5)))]

# ================= rev 7: bench stand (v2 change F) =================
# The gripper hangs jaws-down from a 2020 aluminium extrusion. A printed head bracket takes the ISO 9409 adapter (its
# 4 M6 screws, M6 x 20 here, run into M6 nuts dropped into the bracket from the back) and clamps the column with 2x M5
# into T-nuts; the column stands in a printed base. The power bank sits on the desk beside the base. Gripper frame: +x points down, the
# table is the plane x = X_TABLE.
COL_A, COL_Z, COL_LEN = 20.0, -44.0, 400.0     # extrusion size, axis z (y = 0), length
X_TABLE, BASE_T = 145.0, 8.0                    # narrow tips ~32 mm above the base at gap 0; slide the bracket to change
X_COL1 = X_TABLE - BASE_T                       # column foot stands on the base plate
BRK_T = 30.0                                    # head bracket depth behind the adapter face
PBANK = (100.0, 62.0, 24.0)                     # USB-C PD power bank (10,000 mAh, 20 W): length (z), width (y), thickness
BASE_Y, BASE_Z = (-90.0, 90.0), (-80.0, 90.0)   # rev 7.1 (review item 8): 180 x 170 base with 4 holes to fix it to the bench
def _col_loop(c):
    return rrect_loop(-COL_A/2 - c, COL_Z - COL_A/2 - c, COL_A/2 + c, COL_Z + COL_A/2 + c, 0.5)
def stand_bracket():
    """Head bracket: adapter face with the Ø31.5 spigot recess and 4 M6 nut pockets (open at the back, nut bears on the
    pocket floor 9 mm behind the face), square hole for the column, 2 M5 holes into T-nuts. Prints back face down."""
    x0, x1 = X_AD0 - BRK_T, X_AD0
    ops = [('add', ('extx', rrect_loop(-26.0, COL_Z - 16.0, 26.0, Z_S + AD_HZ + 4.0, 4.0), x0, x1)),
           ('cut', ('extx', _col_loop(0.2), x0 - 1, x1 + 1)),
           ('cut', ('cyl', (x1 - 3.3, 0, Z_S), (x1 + 1, 0, Z_S), 15.85))]
    for a in (45, 135, 225, 315):
        y, z = 25*np.cos(np.radians(a)), Z_S + 25*np.sin(np.radians(a))
        ops += [('cut', ('cyl', (x1 - 15.0, y, z), (x1 + 1, y, z), 3.3)),
                ('cut', ('extx', hex_loop(y, z, 10.2), x0 - 1, x1 - 9.0))]
    for x in (x0 + 8.0, x1 - 8.0):
        ops.append(('cut', ('cyl', (x, 0, COL_Z - 17.0), (x, 0, COL_Z - COL_A/2 + 0.01), 2.75)))
    return ops
def stand_base():
    """Base plate (table face down) with the column socket, an M5 x 16 up into the column end, 2 M5 x 10 through the
    socket walls into T-nuts (no wobble), and 4 counterbored holes to bolt or screw the base to the bench (rev 7.1:
    unclamped, the stand tips over at a few newtons)."""
    x0, x1 = X_TABLE - BASE_T, X_TABLE
    ops = [('add', ('extx', rrect_loop(BASE_Y[0], BASE_Z[0], BASE_Y[1], BASE_Z[1], 10.0), x0, x1)),
           ('add', ('extx', rrect_loop(-17.0, COL_Z - 17.0, 17.0, COL_Z + 17.0, 4.0), x0 - 20.0, x0 + 0.01)),
           ('add', ('extx', rrect_loop(-19.0, COL_Z - 19.0, 19.0, COL_Z + 19.0, 6.0), x0 - 4.0, x0 + 0.01)),   # rev 7.2: stepped
           ('add', ('extx', rrect_loop(-21.0, COL_Z - 21.0, 21.0, COL_Z + 21.0, 8.0), x0 - 2.0, x0 + 0.01)),   # fillet at the socket root
           ('cut', ('extx', _col_loop(0.2), x0 - 21.0, x0)),
           ('cut', ('cyl', (x0 - 0.01, 0, COL_Z), (x1 + 1, 0, COL_Z), 2.75)),
           ('cut', ('cyl', (x1 - 4.5, 0, COL_Z), (x1 + 1, 0, COL_Z), 4.6))]
    for sy in (1, -1):
        ops.append(('cut', ('cyl', (x0 - 10.0, sy*18.0, COL_Z), (x0 - 10.0, sy*(COL_A/2 - 0.5), COL_Z), 2.75)))
    for sy in (1, -1):   # rev 7.2: notch the front top edge under each clamp's inside-corner fillet
        yc = sy*_clamp_y()
        ops.append(('cut', ('box', (x0 - 1, yc - CLP_W/2 - 0.5, BASE_Z[1] - CLP_R1 - 0.5), (x0 + CLP_R1 + 0.5, yc + CLP_W/2 + 0.5, BASE_Z[1] + 1))))
    for y in BASE_Y:
        for z in BASE_Z:
            yc, zc = y - np.sign(y)*12.0, z - np.sign(z)*12.0
            ops += [('cut', ('cyl', (x0 - 1, yc, zc), (x1 + 1, yc, zc), 2.75)),
                    ('cut', ('cyl', (x0 - 1, yc, zc), (x0 + 4.0, yc, zc), 5.0))]
    return ops
def column():   # 2020 extrusion (slots not modelled)
    return [('add', ('extx', _col_loop(0.0), X_COL1 - COL_LEN, X_COL1))]
# ---------- rev 7.1: desk clamps (Anurag's desk: black front edge 40 mm tall, 40 mm deep) ----------
# Two printed C-clamps at the base's front corners (+z edge, flush with the desk's front face). The upper arm sits on
# the base plate with a boss in the corner counterbore; the spine runs down in front of the desk edge; under the desk
# an M8 star-knob screw in a captive nut pushes a printed pad up under the black edge, 20 mm behind the front face.
# Grips desks 24-49 mm thick. Gripper frame: the desk top is the plane x = X_TABLE, the desk below it (+x).
DESK_T, DESK_EDGE_D = 40.0, 40.0                 # clamped edge: thickness, depth of the black section
CLP_W, CLP_SPINE, CLP_ARM = 30.0, 14.0, 12.0     # clamp width (y), spine and lower-arm thickness
CLP_Z0 = BASE_Z[1] + 0.5                         # spine inner face, 0.5 mm in front of the desk front face
CLP_SCREW_Z = BASE_Z[1] - 20.0                   # pad 20 mm behind the front face, under the black edge
CLP_X1 = X_TABLE + 55.0                          # top face of the lower arm (pad + screw travel below the desk)
CLP_R1, CLP_R2 = 3.0, 6.0                        # rev 7.2: fillets in the C's inside corners (upper, lower), where the moment peaks
def _clamp_y():
    return BASE_Y[1] - 12.0                      # centred on the base's front-corner hole (+y side)
def desk_clamp():
    """C-clamp (+y corner; the -y one is its mirror). Prints lying on its -y side (nut slot opens upward)."""
    yc, w = _clamp_y(), CLP_W/2; y0, y1 = yc - w, yc + w
    xa = X_TABLE - BASE_T                        # base top face
    zc = BASE_Z[1] - 12.0                        # corner hole
    xn = CLP_X1 + 3.0                            # captive M8 nut (13 AF x 6.5) in the lower arm
    return [('add', ('box', (xa - 8.0, y0, zc - 8.0), (xa, y1, CLP_Z0 + CLP_SPINE))),                     # upper arm
            ('add', ('box', (xa - 8.0, y0, CLP_Z0), (CLP_X1 + CLP_ARM, y1, CLP_Z0 + CLP_SPINE))),       # spine
            ('add', ('box', (CLP_X1, y0, X_TABLE*0 + BASE_Z[1] - DESK_EDGE_D), (CLP_X1 + CLP_ARM, y1, CLP_Z0 + CLP_SPINE))),   # lower arm
            ('add', ('cyl', (xa - 0.01, yc, zc), (xa + 3.5, yc, zc), 4.8)),                         # boss into the counterbore
            ('cut', ('cyl', (CLP_X1 - 1, yc, CLP_SCREW_Z), (CLP_X1 + CLP_ARM + 1, yc, CLP_SCREW_Z), 4.25)),  # M8 clearance
            ('cut', ('box', (xn, yc - 7.6, CLP_SCREW_Z - 6.6), (xn + 6.8, y1 + 1, CLP_SCREW_Z + 6.6))),       # nut slot from +y
            ('add', ('box', (xa, y0, CLP_Z0 - CLP_R1), (xa + CLP_R1, y1, CLP_Z0 + 0.01))),                    # rev 7.2 fillets
            ('cut', ('cyl', (xa + CLP_R1, y0 - 1, CLP_Z0 - CLP_R1), (xa + CLP_R1, y1 + 1, CLP_Z0 - CLP_R1), CLP_R1)),
            ('add', ('box', (CLP_X1 - CLP_R2, y0, CLP_Z0 - CLP_R2), (CLP_X1 + 0.01, y1, CLP_Z0 + 0.01))),
            ('cut', ('cyl', (CLP_X1 - CLP_R2, y0 - 1, CLP_Z0 - CLP_R2), (CLP_X1 - CLP_R2, y1 + 1, CLP_Z0 - CLP_R2), CLP_R2))]
def clamp_pad():   # printed pad under the desk edge; the knob screw tip sits in its socket
    xp = X_TABLE + DESK_T; yc = _clamp_y()
    return [('add', ('cyl', (xp, yc, CLP_SCREW_Z), (xp + 6.0, yc, CLP_SCREW_Z), 12.0)),
            ('cut', ('cyl', (xp + 3.0, yc, CLP_SCREW_Z), (xp + 7.0, yc, CLP_SCREW_Z), 4.3))]
def knob_screw():  # M8 x 40 star knob (male), tip in the pad socket, knob under the lower arm
    xp = X_TABLE + DESK_T; yc = _clamp_y(); xk = CLP_X1 + CLP_ARM
    return [('add', ('cyl', (xp + 3.2, yc, CLP_SCREW_Z), (xk + 0.01, yc, CLP_SCREW_Z), 4.0)),
            ('add', ('cyl', (xk, yc, CLP_SCREW_Z), (xk + 12.0, yc, CLP_SCREW_Z), 15.0))]

def power_bank():   # lying on the desk beside the base (+y side, 15 mm clear of it), USB-C cable up to the trigger board
    l, w, t = PBANK; y0 = BASE_Y[1] + 15.0
    return [('add', ('box', (X_TABLE - t, y0, 10.0 - l/2), (X_TABLE, y0 + w, 10.0 + l/2)))]

# rev 7: tip-block screws, finger frame (kept apart from FASTENERS so the Onshape part ids of the others stay put)
TIP_FASTENERS = [(nm, (x, tip_screw_y(x), TIP_Z[0] + 1.8), (0, 0, 1), 10.0) for nm, x in zip(('BHT_Tip_A', 'BHT_Tip_B'), TIP_SCREW_X)]   # from below

# ================= poses =================
def rotz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
def Tm(R=np.eye(3), t=(0, 0, 0)):
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; return M
MIR = np.diag([1, -1, 1, 1.0])   # Y mirror (applied to already-mirrored geometry, so we instead mirror ops)

def pose(th, wide=None):
    """Return dict name -> (ops, 4x4 transform). Lower side = mirrored ops with mirrored transforms.
    wide: tip set to place (default TIP_WIDE)."""
    wide = TIP_WIDE if wide is None else wide
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
    add('TipBlock', tip_block(wide), Tm(np.eye(3), (F1[0], F1[1], 0)))
    add('Pad', pad(wide), Tm(np.eye(3), (F1[0], F1[1], 0)))
    for nm, seat, ax, ln in TIP_FASTENERS:
        add(nm, button_screw(seat, ax, ln), Tm(np.eye(3), (F1[0], F1[1], 0)))
    for nm, pt in (('SS_F1', F1), ('SS_F2', g['F2']), ('SS_D', D), ('SS_C', C)):
        add(nm, shoulder_screw(), Tm(np.eye(3), (pt[0], pt[1], 0)))
    parts['Carriage'] = (carriage(), Tm(np.eye(3), (C[0], 0, 0)))
    parts['T8_Nut'] = (nut(), Tm(np.eye(3), (C[0], 0, 0)))
    for nm, ops in (('Base', base()), ('Cover', cover()), ('Adapter', adapter()), ('Motor', motor()),
                    ('LeadScrew', leadscrew()), ('Bearing608', bearing608()), ('LockCollar', collar()),
                    ('EncPuck', enc_puck()), ('Magnet', magnet()), ('AS5600', as5600()),
                    ('Protoboard', protoboard()), ('Pico', pico()), ('TMC2209', tmc2209()), ('Regulator', regulator()),
                    ('Cap100', cap100()), ('PDTrigger', pd_trigger()),
                    ('StandBracket', stand_bracket()), ('StandBase', stand_base()), ('Column', column()), ('PowerBank', power_bank())):
        parts[nm] = (ops, np.eye(4))
    add('Sleeve_O1', sleeve(O1), np.eye(4)); add('Sleeve_O2', sleeve(O2), np.eye(4)); add('LocPin', loc_pin(), np.eye(4))
    add('StandClamp', desk_clamp(), np.eye(4)); add('StandClampPad', clamp_pad(), np.eye(4)); add('StandKnob', knob_screw(), np.eye(4))
    add('Spacer_R', spacer(CTRL_HOLE_X[0]), np.eye(4)); add('Spacer_F', spacer(CTRL_HOLE_X[1]), np.eye(4))
    for nm, seat, ax, ln in CTRL_SCREWS + LID_SCREWS:
        add(nm, button_screw(seat, ax, ln), np.eye(4))
    parts['ElecCover'] = (elec_cover(), np.eye(4))
    parts['PicoHeaders'] = (pico_headers(), np.eye(4)); parts['TMCHeaders'] = (tmc_headers(), np.eye(4))
    for nm, seat, ax, ln, frame in FASTENERS:
        add(nm, button_screw(seat, ax, ln), Tm(np.eye(3), (C[0], 0, 0)) if frame == 'car' else np.eye(4))
    for c, nm in ((O1, 'O1'), (O2, 'O2')):
        parts['Dowel_' + nm + '_U'] = (dowel(c, 1), np.eye(4)); parts['Dowel_' + nm + '_L'] = (dowel(c, -1), np.eye(4))
    return parts

MOVING = lambda n: any(n.startswith(k) for k in ('BellCrank', 'FrontCrank', 'ConRod', 'Finger', 'SS_', 'Carriage', 'T8_Nut', 'BHN_',
                                                  'TipBlock', 'Pad', 'BHT_'))
PRINTED = ['Base', 'Cover', 'Adapter', 'Carriage', 'BellCrank_Lower_U', 'BellCrank_Upper_U', 'FrontCrank_Lower_U',
           'FrontCrank_Upper_U', 'ConRod_U', 'Finger_U', 'Finger_L', 'TipBlock_U', 'TipBlock_L', 'Pad_U']
if __name__ == '__main__':
    print('theta open %.2f deg; S %.2f..%.2f; blk %.2f..%.2f; wall %.2f..%.2f; adapter %.2f..%.2f; screw len %.1f'
          % (np.degrees(TH_O), S_MIN, S_MAX, X_BLK0, X_BLK1, X_WALL0, X_WALL1, X_AD0, X_AD1, SCREW_LEN))
    print('POST', POST_C, 'O2', O2)
