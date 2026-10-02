"""Moore vs von Neumann thermoception, with ANALYTIC ground-truth gradient.

The field is a sum of isotropic Gaussians (EVAAA's recipe: point sources +
Gaussian smoothing), so its gradient is available in closed form and no finite
-difference stencil is privileged.
"""
import numpy as np
H = W = 10

def von_neumann(r):
    return [(dr,dc) for dr in range(-r,r+1) for dc in range(-r,r+1) if abs(dr)+abs(dc)<=r]
def moore(r):
    return [(dr,dc) for dr in range(-r,r+1) for dc in range(-r,r+1) if max(abs(dr),abs(dc))<=r]

class GaussField:
    def __init__(self, rng, n_src=4, sigma=1.5, amp=20.0):
        self.src = rng.uniform(0, H-1, size=(n_src,2))
        self.amp = rng.choice([-amp, amp], size=n_src)
        self.sigma = sigma
    def value(self, r, c):
        d2 = (r-self.src[:,0])**2 + (c-self.src[:,1])**2
        return float(np.sum(self.amp*np.exp(-d2/(2*self.sigma**2))))
    def grad(self, r, c):
        d = np.stack([r-self.src[:,0], c-self.src[:,1]],1)          # [n,2]
        e = self.amp*np.exp(-np.sum(d*d,1)/(2*self.sigma**2))       # [n]
        return -(e[:,None]*d).sum(0)/self.sigma**2                  # [2]

def estimate(field, r, c, offs, noise, rng):
    A,y = [],[]
    for dr,dc in offs:
        rr,cc = r+dr, c+dc
        if not (0<=rr<H and 0<=cc<W): continue
        A.append([dr,dc,1.0]); y.append(field.value(rr,cc)+rng.normal(0,noise))
    A=np.array(A); y=np.array(y)
    if len(A)<3: return None
    coef,*_ = np.linalg.lstsq(A,y,rcond=None)
    return coef[:2]

def ang(a,b):
    na,nb=np.linalg.norm(a),np.linalg.norm(b)
    if na<1e-9 or nb<1e-9: return None
    return np.degrees(np.arccos(np.clip(a@b/(na*nb),-1,1)))

def sweep(offs, noises, n_field=200, n_pos=30, seed=0):
    rng=np.random.default_rng(seed); out=[]
    for nz in noises:
        errs=[]
        for _ in range(n_field):
            f=GaussField(rng)
            for _ in range(n_pos):
                r,c = int(rng.integers(1,H-1)), int(rng.integers(1,W-1))
                g=f.grad(r,c)
                if np.linalg.norm(g)<1e-3: continue
                e=estimate(f,r,c,offs,nz,rng)
                if e is None: continue
                a=ang(g,e)
                if a is not None: errs.append(a)
        out.append(float(np.median(errs)))
    return out
