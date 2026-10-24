"""Step 2: linkage sizing, kinematics, force transmission, motor sizing. Writes results.json + plots.
Run: python3 analysis.py  (needs numpy, scipy, matplotlib)"""
import json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from params import make, REF
from kin import geom, s_of, ds_dth, face_y, transmission, statics
from scipy.optimize import brentq

P = make(28.0)
D2R = np.radians
# ---- operating window ----
TH_C = P['th_c']                                   # jaws touch (reference: -15.5 deg)
GAP_OPEN = 66.0                                    # open hard stop: 66 mm (60 mm spec + 6 mm margin)
TH_O = brentq(lambda t: 2*face_y(P, t) - GAP_OPEN, 0, D2R(80))
# ---- requirements ----
m, g = 0.5, 9.81; W = m*g
mu_jaw = 0.35          # printed serrations on typical plastic/metal (conservative; TPU pad ~0.7+)
dyn = 2.0              # load factor for robot accel up to 1 g
SF_slip = 1.5
Fg_req = W*dyn*SF_slip/(2*mu_jaw)                  # per jaw
Fg_target = 25.0
# ---- screw / motor ----
lead = 2.0e-3; d_mean = 7.0e-3; half_ang = D2R(15)
lam = np.arctan(lead/(np.pi*d_mean))
def eta(mu): ph = np.arctan(mu/np.cos(half_ang)); return np.tan(lam)/np.tan(lam+ph)
def selflock(mu): return np.arctan(mu/np.cos(half_ang)) > lam
mu_s_lo, mu_s_hi = 0.10, 0.25                      # lubricated..dry brass on steel
T_hold, I_rated = 0.40, 1.5                        # typical NEMA17 40 mm integrated-screw motor (verify datasheet)

th = np.linspace(TH_C, TH_O, 401)
gap = 2*face_y(P, th); s = s_of(P, th); G = ds_dth(P, th)
MA = G/(2*P['L']*np.cos(th))                       # Fg per jaw / total screw force
mu_t, rod = transmission(P, th)
# numeric cross-checks
fd = np.gradient(s, th); err_fd = np.nanmax(np.abs(fd[2:-2]-G[2:-2])/np.abs(G[2:-2]))
vw = [abs(-2*statics(P, t, 1.0)['Fs'] - 1/ma)/(1/ma) for t, ma in zip(th[::40], MA[::40])]
# closed-form s(theta) vs numeric loop closure (solve theta from s by root finding, compare)
rt = [abs(brentq(lambda t: s_of(P, t)-si, TH_C-0.2, TH_O+0.2) - ti) for si, ti in zip(s[::50], th[::50])]

Fs_op = Fg_target/np.min(MA)                        # screw force giving >= 25 N everywhere
Fs_lim = 200.0                                      # structural limit case (driver misset / stall)
T_op_hi = Fs_op*lead/(2*np.pi*eta(mu_s_hi))         # worst friction -> most torque
T_op_lo = Fs_op*lead/(2*np.pi*eta(mu_s_lo))
loads_op = [statics(P, t, Fg_target) for t in th[::20]]
def pin_env(Fs_total):
    out = {k: 0.0 for k in ['F1','F2','O1','O2','D','C','rod','N']}
    for t, ma in zip(th[::4], MA[::4]):
        st = statics(P, t, Fs_total*ma)
        for k in out: out[k] = max(out[k], abs(st[k]))
    return out
env_op = pin_env(Fs_op); env_lim = pin_env(Fs_lim)

