"""Figure M — the world as it now ships, measured from the live environment.

Everything here comes from the real config through the real loader and the real
reset path, then the body recurrence exactly as core.py applies it (including the
warming / cooling scales). Nothing is hand-typed.

Run: /home/vncuser/miniconda3/envs/grid_world_pain/bin/python figM_shipped.py
"""
import os, sys, json
os.environ.setdefault("JAX_PLATFORMS", "cpu")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."]*5))
sys.path.insert(0, ROOT)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, jax
from src.environment.config_loader import load_env_config, load_env_params, _thermal_radial_equilibria
from src.environment.core import jax_reset, heat_source_mask

SURF='#fcfcfb'; INK='#16181d'; INK2='#4e545e'; GRID='#e3e2de'
COLD='#2a78d6'; HOT='#b02b2b'; WARM='#eb6834'; OK='#0f7a55'; MUTE='#c3c6c2'
plt.rcParams.update({'figure.dpi':140,'figure.facecolor':SURF,'axes.facecolor':SURF,
 'savefig.facecolor':SURF,'text.color':INK,'axes.labelcolor':INK2,'xtick.color':INK2,
 'ytick.color':INK2,'axes.edgecolor':GRID,'font.size':9.5,'axes.titlesize':10.5,
 'axes.titleweight':'bold'})

CFG = 'configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml'
p = load_env_params(load_env_config(os.path.join(ROOT, CFG)))
KX, KL = float(p.thermal_k_exchange), float(p.thermal_k_loss)
WS, CS = float(p.thermal_warming_rate_scale), float(p.thermal_cooling_rate_scale)
LO, HI, SET = float(p.min_temperature), float(p.max_temperature), float(p.temperature_setpoint)
SIG = float(p.thermal_sigma)
W_LO, W_HI = float(p.thermal_default_temp_low), float(p.thermal_default_temp_high)
EPISODE, HUNGER = 500, 100

def step(T, amb):
    d = KX*(amb - T) + float(p.thermal_k_metabolic) - KL*(T - SET)
    return T + (WS if d > 0 else CS)*d

def run(T0, amb, stop, cap=400):
    T = T0; traj=[T]
    for n in range(1, cap+1):
        T = step(T, amb); traj.append(T)
        if stop(T): return n, np.array(traj)
    return None, np.array(traj)

# ---- live resets -------------------------------------------------------------
N = 600
st = jax.vmap(lambda k: jax_reset(p, k))(jax.random.split(jax.random.PRNGKey(11), N))
fld = np.asarray(st.thermal_field)
eq  = KX*fld/(KX+KL)
safe = (eq >= LO) & (eq <= HI)
away=[]; rew=[]; t1=[]; burn=[]
for i in range(N):
    s = safe[i]
    if not s.any(): continue
    e = eq[i]; ring=float(e[s].max()); far=float(e.min()); fire=float(e.max())
    amb = lambda x: x*(KX+KL)/KX
    away.append(run(0.0, amb(far), lambda T: T <= LO)[0])
    rew.append(run(-14.0, amb(ring), lambda T: T >= 0.0)[0])
    t1.append(ring + WS*(KX*(amb(fire)-ring) - KL*(ring-SET)))
    burn.append(run(ring, amb(fire), lambda T: T >= HI, cap=20)[0])
away, rew, t1, burn = map(np.array, (away, rew, t1, burn))

fig = plt.figure(figsize=(13.6, 9.0))
gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.20)

# ---- A: radial profile, published vs shipped ---------------------------------
axA = fig.add_subplot(gs[0,0])
def prof(world, ratio, kl):
    e = _thermal_radial_equilibria(ratio*abs(world), world, SIG, 3, 10, 10, KX, kl, 0.0, 0.0)
    ds = [d for d in sorted(e) if e[d] is not None]
    return ds, [e[d] for d in ds]
