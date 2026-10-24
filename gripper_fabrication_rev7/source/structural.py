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
T_hold, I_rated = 0.40, 1.5
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
add('Shoulder screw Ø4 double shear (12.9 steel)', Fmax, Fmax/(2*np.pi*d**2/4), 500, 'τ vs ~1000 MPa shear-yield class, huge margin')
zA, zB, zP = -3.0, (D.Z_C0 + 26.0)/2, (D.Z_B0 + D.Z_U1)/2          # supports and load point along the dowel (mm)
span = zB - zA; RA = (zB - zP)/span; RB = (zP - zA)/span     # reaction shares base / cover
M_dow = lim['O2']*(zP - zA)*(zB - zP)/span
add('Dowel Ø4 bending, simply supported base↔cover', lim['O2'], 32*M_dow/(np.pi*d**3), 600, 'hardened ISO 8734, yield >1200 MPa; cover hole close fit Ø4.0')
# bearing stress on printed bores
add('Finger bore at F2 on shoulder (%.1f mm)' % t_mid, lim['F2'], lim['F2']/(d*t_mid), PR['allow'], D.MAT + ' bearing')
add('Finger bore at F1 (%.1f mm)' % t_mid, lim['F1'], lim['F1']/(d*t_mid), PR['allow'], '')
add('FrontCrank bores at O2 (%.1f+%.1f plates + %.1f spacer)' % (t_low, t_up, t_spacer), lim['O2'], lim['O2']/(d*(t_low + t_up + t_spacer)), PR['allow'], '')
add('Base dowel press hole (%.0f%% share, 6 mm)' % (100*RA), lim['O2'], RA*lim['O2']/(d*6.0), PR['allow'], 'beam reaction')
add('Cover dowel hole (%.0f%% share, 3.9 mm)' % (100*RB), lim['O2'], RB*lim['O2']/(d*3.9), PR['allow'], 'beam reaction; needs the close fit')
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
add('Tip block layer plane at the tongue top (z=14.1)', Fg_max*0.6, Fg_max*0.6*6/(arm_tip*20**2/6), PR['allow_z'], 'interlayer, allow %.0f MPa' % PR['allow_z'])
# seam joint: the moment is carried as an x-couple between the 2 tip screws and the top edge of the seam,
# and in parallel by the tongue bearing on its pocket flank; each path is checked alone with the full moment
arm_scr = (D._body_edge_y(D.SEAM_X) - 2.0) - D.TIP_SCREW_Y
F_scr = M_seam/arm_scr/2
add('Tip screw insert bearing in the finger tongue', F_scr, F_scr/(4.6*5.7), PR['allow'], 'per screw; moment arm %.1f mm to the seam top edge' % arm_scr)
add('Tip screw shank bearing in the tip block', F_scr, F_scr/(3.0*(D.Z_JAW - 3.2 - D.Z_M1)), PR['allow'], 'per screw')
Lt = D.TONGUE_X1 - D.SEAM_X
F_t = M_seam/(2*Lt/3)
add('Tongue flank bearing in the tip block pocket (%.0f mm long)' % Lt, F_t, 2*F_t/(t_mid*Lt), PR['allow'], 'triangular bearing, peak value')
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
tip = dict(Fg_max_N=round(Fg_max, 1), Fg_at_60mm_cap_N=round(Fg60, 1), factor_at_cap=round(Fg_max/Fg60, 2),
           note='Tip rows use the grip at the 66 mm stop (max MA). Gripping is capped at 60 mm by firmware, where the grip '
                'is at most Fg_at_60mm_cap_N, so the tip-row safety factors are factor_at_cap times higher in use.')
out = dict(rows=rows, driver=drv, thrust=thrust, tip=tip, min_SF=min(r['SF_yield_at_limit'] for r in rows))
json.dump(out, open('results_struct.json', 'w'), indent=1)
for r in rows: print(f"{r['item']:52s} {r['load_limit_N']:7.1f} N  σ_lim {r['stress_limit_MPa']:7.2f}  σ_op {r['stress_op_MPa']:6.2f}  SF {r['SF_yield_at_limit']}")
print(json.dumps(drv, indent=1)); print('min SF at 200 N limit:', out['min_SF'])
