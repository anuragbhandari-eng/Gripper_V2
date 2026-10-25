"""Step 5: structural + motor/driver checks. Uses pin-load envelopes from analysis (results.json)."""
import json, numpy as np
import design as D
R = json.load(open('results.json')); P = R['params']
t_low, t_mid, t_up = D.Z_B1 - D.Z_B0, D.Z_M1 - D.Z_M0, D.Z_U1 - D.Z_U0   # printed layer thicknesses (mm)
t_spacer = D.Z_U0 - D.Z_B1
op, lim = R['pin_loads_envelope_op'], R['pin_loads_envelope_limit200']
PR = dict(sy=D.MAT_SY, allow=D.MAT_SY/2, allow_z=D.MAT_SZ/2)   # MPa, printed: in-plane (along rasters) and across layers; allowable = strength/2
d = 4.0
rows = []
# motor / driver
T_hold, I_rated = 0.44, 1.7                     # chosen motor: YEJMKJ N17-Y42-39-SG240 (Amazon B0FHHWXJLV)
eta_hi, eta_lo = R['screw']['eta_mu010'], R['screw']['eta_mu025']
lead = R['screw']['lead_mm']*1e-3
# rev 7 (Tr8x8): the lowest current (0.05 A steps) that still gives the operating screw force with worst-case friction
I_set = round(float(np.ceil(R['motor']['Fs_op_N']*lead/(2*np.pi*eta_lo*T_hold/I_rated)/0.05 - 1e-9)*0.05), 2)
T_set = T_hold*I_set/I_rated
Fs_best = 2*np.pi*eta_hi*T_set/lead; Fs_worst = 2*np.pi*eta_lo*T_set/lead
drv = dict(I_rated_A=I_rated, T_hold_Nm=T_hold, I_set_rms_A=I_set, T_at_set_Nm=round(T_set, 3),
           Fs_range_at_set_N=[round(Fs_worst, 1), round(Fs_best, 1)], Fs_needed_N=round(R['motor']['Fs_op_N'], 1), Fs_operating_max_N=round(Fs_best, 1),
           grip_min_per_jaw_N=round(Fs_worst*R['MA']['min'], 1), grip_at60_worstfriction_N=round(Fs_worst*R['MA']['at_gap_60'], 1),
           within_200N_limit=bool(Fs_best <= 200),
           speed_note='600 rpm -> %.0f mm/s -> full stroke %.1f s' % (10*R['screw']['lead_mm'], R['window']['stroke_mm']/(10*R['screw']['lead_mm'])))

def add(item, load_lim, stress_lim, allow, note):
    sf = allow*2/stress_lim if stress_lim > 0 else np.inf   # SF vs yield
    rows.append(dict(item=item, load_limit_N=round(load_lim, 1), stress_limit_MPa=round(stress_lim, 2),
                     stress_op_MPa=round(stress_lim*Fs_best/200.0, 2), SF_yield_at_limit=round(sf, 1), note=note))