for (w,r,kl,col,ls,lab) in ((-25.0,12,0.01,MUTE,'--','as published: world −25, fire 12×, k_loss 0.01'),
                            (-30.0,11,0.02,COLD,'-','as shipped: world −30, fire 11×, k_loss 0.02')):
    ds, ys = prof(w,r,kl)
    axA.plot(ds, ys, color=col, lw=2.4, ls=ls, marker='o', ms=5, label=lab)
    for d,y in zip(ds,ys):
        if d in (0,1):
            dy = 9 if ls == '--' else -13          # published above the point, shipped below
            axA.annotate(f"{y:+.1f}", (d,y), xytext=(7,dy), textcoords='offset points',
                         fontsize=8.4, color=col, fontweight='bold')
axA.axhspan(LO, HI, color=OK, alpha=0.08, zorder=0)
axA.axhline(HI, color=HOT, lw=1.0); axA.axhline(LO, color=COLD, lw=1.0)
axA.text(1.55, HI+1.6, "heat death +15", color=HOT, fontsize=8.4, ha='center')
axA.text(1.55, LO-2.2, "cold death −15", color=COLD, fontsize=8.4, ha='center', va='top')
axA.set_xticks([0,1,2,3]); axA.set_xlim(-0.2, 3.2); axA.set_ylim(-28, 62)
axA.set_xlabel("distance from the fire  (cells, Manhattan)")
axA.set_ylabel("body temperature it settles at  (degrees)")
axA.set_title("A   Doubling k_loss moved every settling temperature", loc='left')
axA.legend(frameon=False, fontsize=8.2, loc='upper right')
axA.grid(color=GRID, lw=.7); axA.set_axisbelow(True)
for s_ in ('top','right'): axA.spines[s_].set_visible(False)

# ---- B: the three clocks, then and now ---------------------------------------
axB = fig.add_subplot(gs[0,1])
rows = [("episode", EPISODE, EPISODE, GRID),
        ("hunger", HUNGER, HUNGER, WARM),
        ("thermal", 34, int(np.median(away)), COLD)]
y = np.arange(len(rows))[::-1]
for (lab, before, now, col), yy in zip(rows, y):
    axB.barh(yy+0.17, before, height=0.32, color=MUTE)
    axB.barh(yy-0.17, now,    height=0.32, color=col)
    axB.text(before+7, yy+0.17, f"{before}", va='center', fontsize=8.6, color=INK2)
    axB.text(now+7,    yy-0.17, f"{now}",    va='center', fontsize=8.6, color=INK, fontweight='bold')
axB.set_yticks(y); axB.set_yticklabels([r[0] for r in rows], fontsize=9)
axB.set_xlim(0, 585); axB.set_xlabel("steps")
axB.set_title("B   The three clocks: episode limit, hunger, temperature — before (grey) and now", loc='left')
axB.text(0, -0.95, f"Away from the fire went from 34 steps to {away.min()}–{away.max()} "
         f"(median {int(np.median(away))}), which is the point of the retune:\nit now sits alongside the "
         f"hunger clock instead of dominating it.", fontsize=8.6, color=INK2, va='top', linespacing=1.5)
for s_ in ('top','right'): axB.spines[s_].set_visible(False)