R = dict(
  params={k: (float(v) if np.ndim(v)==0 else list(map(float, v))) for k, v in P.items()},
  derived=dict(O2=list(map(float, geom(P,0.0)['O2'])), F1F2=list(map(float, geom(P,0.0)['O2']-geom(P,0.0)['O1'])),
               h_face_below_F1=float(P['h'])),
  window=dict(th_closed_deg=float(np.degrees(TH_C)), th_open_deg=float(np.degrees(TH_O)), gap_max_mm=GAP_OPEN,
              C_x_closed=float(s[0]), C_x_open=float(s[-1]), stroke_mm=float(s[-1]-s[0]),
              screw_turns=float((s[-1]-s[0])/2.0)),
  transmission=dict(mu_min_deg=float(mu_t.min()), mu_max_deg=float(mu_t.max()), rod_angle_max_deg=float(rod.max()),
                    ds_dth_min=float(G.min()), ds_dth_max=float(G.max()), toggle_in_window=bool((G<=0).any())),
  MA=dict(min=float(MA.min()), at_gap_0=float(MA[0]), at_gap_60=float(np.interp(60, gap, MA)), max=float(MA.max())),
  requirement=dict(W_N=W, mu_jaw=mu_jaw, dyn=dyn, SF_slip=SF_slip, Fg_req_per_jaw=float(Fg_req), Fg_target=Fg_target),
  screw=dict(lead_mm=2.0, lead_angle_deg=float(np.degrees(lam)), eta_mu010=float(eta(0.10)), eta_mu025=float(eta(0.25)),
             self_locking_mu010=bool(selflock(0.10)), self_locking_mu025=bool(selflock(0.25))),
  motor=dict(Fs_op_N=float(Fs_op), T_op_Nm_range=[float(T_op_lo), float(T_op_hi)], T_hold_assumed=T_hold,
             torque_fraction_of_hold=float(T_op_hi/T_hold), Fs_at_full_hold_mu010=float(2*np.pi*eta(0.10)*T_hold/lead),
             Fg_at_gap60_with_Fs_op=float(Fs_op*np.interp(60, gap, MA)), Fs_lim_N=Fs_lim),
  pin_loads_envelope_op=env_op, pin_loads_envelope_limit200=env_lim,
  checks=dict(deriv_fd_max_rel_err=float(err_fd), virtual_work_vs_FBD_max_rel_err=float(max(vw)),
              inverse_solve_max_err_rad=float(max(rt))))
json.dump(R, open('results.json','w'), indent=1)

fig, ax = plt.subplots(2, 2, figsize=(11, 8))
ax[0,0].plot(np.degrees(th), gap); ax[0,0].set(xlabel='crank angle θ [deg]', ylabel='jaw gap [mm]', title='Jaw gap')
ax[0,0].axhline(60, ls='--', c='gray'); ax2=ax[0,0].twinx(); ax2.plot(np.degrees(th), s, c='C1'); ax2.set_ylabel('carriage C_x [mm]', color='C1')
ax[0,1].plot(gap, MA); ax[0,1].set(xlabel='jaw gap [mm]', ylabel='Fg per jaw / Fs total', title='Mechanical advantage')
ax[1,0].plot(gap, Fs_op*MA, label=f'Fs = {Fs_op:.0f} N (operating)'); ax[1,0].axhline(Fg_req, ls='--', c='r', label=f'required {Fg_req:.1f} N')
ax[1,0].set(xlabel='jaw gap [mm]', ylabel='grip force per jaw [N]', title='Grip force'); ax[1,0].legend()
ax[1,1].plot(gap, mu_t, label='transmission angle μ (rod vs bell-crank arm)'); ax[1,1].plot(gap, rod, label='rod angle to slider axis')
ax[1,1].set(xlabel='jaw gap [mm]', ylabel='deg', title='Transmission'); ax[1,1].legend()
for a in ax.flat: a.grid(alpha=.3)
plt.tight_layout(); plt.savefig('step2_kinematics.png', dpi=110)
print(json.dumps({k: R[k] for k in ['window','transmission','MA','requirement','screw','motor','checks']}, indent=1))
print('pin env op', {k: round(v,1) for k,v in env_op.items()}); print('pin env 200N', {k: round(v,1) for k,v in env_lim.items()})