# pins
Fmax = max(lim.values())
add('Shoulder screw Ø4 double shear (304 stainless)', Fmax, Fmax/(2*np.pi*d**2/4), 130, 'τ vs ~260 MPa shear yield (A2-70 class); bought: MECCANIXITY 304')
zA, zB, zP = D.DOW_Z[0]/2, D.Z_C0 + D.SLV_L/2, (D.Z_B0 + D.Z_U1)/2   # supports (base socket, bonded sleeve) and load point (mm)
span = zB - zA; RA = (zB - zP)/span; RB = (zP - zA)/span     # reaction shares base / cover
M_dow = lim['O2']*(zP - zA)*(zB - zP)/span
add('Dowel Ø4 bending, simply supported base↔cover', lim['O2'], 32*M_dow/(np.pi*d**3), 600, 'hardened ISO 8734, yield >1200 MPa; top held by the bonded sleeve')
# bearing stress on printed bores
add('Finger bore at F2 on shoulder (%.1f mm)' % t_mid, lim['F2'], lim['F2']/(d*t_mid), PR['allow'], D.MAT + ' bearing')
add('Finger bore at F1 (%.1f mm)' % t_mid, lim['F1'], lim['F1']/(d*t_mid), PR['allow'], '')
add('FrontCrank bores at O2 (%.1f+%.1f plates + %.1f spacer)' % (t_low, t_up, t_spacer), lim['O2'], lim['O2']/(d*(t_low + t_up + t_spacer)), PR['allow'], '')
add('Base dowel press hole (%.0f%% share, %.1f mm)' % (100*RA, -D.DOW_Z[0]), lim['O2'], RA*lim['O2']/(d*-D.DOW_Z[0]), PR['allow'], 'beam reaction')
add('Cover hole on the bonded sleeve (%.0f%% share, Ø6 x %.0f)' % (100*RB, D.SLV_L), lim['O2'], RB*lim['O2']/(2*D.SLV_RO*D.SLV_L), PR['allow'], 'beam reaction; sleeve bonded in place, zero clearance')
add('ConRod bores (%.1f mm)' % t_mid, lim['rod'], lim['rod']/(d*t_mid), PR['allow'], '')
add('Carriage ears at C (%.1f + %.1f mm)' % (D.Z_B1, t_up), lim['C'], lim['C']/(d*(D.Z_B1 + t_up)), PR['allow'], '')
# tear-out ligaments: boss R5.5, hole R2.1 -> 3.4 mm ligaments, double
add('Finger boss tear-out at F2', lim['F2'], lim['F2']/(2*3.4*t_mid), PR['allow']*0.6, 'shear allowable 0.6σ')
# two-force members (axial)
add('FrontCrank (two-force) net section', lim['F2'], lim['F2']/((11-4.2)*(t_low + t_up)), PR['allow'], 'axial only')
add('ConRod (two-force) net section', lim['rod'], lim['rod']/((10-4.2)*t_mid), PR['allow'], 'axial only')
# bell crank bending (3-force member): section 11 mm from O1, width 18.2, plates 6+4
Z = (t_low*18.2**2/6) + (t_up*18.2**2/6)
add('BellCrank bending near O1 (two plates)', lim['F1'], lim['F1']*(28-11)/Z, PR['allow'], 'conservative: full F1 ⟂ arm')
# finger + bolt-on tip (rev 7): grip at max MA with 200 N screw force, at the far end of the pad (worst lever)
Fg_max = 200*R['MA']['max']
arm_tip = D.FACE_X1 - D.SEAM_X                                   # seam to far-tip contact
seam_d = D._body_edge_y(D.SEAM_X) - D.SEAM_Y0                    # finger body depth at the seam
M_seam = Fg_max*arm_tip
add('Finger body at the tip seam (%.1f mm deep x %.1f)' % (seam_d, t_mid), Fg_max, M_seam/(t_mid*seam_d**2/6), PR['allow'], 'far-tip grip, cantilever %.0f mm' % arm_tip)
# rev 7.1 seam joint: only the tongue crosses the seam, so it carries the whole tip moment in bending at its root and
# hands it to the tip block by bearing on the pocket flanks; the 2 tip screws only hold the block on (from below).
t_tg, h_tg = D.TIP_Z[1] - D.Z_M0, D.tongue_top(D.SEAM_X) - D.TONGUE_Y0     # tongue thickness (z) and root depth (y)
add('Tongue root bending at the seam (%.1f deep x %.1f)' % (h_tg, t_tg), Fg_max, M_seam/(t_tg*h_tg**2/6), PR['allow'], 'far-tip grip; in-plane (along rasters)')
Lt = D.TONGUE_X1 - D.SEAM_X
F_t = M_seam/(2*Lt/3)
add('Tongue flank bearing in the tip block pocket (%.0f mm long)' % Lt, F_t, 2*F_t/(t_tg*Lt), PR['allow'], 'triangular bearing, peak value')
wall_w = (D.TONGUE_Y0 - 0.15) - (D.tip_face_y(True) + D.PAD_KEY[2])         # wide block: wall between pad groove and pocket
f_low = (D.Z_M0 - D.TIP_Z[0])/(D.TIP_Z[1] - D.TIP_Z[0])                     # pad share below the tongue
add('Tip block wall, interlayer shear at z = %.1f (wide set, %.2f mm wall)' % (D.Z_M0, wall_w), Fg_max*f_low, Fg_max*f_low/(arm_tip*wall_w), PR['allow_z']*0.6, 'pad load below the tongue')
# grip on the top edge of the pad (small objects): the pad force sits half the pad height off the pin plane and
# twists the finger about x; the tongue takes it in torsion and the F1/F2 bores as a bearing couple
dz = D.TIP_Z[1] - D.Z_S
T_x = Fg_max*dz
b, cc = max(h_tg, t_tg), min(h_tg, t_tg); alpha = 0.208   # torsion factor of a square, conservative for b/c > 1
add('Tongue torsion, grip on the pad edge (%.2f mm off the pin plane)' % dz, Fg_max, T_x/(alpha*b*cc**2), PR['allow_z']*0.6, 'interlayer shear allowable')
d = 4.0
sig_F2 = lim['F2']/(d*t_mid) + 6*(T_x/2)/(d*t_mid**2)
add('Finger bore at F2, far-tip grip on the pad edge', lim['F2'], sig_F2, PR['allow'], 'in-plane bearing + twist couple, bore only (conservative: the crank plates above and below take the twist once the 0.2/0.3 mm gaps close)')
Fg60 = 200*R['MA']['at_gap_60']
# thrust path (rev 6): grip thrust goes screw -> collar -> 608 inner ring -> balls -> outer ring -> block front lip
Fs_lim = 200.0
r_or = 8.5                                        # 608 outer-ring face inner radius (approx.)
add('Block front lip bearing on 608 outer ring', Fs_lim, Fs_lim/(np.pi*(11.0**2 - r_or**2)), PR['allow'], D.MAT + ' bearing, grip thrust')
t_lip = D.X_PCB0 - 1.0 - D.X_BRG1                    # rev 7: lip between the 608 and the encoder relief
add('Block front lip shear-out (%.2f mm lip)' % t_lip, Fs_lim, Fs_lim/(np.pi*22.0*t_lip), PR['allow']*0.6, 'shear allowable 0.6σ; encoder board in front')
C0_608 = 1370.0                                   # N, 608 static load rating (radial); axial static taken as 0.5*C0
thrust = dict(load_N=Fs_lim, bearing608_axial_static_capacity_N=0.5*C0_608, ratio=round(0.5*C0_608/Fs_lim, 1),
              note='collar set-screw holding on the threaded screw is not rated: verify with a hand pull test before assembly')
