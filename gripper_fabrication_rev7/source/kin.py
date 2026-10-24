"""Kinematics + statics of the lead-screw parallel gripper (upper side; lower side mirrored).
Frame: X forward along screw, Y outward (upper side), origin on centerline at X of O1.
theta = angle of crank O1->F1 from +X (CCW +). Bell crank: D at theta - beta from O1.
Carriage pin C on line Y = YC, behind D (smaller X)."""
import numpy as np

def geom(P, th):
    th=np.asarray(th,float)
    O1=np.array([0.0,P['YO1']]); O2=O1+P['L']*P['g']*np.array([np.cos(P['gang']),np.sin(P['gang'])])
    u=np.stack([np.cos(th),np.sin(th)],-1)
    F1=O1+P['L']*u; F2=O2+P['L']*u
    ph=th-P['beta']
    D=O1+P['r']*np.stack([np.cos(ph),np.sin(ph)],-1)
    dy=P['YC']-D[...,1]
    disc=P['l']**2-dy**2
    w=np.where(disc>=0,np.sqrt(np.abs(disc)),np.nan)
    C=np.stack([D[...,0]-w,np.full_like(w,P['YC'])],-1)
    return dict(O1=O1,O2=O2,F1=F1,F2=F2,D=D,C=C)

def s_of(P,th): return geom(P,th)['C'][...,0]

def ds_dth(P,th,h=1e-6):
    # analytic
    ph=th-P['beta']; Dx=P['r']*np.cos(ph); Dy=P['YO1']+P['r']*np.sin(ph)
    dDx=-P['r']*np.sin(ph); dDy=P['r']*np.cos(ph)
    dy=P['YC']-Dy; w=np.sqrt(P['l']**2-dy**2)
    dw=(dy*dDy)/w   # d/dth sqrt(l^2-dy^2) = -dy*(-dDy)/w
    return dDx-dw

def face_y(P,th): return P['YO1']+P['L']*np.sin(th)-P['h']

def theta_of_s(P,s,th0=0.3):
    from scipy.optimize import brentq
    f=lambda t: s_of(P,t)-s
    return brentq(f,np.radians(-60),np.radians(110))

def transmission(P,th):
    g=geom(P,th); D=g['D'];C=g['C'];O1=g['O1']
    a=D-O1; b=D-C
    mu=np.degrees(np.arccos(np.abs(np.sum(a*b,-1))/np.linalg.norm(a,axis=-1)/np.linalg.norm(b,axis=-1)))
    rod=np.degrees(np.arctan2(b[...,1],b[...,0]))   # rod angle wrt slider axis
    return mu, rod

def statics(P, th, Fg, Fx=0.0):
    """Upper side. External load on finger: grip reaction +Fg in +Y (object pushes jaw outward),
    plus Fx in +X (payload drag along the jaw), applied at contact point Pc (finger-fixed).
    Unknowns: pin forces (force ON first-named body BY second): 
      F1: on finger by BC (2), F2: on finger by FC (2), O1: on BC by ground(2), O2: on FC by ground(2),
      D: on BC by rod (2), C: on carriage by rod (2), Fs: screw force on carriage half (x), N: guide (y)
    Returns dict of forces (N)."""
    g=geom(P,th); O1,O2,F1,F2,D,C=[g[k] for k in ['O1','O2','F1','F2','D','C']]
    Pc=np.array([F2[0]+P['xc_rel_F2'], P['YO1']+P['L']*np.sin(th)-P['h']])
    cr=lambda r,f: r[0]*f[1]-r[1]*f[0]
    # variable order: F1x F1y F2x F2y O1x O1y O2x O2y Dx Dy Cx Cy Fs N
    A=[];b=[]
    def row(coeffs,rhs):
        r=np.zeros(14)
        for i,v in coeffs: r[i]+=v
        A.append(r); b.append(rhs)
    ext=np.array([Fx,Fg])
    # finger: forces F1 (on finger), F2 (on finger), ext at Pc. moments about F1
    row([(0,1),(2,1)],-ext[0]); row([(1,1),(3,1)],-ext[1])
    rF2=F2-F1; rP=Pc-F1
    row([(2,-rF2[1]),(3,rF2[0])],-cr(rP,ext))
    # BC: -F1 (reaction), O1, D. moments about O1
    rF1=F1-O1; rD=D-O1
    row([(0,-1),(4,1),(8,1)],0); row([(1,-1),(5,1),(9,1)],0)
    row([(0,rF1[1]),(1,-rF1[0]),(8,-rD[1]),(9,rD[0])],0)
    # FC: -F2, O2. moments about O2
    rF2b=F2-O2
    row([(2,-1),(6,1)],0); row([(3,-1),(7,1)],0)
    row([(2,rF2b[1]),(3,-rF2b[0])],0)
    # rod CD: on rod at D = -Dforce, at C = -Cforce ; two-force: sum=0, and aligned with CD
    row([(8,1),(10,1)],0); row([(9,1),(11,1)],0)
    e=D-C; # force on rod at D (=-Dvec) parallel to e  -> cross(e, Dvec)=0
    row([(8,-e[1]*-1),(9,e[0]*-1)],0)  # cross(e,-Dv)=0
    # carriage half: Cforce + Fs (x) + N (y) = 0
    row([(10,1),(12,1)],0); row([(11,1),(13,1)],0)
    x=np.linalg.solve(np.array(A),np.array(b))
    n=lambda i: np.hypot(x[i],x[i+1])
    return dict(F1=n(0),F2=n(2),O1=n(4),O2=n(6),D=n(8),C=n(10),Fs=x[12],N=x[13],rod=n(8),x=x,Pc=Pc)
