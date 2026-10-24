"""Single source of truth for the gripper design (mm, N, rad)."""
import numpy as np
REF=dict(O1O2_L=1.5707763, gang_deg=-42.799, r_L=0.746771, l_L=0.809826, YC_L=0.889803, YO1_L=1.820360,
         beta_deg=90.11, th_min=-15.52, th_max=70.68)
def make(L=28.0, **kw):
    P=dict(L=L, g=REF['O1O2_L'], gang=np.radians(REF['gang_deg']), r=REF['r_L']*L, l=REF['l_L']*L,
           YC=REF['YC_L']*L, YO1=REF['YO1_L']*L, beta=np.radians(90.0),
           th_c=np.radians(REF['th_min']), xc_rel_F2=15.0)
    P.update(kw)
    P['h']=P['YO1']+P['L']*np.sin(P['th_c'])   # jaw face at Y=0 when theta=th_c
    return P
