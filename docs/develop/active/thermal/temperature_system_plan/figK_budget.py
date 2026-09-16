"""Figure K — how each thermal setting moves the agent's survival budget.

The question this answers: the temperature system imposes a clock. Is that clock
long enough to leave room for the agent's other jobs — foraging, hiding, healing?

Everything is computed from the same first-order body recurrence the environment
uses (sim.py), over fields built the same way jax_reset builds them.

Run: /home/vncuser/miniconda3/envs/grid_world_pain/bin/python figK_budget.py
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sim import gaussian_smooth, body_traj, H, W

SURF='#fcfcfb'; INK='#16181d'; INK2='#4e545e'; GRID='#e3e2de'
COLD='#2a78d6'; HOT='#b02b2b'; WARM='#eb6834'; OK='#0f7a55'; PUR='#4a3aa7'
plt.rcParams.update({'figure.dpi':140,'figure.facecolor':SURF,'axes.facecolor':SURF,
 'savefig.facecolor':SURF,'text.color':INK,'axes.labelcolor':INK2,'xtick.color':INK2,
 'ytick.color':INK2,'axes.edgecolor':GRID,'font.size':9.5,'axes.titlesize':10.5,
 'axes.titleweight':'bold'})

# ---- shipped values, resolved from the live config -------------------------
K_EX, K_LOSS, SETPOINT = 0.04, 0.01, 0.0
DEATH_COLD, DEATH_HOT = -15.0, 15.0
WORLD, RATIO, SIGMA = -25.0, 12.0, 0.7
SEP = 3
# the competing clocks
EPISODE, HUNGER_CLOCK, FOOD_VALUE = 500, 100.0, 6.0

rng = np.random.default_rng(7)
CAP = 240   # 'the cold never kills here' — plotted at the cap and annotated

def place_fires(n, rng, margin=2, sep=SEP, tries=400):
    """Fires inside the shipped spawn area, respecting min Manhattan separation."""
    for _ in range(tries):
        pts=[]
        for _ in range(n):
            for _ in range(60):
                r,c = rng.integers(margin,H-margin), rng.integers(margin,W-margin)
                if all(abs(r-a)+abs(c-b) >= sep for a,b in pts): pts.append((r,c)); break
        if len(pts)==n: return pts
    return None

def field_of(fires, world=WORLD, ratio=RATIO, sigma=SIGMA):
    raw = np.full((H,W), float(world))
    for (r,c) in fires: raw[r,c] += ratio*abs(world)
    return gaussian_smooth(raw, sigma)

def eq(f):  return (K_EX*f + K_LOSS*SETPOINT)/(K_EX+K_LOSS)

def survivable(fld):
    e = eq(fld)
    return (e >= DEATH_COLD) & (e <= DEATH_HOT)

def budget_from(start_T, ambient):
    """Steps standing in `ambient` before the body leaves the survivable band."""
    T = start_T
    for n in range(1, 5000):
        T = T + K_EX*(ambient-T) - K_LOSS*(T-SETPOINT)
        if T <= DEATH_COLD or T >= DEATH_HOT: return n
    return None

def metrics(fires, world=WORLD, ratio=RATIO, sigma=SIGMA, k_ex=None, k_loss=None):
    global K_EX, K_LOSS
    if k_ex is not None or k_loss is not None:
        oe, ol = K_EX, K_LOSS
        K_EX = k_ex if k_ex is not None else K_EX
        K_LOSS = k_loss if k_loss is not None else K_LOSS
    fld = field_of(fires, world, ratio, sigma)
    safe = survivable(fld)
    frac = float(safe.mean())*100
    if safe.any():
        _e = eq(fld)[safe]
        best = float(_e[np.argmin(np.abs(_e))])      # most comfortable survivable cell
        warmest = float(_e.max())                    # most runway a survivable cell can bank
        # walk home: Manhattan distance from each cell to the nearest survivable cell
        sr, sc = np.nonzero(safe)
        rr, cc = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
        d = np.abs(rr[...,None]-sr[None,None,:]) + np.abs(cc[...,None]-sc[None,None,:])
        home = d.min(axis=2)
        mean_home = float(home.mean()); far_home = float(np.percentile(home, 90))
    else:
        best, warmest, mean_home, far_home = np.nan, np.nan, np.nan, np.nan
    coldest = float(eq(fld).min())
    b = budget_from(best, coldest/ (K_EX/(K_EX+K_LOSS)) if False else fld.min()) if safe.any() else 0
    b_warm = budget_from(warmest, fld.min()) if safe.any() else 0
    out = dict(frac=frac, ring_eq=best, warm_eq=warmest, budget=(b or CAP),
               budget_warm=(b_warm or CAP), home=mean_home, home90=far_home)
    if k_ex is not None or k_loss is not None: K_EX, K_LOSS = oe, ol
    return out

def avg(n, **kw):
    rows=[metrics(place_fires(n, np.random.default_rng(s)), **kw) for s in range(24)]
    rows=[r for r in rows if r['ring_eq']==r['ring_eq']]
    return {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}

# =============================================================================
fig = plt.figure(figsize=(13.6, 8.8))
gs = fig.add_gridspec(2, 2, hspace=0.46, wspace=0.26)

# ---- A: the three clocks ----------------------------------------------------
axA = fig.add_subplot(gs[0,0])
base = avg(2)
clocks = [("episode length", EPISODE, GRID),
          ("hunger: full → starving", HUNGER_CLOCK, WARM),
          ("thermal: ring → dead in the cold", base['budget'], COLD)]
y = np.arange(len(clocks))[::-1]
for (lab,v,col), yy in zip(clocks, y):
    axA.barh(yy, v, color=col, height=0.55)
    axA.text(v+8, yy, f"{v:.0f} steps", va='center', fontsize=9.5, color=INK)
axA.set_yticks(y); axA.set_yticklabels([c[0] for c in clocks], fontsize=9)
axA.set_xlim(0, 585); axA.set_xlabel("steps")
axA.set_title("A   The three clocks the agent runs at once", loc='left')
axA.text(0, -0.92, f"Temperature is {HUNGER_CLOCK/base['budget']:.1f}x more urgent than hunger.\n"
         f"What that leaves room for is worked out in the table below, from this same budget.",
         fontsize=8.6, color=INK2, va='top', linespacing=1.5)
for s in ('top','right'): axA.spines[s].set_visible(False)

# ---- B: world coldness x fire strength -------------------------------------
axB = fig.add_subplot(gs[0,1])
worlds = np.arange(-40, -13, 2.0)
for ratio, col in ((8, '#9fc3ef'), (12, COLD), (16, PUR)):
    ys=[avg(2, world=float(w), ratio=ratio)['budget'] for w in worlds]
    axB.plot(worlds, ys, color=col, lw=2.2, marker='o', ms=3.5, label=f"fire ratio {ratio}x")
axB.axhline(HUNGER_CLOCK, color=WARM, ls=(0,(5,3)), lw=1.6)
axB.text(-26.0, HUNGER_CLOCK+4, "hunger clock (100)", color=WARM, fontsize=8.4, ha='right')
axB.axvline(WORLD, color=INK2, lw=1.4); axB.text(WORLD+0.4, 150, "shipped\n−25", color=INK2, fontsize=8.4, fontweight='bold')
axB.set_xlabel("world baseline temperature  (degrees; colder to the left)")
axB.set_ylabel("thermal budget  (steps from the ring to death)")
axB.set_title("B   A colder world shortens the clock; fire strength barely moves it", loc='left')
axB.legend(frameon=False, fontsize=8.4, loc='center left'); axB.grid(color=GRID, lw=.7); axB.set_axisbelow(True)
axB.set_ylim(0, CAP*1.06)
axB.axhline(CAP, color=INK2, lw=1.0, ls=':')
axB.text(-40, CAP-9, "above this line the cold never kills", fontsize=8.0,
         color=INK2, va='top', ha='left')
for s in ('top','right'): axB.spines[s].set_visible(False)

# ---- C: fire count ----------------------------------------------------------
axC = fig.add_subplot(gs[1,0])
ns = [1,2,3,4,5]
rows = [avg(n) for n in ns]
w=0.36
axC.bar(np.array(ns)-w/2, [r['frac'] for r in rows], w, color=OK, label="survivable share of the map (%)")
axC.set_ylabel("survivable share of the map  (%)", color=OK)
axC.tick_params(axis='y', colors=OK)
ax2 = axC.twinx()
ax2.bar(np.array(ns)+w/2, [r['home'] for r in rows], w, color=COLD,
        label="mean walk home (steps)")
ax2.set_ylabel("mean steps to the nearest safe cell", color=COLD)
ax2.tick_params(axis='y', colors=COLD)
axC.set_xticks(ns); axC.set_xlabel("number of campfires  (shipped range is 1–3)")
axC.set_title("C   More fires buy a shorter walk home, not a longer clock", loc='left')
axC.set_axisbelow(True)
h1,l1 = axC.get_legend_handles_labels(); h2,l2 = ax2.get_legend_handles_labels()
axC.legend(h1+h2, l1+l2, frameon=False, fontsize=8.4, loc='upper center', bbox_to_anchor=(0.5,-0.22))
for s in ('top',): axC.spines[s].set_visible(False); ax2.spines[s].set_visible(False)

# ---- D: the two rate constants ---------------------------------------------
axD = fig.add_subplot(gs[1,1])
kxs = np.linspace(0.01, 0.12, 23)
for kl, col, lab in ((0.005,'#9fc3ef','k_loss 0.005'),(0.01,COLD,'k_loss 0.01 (shipped)'),(0.02,PUR,'k_loss 0.02')):
    ys=[avg(2, k_ex=float(k), k_loss=kl)['budget'] for k in kxs]
    axD.plot(kxs, ys, color=col, lw=2.2, label=lab)
axD.axhline(HUNGER_CLOCK, color=WARM, ls=(0,(5,3)), lw=1.6)
axD.text(0.075, HUNGER_CLOCK+5, "hunger clock (100)", color=WARM, fontsize=8.4, ha='right')
axD.axvline(K_EX, color=INK2, lw=1.4); axD.text(K_EX+0.002, 168, "shipped\n0.04", color=INK2, fontsize=8.4, fontweight='bold')
axD.set_xlabel("k_exchange  (how fast the world gets into the body, per step)")
axD.set_ylabel("thermal budget  (steps)")
axD.set_title("D   The clock is set by the rate constants, not by the scenery", loc='left')
axD.legend(frameon=False, fontsize=8.4, loc='center right'); axD.grid(color=GRID, lw=.7); axD.set_axisbelow(True)
axD.set_ylim(0, CAP*1.06)
axD.axhline(CAP, color=INK2, lw=1.0, ls=':')
axD.text(0.119, CAP-9, "the cold never kills below this k_exchange", fontsize=8.0,
         color=INK2, va='top', ha='right')
for s in ('top','right'): axD.spines[s].set_visible(False)

fig.savefig('figK_budget.png', bbox_inches='tight', dpi=140)
print("wrote figK_budget.png\n")
print(f"{'fires':>6} {'safe%':>7} {'comfy':>7} {'budget':>7} | {'warmest':>8} {'budget':>7} | {'home':>5} {'window':>7}")
for n, r in zip(ns, rows):
    print(f"{n:>6} {r['frac']:>7.1f} {r['ring_eq']:>+7.1f} {r['budget']:>7.0f} | "
          f"{r['warm_eq']:>+8.1f} {r['budget_warm']:>7.0f} | {r['home']:>5.1f} "
          f"{r['budget_warm']-r['home']:>7.0f}")
print("\n'comfy' = the survivable cell nearest the setpoint (best drive).")
print("'warmest' = the warmest survivable cell (worse drive, more thermal runway).")
print("Waiting on the warmest cell before a trip BANKS heat: that is a state-dependent choice.")
