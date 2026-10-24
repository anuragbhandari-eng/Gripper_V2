"""Fastener checks for the ISO 7380 button-head set: engagement, seats, and load capacity (SF vs yield)."""
import json, numpy as np
import design as D, check as C, cadquery as cq
R = json.load(open('results.json')); S = json.load(open('results_struct.json'))
Fs_stall = S['driver']['Fs_range_at_set_N'][1]            # N, clamp/stall force at the set current
lim = R['pin_loads_envelope_limit200']
PR_y, PR_tau = D.MAT_SY, 0.58*D.MAT_SY                      # MPa (printed, in-plane)
STEEL_tau = 0.58*640.0                                      # 8.8 class shear yield
As_M3 = 5.03                                                # mm^2, M3 stress area (fully threaded button heads)
A_head = np.pi/4*(D.BH_DK**2 - 3.4**2)                      # under-head bearing annulus on a D3.4 hole
# ---- mass & centre of gravity of everything that hangs on the 4 adapter side screws (gap 30) ----
rho = {D.MAT: D.MAT_RHO*1e-3, D.PAD_MAT: D.PAD_RHO*1e-3, 'FR4': 1.85e-3, 'STEEL': 7.85e-3, 'BRASS': 8.5e-3}   # g/mm^3 (printed parts taken solid = conservative)
def mat(n):
    if n.startswith(('T8_Nut',)): return 'BRASS'
    if n.startswith(('Dowel', 'SS_', 'BH', 'LeadScrew', 'Bearing608')): return 'STEEL'
    if n.startswith('Pad'): return D.PAD_MAT
    if n.startswith(('Protoboard', 'Pico', 'TMC2209', 'Buck', 'AS5600')): return 'FR4'
    if n.startswith('Magnet'): return 'STEEL'
    if n.startswith('Standoff'): return 'BRASS'
    return D.MAT
th = np.arcsin(30/(2*D.L) + np.sin(D.TH_C))
m_tot = 0.0; mx = 0.0
for n, (ops, M) in D.pose(th).items():
    if n == 'Adapter' or n.startswith(('Stand', 'Column', 'Battery')): continue   # mount check: the gripper only
    s = cq.Shape.cast(C.place(C.solid(ops), M))
    if n == 'Motor':
        m = 280.0                                           # g, typical 40 mm NEMA 17 (body only)
    else:
        m = s.Volume()*rho[mat(n)]
    m_tot += m; mx += m*s.Center().x
x_cg = mx/m_tot
x_mount = D.X_AD0 + 7.0                                     # side-screw plane
g = 9.81; dyn = 2.0; m_pay = 500.0
F1 = D.geom(D.P, th)['F1'] if hasattr(D, 'geom') else None
from kin import geom
x_pay = geom(D.P, th)['F1'][0] + (D.SEAM_X + D.FACE_X1)/2   # payload at the middle of the pads (rev 7 tips)
M_pitch = g*dyn*(m_tot*(x_cg - x_mount) + m_pay*(x_pay - x_mount))*1e-6   # N*m
dz = D.AD_SCREW_Z[1] - D.AD_SCREW_Z[0]
F_side = M_pitch*1e3/dz/2 + g*dyn*(m_tot + m_pay)*1e-3/4   # N per screw: moment couple per side + direct shear
rows = []
def add(item, load, stress, allow_yield, note):
    rows.append(dict(item=item, load_N=round(load, 1), stress_MPa=round(stress, 2), SF_yield=round(allow_yield/stress, 1), note=note))
add('Side screw M3x8, shank shear (mount, x2 dynamic)', F_side, F_side/As_M3, STEEL_tau, '8.8 steel; ignores clamp friction')
add('Side wall hole bearing, 3.8 mm wall (mount)', F_side, F_side/(3.0*3.8), PR_y, 'base/cover side wall')
add('Adapter insert bearing in %s (mount)' % D.MAT, F_side, F_side/(4.6*5.7), PR_y, 'insert OD 4.6 x 5.7 mm')
F_mot = Fs_stall/4
add('Motor screw head on %s (open-stop stall, tension)' % D.MAT, F_mot, F_mot/A_head, PR_y, '4 screws share the stall force')
F_nut = Fs_stall/2
add('Nut screw pull-out, self-tapped 4.4 mm (open-stop stall)', F_nut, F_nut/(np.pi*2.5*4.4), PR_tau, 'shear at the D2.5 pilot wall')
add('Nut screw head on brass flange', F_nut, F_nut/A_head, 200.0, 'CuZn yield ~200 MPa')
F_cov = 4*0.45*lim['O2']/6
add('Cover screw bearing in cover (200 N limit case)', F_cov, F_cov/(3.0*(D.Z_C1 - 3.2 - D.Z_C0)), PR_y, 'all four dowel reactions on 6 screws')
# ---- engagement table (mm) ----
seat_cov = D.Z_C1 - 3.2; seat_side = D.Y_RAIL1 - 3.2
def row(screw, L, clamp, hole_bottom_gap, into):
    return dict(screw=screw, clamp_mm=round(clamp, 2), thread_mm=round(L - clamp, 2), tip_to_hole_bottom_mm=round(hole_bottom_gap, 2), into=into)
eng = [
 row('Motor M3x8', 8, 4.5, 4.5 - 3.5, 'motor tapped hole, ~4.5 deep'),
 row('Cover to wall/block M3x20', 20, seat_cov - D.Z_S, (seat_cov - 20) - (D.Z_S - 6.5), 'insert 5.7 (hole 6.5)'),
 row('Cover to post M3x8', 8, seat_cov - D.Z_C0, (seat_cov - 8) - (D.Z_C0 - 6.5), 'insert 5.7 (hole 6.5)'),
 row('Side wall to adapter M3x8', 8, seat_side - D.AD_HW, (seat_side - 8) - (D.AD_HW - 6.5), 'insert 5.7 (hole 6.5)'),
 row('Nut flange M3x8', 8, D.NUT_FL_T + 0.1, 7.0 - (8 - D.NUT_FL_T - 0.1), 'self-tapped D2.5 pilot, 7 deep'),
 row('Tip block to tongue M3x16', 16, D.Z_JAW - 3.2 - D.Z_M1, (D.Z_JAW - 3.2 - 16) - D.Z_M0, 'insert 5.7 in the finger tongue (through hole)'),
]
out = dict(mass_g=round(m_tot, 0), x_cg_mm=round(x_cg, 1), x_payload_mm=round(x_pay, 1), x_mount_mm=round(x_mount, 1),
           M_pitch_Nm=round(M_pitch, 2), rows=rows, engagement=eng, min_SF=min(r['SF_yield'] for r in rows),
           head_bearing_area_mm2=round(A_head, 1))
json.dump(out, open('results_fasteners.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ('rows', 'engagement')}))
for r in rows: print(f"{r['item']:58s} {r['load_N']:7.1f} N  {r['stress_MPa']:6.2f} MPa  SF {r['SF_yield']}")
for e in eng: print(e)