Fg_use = Fs_best*R['MA']['at_gap_60']                   # in use: stall force at the set current, at the 60 mm cap
# rev 7.1 (review item 5): hitting a hard stop at speed. The rotor inertia is reflected to the carriage by the lead;
# J is a typical 40 mm NEMA 17 value (check the motor you buy); stop stiffness 1-10 N/um.
from kin import ds_dth
J_rot = 65e-7                                             # kg m^2 (listing: about 65 g cm2)
m_ref = J_rot*(2*np.pi/lead)**2
v_full, v_home = R['screw']['lead_mm']*10.0, 10.0          # mm/s: 600 rpm, homing
I_home = 0.3
dynamic = dict(J_rotor_kgm2_assumed=J_rot, reflected_mass_kg=round(m_ref, 2),
               F_stop_N_at_600rpm=[round(v_full/1e3*np.sqrt(m_ref*k*1e6)) for k in (1, 10)],
               F_stop_N_at_10mm_s=[round(v_home/1e3*np.sqrt(m_ref*k*1e6)) for k in (1, 10)],
               homing=dict(direction='closing: the reaction goes through collar, 608 and printed lip, not the motor bearing',
                           current_A=I_home, speed_mm_s=v_home, Fs_max_N=round(2*np.pi*eta_hi*T_hold*I_home/I_rated/lead, 1)))
# rev 7.1 (review item 9): run current against gap for a steady grip with worst-case friction (firmware table)
Fg_goal, k_I = 30.0, 2*np.pi*eta_lo*T_hold/I_rated/lead   # N per jaw; N of screw force per A (worst friction)
schedule = []
for g in range(0, 61, 10):
    thg = np.arcsin(g/(2*D.L) + np.sin(D.TH_C)); ma = float(ds_dth(D.P, thg)/(2*D.L*np.cos(thg)))
    I = float(np.clip(Fg_goal/(k_I*ma), I_home, I_set))
    schedule.append(dict(gap_narrow_mm=g, gap_wide_mm=int(g + 2*D.WIDE_OFS), MA=round(ma, 3), I_run_A=round(I, 2),
                         IRUN=int(round(32*I/I_set)) - 1, grip_N=[round(k_I*I*ma, 1), round(k_I*I*ma*eta_hi/eta_lo, 1)]))
tip = dict(Fg_max_N=round(Fg_max, 1), Fg_at_60mm_cap_N=round(Fg60, 1), factor_at_cap=round(Fg_max/Fg60, 2),
           Fg_in_use_N=round(Fg_use, 1), factor_in_use=round(Fg_max/Fg_use, 2),
           note='Tip rows use the grip at the 66 mm stop (max MA). Gripping is capped at 60 mm by firmware, where the grip '
                'is at most Fg_at_60mm_cap_N, so the tip-row safety factors are factor_at_cap times higher in use.')
# rev 7.1: desk clamp (bench stand), hand-tight knob, taken as 400 N; the C-frame bends at the spine and the arms
F_cl = 400.0
w_c = D.CLP_W
arm_s = (D.CLP_Z0 + D.CLP_SPINE/2) - D.CLP_SCREW_Z
add('Desk clamp spine bending (%.0f x %.0f, hand-tight 400 N)' % (w_c, D.CLP_SPINE), F_cl, F_cl*arm_s/(w_c*D.CLP_SPINE**2/6), PR['allow'], 'prints on its side: in-plane')
add('Desk clamp lower arm at the spine (%.0f x %.0f)' % (w_c, D.CLP_ARM), F_cl, F_cl*(D.CLP_Z0 - D.CLP_SCREW_Z)/(w_c*D.CLP_ARM**2/6), PR['allow'], '')
out = dict(rows=rows, driver=drv, thrust=thrust, tip=tip, dynamic=dynamic, current_schedule=schedule,
           min_SF=min(r['SF_yield_at_limit'] for r in rows),
           min_SF_in_use=round(min(r['SF_yield_at_limit'] for r in rows)*Fg_max/Fg_use, 1))
json.dump(out, open('results_struct.json', 'w'), indent=1)
for r in rows: print(f"{r['item']:52s} {r['load_limit_N']:7.1f} N  σ_lim {r['stress_limit_MPa']:7.2f}  σ_op {r['stress_op_MPa']:6.2f}  SF {r['SF_yield_at_limit']}")
print(json.dumps(drv, indent=1)); print('min SF at 200 N limit:', out['min_SF'])