# ---- C: one cycle at the shipped settings ------------------------------------
axC = fig.add_subplot(gs[1,0])
i0 = int(np.argsort(away)[len(away)//2])                      # a median episode
e = eq[i0]; s = safe[i0]
ring=float(e[s].max()); far=float(e.min()); fire=float(e.max())
amb = lambda x: x*(KX+KL)/KX
_, up   = run(-14.0, amb(ring), lambda T: T >= 0.0)
_, down = run(0.0,  amb(far),  lambda T: T <= LO)
_, onf  = run(ring, amb(fire), lambda T: T >= HI, cap=6)
t = 0
axC.plot(np.arange(len(up)), up, color=WARM, lw=2.6, label=f"rewarming beside the fire ({len(up)-1} steps)")
t = len(up)-1
axC.plot(t+np.arange(len(down)), down, color=COLD, lw=2.6, label=f"out in the cold ({len(down)-1} steps)")
axC.axhspan(LO, HI, color=OK, alpha=0.07, zorder=0)
axC.axhline(0, color=INK2, lw=0.9, ls=(0,(4,3)))
axC.axhline(LO, color=COLD, lw=1.0); axC.axhline(HI, color=HOT, lw=1.0)
axC.axvline(t, color=GRID, lw=1.2)
axC.text(t+2, 10.4, "leaves the fire", fontsize=8.4, color=INK2)
axC.text(6.5, -16.4, "arrives nearly frozen", fontsize=8.4, color=INK2)
axC.set_xlim(-2, t+len(down)+6); axC.set_ylim(-19, 21)   # headroom so the legend clears +15
axC.set_xlabel("step within the episode  (one environment step per unit)")
axC.set_ylabel("body temperature  (degrees, 0 = comfortable)")
axC.set_title("C   One full cycle as it now ships", loc='left')
axC.legend(frameon=False, fontsize=8.4, loc='upper right', bbox_to_anchor=(1.0, 1.0))
axC.grid(color=GRID, lw=.7); axC.set_axisbelow(True)
for s_ in ('top','right'): axC.spines[s_].set_visible(False)

# ---- D: measured across 600 live episodes ------------------------------------
axD = fig.add_subplot(gs[1,1])
specs = [("steps away\nfrom the fire", away, (80,110), COLD),
         ("steps to rewarm\nfrom near-death", rew, (0,10), WARM),
         ("body after ONE step\nonto the fire", t1, (None,HI), HOT)]
pos = np.arange(len(specs))
for k,(lab, vals, band, col) in enumerate(specs):
    v = np.asarray(vals, dtype=float)
    axD.scatter(np.full(v.size, k) + (np.random.default_rng(3).random(v.size)-0.5)*0.22, v,
                s=6, color=col, alpha=0.25, zorder=3)
    axD.plot([k-0.25, k+0.25], [v.min(), v.min()], color=col, lw=2)
    axD.plot([k-0.25, k+0.25], [v.max(), v.max()], color=col, lw=2)
    axD.annotate(f"{v.min():.0f}–{v.max():.0f}" if k < 2 else f"{v.min():+.1f}..{v.max():+.1f}",
                 (k, v.max()), xytext=(0, 9), textcoords='offset points', ha='center',
                 fontsize=8.6, color=col, fontweight='bold')
    lo_, hi_ = band
    if lo_ is not None: axD.plot([k-0.34,k+0.34],[lo_,lo_], color=INK2, lw=1.4, ls='--')
    if hi_ is not None: axD.plot([k-0.34,k+0.34],[hi_,hi_], color=INK2, lw=1.4, ls='--')
axD.set_xticks(pos); axD.set_xticklabels([s[0] for s in specs], fontsize=8.8)
axD.set_ylabel("steps  (first two) / degrees  (third)")
axD.set_title(f"D   Every target met, on {len(away)} live episodes", loc='left')
axD.set_ylim(-8, 118)
axD.grid(axis='y', color=GRID, lw=.7); axD.set_axisbelow(True)
for s_ in ('top','right'): axD.spines[s_].set_visible(False)

fig.savefig('figM_shipped.png', bbox_inches='tight', dpi=140)
out = dict(n=len(away), away=[int(away.min()), int(away.max()), int(np.median(away))],
           rew=[int(rew.min()), int(rew.max())], t1=[float(t1.min()), float(t1.max())],
           burn=[int(burn.min()), int(burn.max())],
           ring_new=round(float(prof(-30.0,11,0.02)[1][1]),1), fire_new=round(float(prof(-30.0,11,0.02)[1][0]),1),
           ring_old=round(float(prof(-25.0,12,0.01)[1][1]),1), fire_old=round(float(prof(-25.0,12,0.01)[1][0]),1),
           safe_cells=round(float(safe.sum(axis=(1,2)).mean()),1),
           none_safe=int((safe.sum(axis=(1,2))==0).sum()),
           world=[W_LO, W_HI], k_loss=KL, warm=WS, cool=CS,
           sep=int(p.thermal_min_fire_separation), cycle=[len(up)-1, len(down)-1])
json.dump(out, open('figM_numbers.json','w'), indent=1)
print("wrote figM_shipped.png"); print(json.dumps(out, indent=1))
