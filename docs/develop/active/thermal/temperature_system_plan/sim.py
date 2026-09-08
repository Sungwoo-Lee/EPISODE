"""Calibration sandbox for the temperature system. Pure numpy."""
import numpy as np
H=W=10

def gaussian_smooth(f, sigma):
    """Weight-normalised Gaussian blur, EVAAA's sum/weightSum at the edges."""
    if sigma <= 0: return f.copy()
    rad=int(np.ceil(3*sigma)); k=np.exp(-0.5*(np.arange(-rad,rad+1)/sigma)**2)
    out=np.zeros_like(f); wsum=np.zeros_like(f)
    for i,dr in enumerate(range(-rad,rad+1)):
        for j,dc in enumerate(range(-rad,rad+1)):
            wt=k[i]*k[j]
            rs=np.clip(np.arange(H)+dr,0,H-1); cs=np.clip(np.arange(W)+dc,0,W-1)
            inb=((np.arange(H)+dr>=0)&(np.arange(H)+dr<H))[:,None]&((np.arange(W)+dc>=0)&(np.arange(W)+dc<W))[None,:]
            out+=np.where(inb,f[np.ix_(rs,cs)]*wt,0.0); wsum+=np.where(inb,wt,0.0)
    return out/wsum

def build_field(rng, default=0.0, n_spots=2, spot_temp=20.0, spot_size=2,
                objects=None, sigma=1.5):
    """Stage order: fill -> random spots -> object stamps -> smooth. Stamps ADD."""
    raw=np.full((H,W),default,float)
    stages={'fill':raw.copy()}
    for _ in range(n_spots):
        r,c=rng.integers(0,H),rng.integers(0,W); s=int(spot_size)//2
        sign=rng.choice([-1,1])
        for dr in range(-s,s+1):
            for dc in range(-s,s+1):
                rr,cc=r+dr,c+dc
                if 0<=rr<H and 0<=cc<W: raw[rr,cc]+=sign*spot_temp
    stages['spots']=raw.copy()
    for (r,c,t) in (objects or []):
        if 0<=r<H and 0<=c<W: raw[r,c]+=t
    stages['objects']=raw.copy()
    stages['smoothed']=gaussian_smooth(raw,sigma)
    return stages

# ---- body temperature dynamics ----
def body_traj(T_field_seq, T0=0.0, k_ex=0.04, k_loss=0.01, k_met=0.0, T_neutral=0.0):
    T=T0; out=[T]
    for Tf in T_field_seq:
        T = T + k_ex*(Tf-T) + k_met - k_loss*(T-T_neutral)
        out.append(T)
    return np.array(out)

if __name__=='__main__':
    k_ex,k_loss=0.04,0.01
    tau=1.0/(k_ex+k_loss)
    print(f'  k_exchange={k_ex}  k_loss={k_loss}')
    print(f'  time constant tau = 1/(k_ex+k_loss) = {tau:.1f} steps   (episode = 500 steps)')
    for Tf in (20.0,10.0,-20.0):
        Tstar=k_ex*Tf/(k_ex+k_loss)
        print(f'  standing in a {Tf:+.0f} cell -> equilibrium body temp {Tstar:+.1f}', end='')
        tr=body_traj([Tf]*600); idx=np.argmax(np.abs(tr)>=15.0)
        print(f'   reaches |15| (death) at step {idx if idx>0 else "never"}')
    tr=body_traj([0.0]*200,T0=14.0)
    print(f'  recovery: from T=14 in a neutral cell -> T=5 after {np.argmax(tr<=5.0)} steps')
