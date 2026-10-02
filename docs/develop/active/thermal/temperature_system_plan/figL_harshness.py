"""Figure L — how harsh is the cold? World temperature x fire temperature x time scale.

Every validity verdict comes from the environment's OWN load-time check
(config_loader._thermal_radial_equilibria + _thermal_structure_verdict), so a cell
marked invalid is a config the loader would actually refuse — not an opinion.

Run: /home/vncuser/miniconda3/envs/grid_world_pain/bin/python figL_harshness.py
"""
import os, sys, json
os.environ.setdefault("JAX_PLATFORMS", "cpu")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."]*5))
sys.path.insert(0, ROOT)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
from src.environment.config_loader import _thermal_radial_equilibria, _thermal_structure_verdict

SURF='#fcfcfb'; INK='#16181d'; INK2='#4e545e'; GRID='#e3e2de'
COLD='#2a78d6'; HOT='#b02b2b'; WARM='#eb6834'; OK='#0f7a55'; PUR='#4a3aa7'
plt.rcParams.update({'figure.dpi':140,'figure.facecolor':SURF,'axes.facecolor':SURF,
 'savefig.facecolor':SURF,'text.color':INK,'axes.labelcolor':INK2,'xtick.color':INK2,
 'ytick.color':INK2,'axes.edgecolor':GRID,'font.size':9.5,'axes.titlesize':10.5,
 'axes.titleweight':'bold'})

H = W = 10; SIGMA, KR = 0.7, 3; LO, HI = -15.0, 15.0
K_EX, K_LOSS = 0.04, 0.01
SHIP_WORLD, SHIP_RATIO = -25.0, 12.0

# ---- obligations the thermal clock competes with (live config values) --------
def heal_steps(inj, base=0.1, acc=0.5):
    s=0.0; n=0
    while s < inj: n+=1; s += base*(1+acc)**(n-1)
    return n
HEAL_FULL = heal_steps(100)          # 16: uninterrupted rest to heal from 100 injury
WALK = 3                             # typical steps from safety to a bush / food
HIDE_HEAL_TRIP = HEAL_FULL + 2*WALK  # 22: walk out, heal hidden in the cold, walk back

def sim(T0, amb, kx, kl, stop, cap=5000):
    T = T0
    for n in range(1, cap):
        T = T + kx*(amb - T) - kl*T
        if stop(T): return n
    return None

def evaluate(world, ratio, kx=K_EX, kl=K_LOSS):
    eq = _thermal_radial_equilibria(ratio*abs(world), world, SIGMA, KR, H, W, kx, kl, 0.0, 0.0)
    ok, fails = _thermal_structure_verdict(eq, LO, HI)
    d0, d1 = eq[0], eq[1]
    away   = sim(d1, world, kx, kl, lambda T: T <= LO)
    burn   = sim(d1, d0*(kx+kl)/kx, kx, kl, lambda T: T >= HI)
    rewarm = sim(LO+1, d1*(kx+kl)/kx, kx, kl, lambda T: T >= 0.0) if d1 > 0 else None
    reason = ('valid' if ok else
              'fire harmless' if any('does not hurt' in f for f in fails) else
              'no comfort ring' if any('no comfort ring' in f for f in fails) else
              'cold harmless')
    return dict(ok=ok, reason=reason, d0=d0, d1=d1, away=away, burn=burn, rewarm=rewarm)

WORLDS = np.arange(-40, -13, 1.0)
RATIOS = np.arange(4, 21, 1.0)
grid = [[evaluate(float(w), float(r)) for w in WORLDS] for r in RATIOS]

CAP = 150
def arr(key, cap=CAP):
    a = np.full((len(RATIOS), len(WORLDS)), np.nan)
    for i in range(len(RATIOS)):
        for j in range(len(WORLDS)):
            g = grid[i][j]
            if g['ok'] and g[key] is not None: a[i, j] = min(g[key], cap)
    return a
REASONS = ['valid', 'cold harmless', 'no comfort ring', 'fire harmless']
reason_idx = np.array([[REASONS.index(grid[i][j]['reason']) for j in range(len(WORLDS))]
                       for i in range(len(RATIOS))])

fig = plt.figure(figsize=(13.8, 10.4))
gs = fig.add_gridspec(2, 2, hspace=0.36, wspace=0.26)
ext = [WORLDS[0]-.5, WORLDS[-1]+.5, RATIOS[0]-.5, RATIOS[-1]+.5]

def ship(ax):
    ax.plot(SHIP_WORLD, SHIP_RATIO, marker='*', ms=15, color='white', mec=INK, mew=1.3, zorder=5)
    ax.annotate('shipped', (SHIP_WORLD, SHIP_RATIO), xytext=(SHIP_WORLD-7.5, SHIP_RATIO+3.2),
                fontsize=8.6, color=INK, fontweight='bold',
                arrowprops=dict(arrowstyle='-', color=INK, lw=0.9))

# ---- A: where the design is valid at all -------------------------------------
axA = fig.add_subplot(gs[0, 0])
cm = ListedColormap(['#d9ece3', '#dce8f7', '#f4e3cf', '#f3dada'])
axA.imshow(reason_idx, origin='lower', extent=ext, aspect='auto', cmap=cm,
           norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5], 4), interpolation='nearest')
for k, (lab, col) in enumerate(zip(['valid — fire hurts, ring is safe, cold kills',
                                    'cold never kills (loader refuses)',
                                    'no survivable ring (loader refuses)',
                                    'fire does not hurt (loader refuses)'],
                                   ['#d9ece3','#dce8f7','#f4e3cf','#f3dada'])):
    axA.plot([], [], 's', ms=10, color=col, mec=GRID, label=lab)
axA.legend(frameon=False, fontsize=8.0, loc='upper center', bbox_to_anchor=(0.5, -0.13), ncol=2)
ship(axA)
axA.set_xlabel("world baseline temperature  (degrees; colder to the left)")
axA.set_ylabel("fire strength  (multiple of the world's coldness)")
axA.set_title("A   Where the design holds at all — per the loader's own check", loc='left')

# ---- B: away budget over the valid region ------------------------------------
axB = fig.add_subplot(gs[0, 1])
aw = arr('away')
im = axB.imshow(aw, origin='lower', extent=ext, aspect='auto', cmap='viridis', vmin=0, vmax=CAP)
cs = axB.contour(WORLDS, RATIOS, aw, levels=[HIDE_HEAL_TRIP, 2*HIDE_HEAL_TRIP, 3*HIDE_HEAL_TRIP],
                 colors=['white'], linewidths=1.3, linestyles=['--','-','-'])
axB.clabel(cs, fmt={HIDE_HEAL_TRIP:f'{HIDE_HEAL_TRIP}', 2*HIDE_HEAL_TRIP:f'{2*HIDE_HEAL_TRIP}',
                    3*HIDE_HEAL_TRIP:f'{3*HIDE_HEAL_TRIP}'}, fontsize=8.2, colors='white')
cb = fig.colorbar(im, ax=axB, pad=0.02); cb.set_label("steps away before cold death")
ship(axB)
axB.set_xlabel("world baseline temperature  (degrees; colder to the left)")
axB.set_ylabel("fire strength  (multiple of the world's coldness)")
axB.set_title("B   The away budget is set mostly by the world, a little by the fire", loc='left')
axB.text(WORLDS[0]+0.3, RATIOS[-1]-0.3,
         f"white lines: 1, 2, 3 hide-and-heal trips ({HIDE_HEAL_TRIP} steps each)\nblank: the loader refuses this config",
         fontsize=8.0, color=INK, va='top',
         bbox=dict(boxstyle='round,pad=0.3', fc=SURF, ec=GRID, lw=0.8))

# ---- C: slice at the shipped fire strength — the knife edge -------------------
axC = fig.add_subplot(gs[1, 0])
ws = np.arange(-40, -13, 0.5)
sl = [evaluate(float(w), SHIP_RATIO) for w in ws]
ys = [min(s['away'], CAP) if (s['ok'] and s['away']) else np.nan for s in sl]
axC.plot(ws, ys, color=COLD, lw=2.4, label='away budget (steps)')
inv = [w for w, s in zip(ws, sl) if not s['ok']]
if inv: axC.axvspan(min(inv)-0.25, max(inv)+0.25, color='#dce8f7', zorder=0)
axC.text((min(inv)+max(inv))/2 if inv else -16, CAP*0.55, "loader refuses:\ncold never kills",
         ha='center', fontsize=8.4, color=COLD)
for n, ls in ((1, '--'), (2, '-'), (3, '-')):
    axC.axhline(n*HIDE_HEAL_TRIP, color=INK2, lw=1.1, ls=ls)
    axC.text(-39.6, n*HIDE_HEAL_TRIP+(6.0 if n == 1 else 2.5), f"{n} hide-and-heal trip{'s' if n>1 else ''}", color=INK2, fontsize=8.2)
axC.axvline(SHIP_WORLD, color=INK2, lw=1.3)
axC.text(SHIP_WORLD+0.3, CAP*0.88, "shipped −25", color=INK2, fontsize=8.4, fontweight='bold')
axC.set_xlim(-40, -14); axC.set_ylim(0, CAP*1.04)
axC.set_xlabel("world baseline temperature  (degrees; fire strength fixed at the shipped 12x)")
axC.set_ylabel("steps away from the fire before cold death")
axC.set_title("C   Warming the world is a knife edge, not a dial", loc='left')
axC.grid(color=GRID, lw=.7); axC.set_axisbelow(True)
for s in ('top','right'): axC.spines[s].set_visible(False)

# ---- D: the time-scale lever --------------------------------------------------
axD = fig.add_subplot(gs[1, 1])
scales = np.array([1.0, 0.85, 0.75, 0.65, 0.5, 0.4, 0.33, 0.25])
lev = [evaluate(SHIP_WORLD, SHIP_RATIO, K_EX*s, K_LOSS*s) for s in scales]
axD.plot(scales, [l['away'] for l in lev],   color=COLD, lw=2.4, marker='o', ms=4, label='away budget — steps to cold death')
axD.plot(scales, [l['rewarm'] for l in lev], color=WARM, lw=2.2, marker='o', ms=4, label='rewarm — near-death back to comfortable')
axD.plot(scales, [l['burn'] for l in lev],   color=HOT,  lw=2.2, marker='o', ms=4, label='fire pain — steps on the fire to heat death')
for n, ls in ((1,'--'),(2,'-')):
    axD.axhline(n*HIDE_HEAL_TRIP, color=INK2, lw=1.1, ls=ls)
    axD.text(0.235, n*HIDE_HEAL_TRIP+2.5, f"{n} hide-and-heal trip{'s' if n>1 else ''}", color=INK2, fontsize=8.2)
axD.axhline(3, color=HOT, lw=0.9, ls=':')
axD.text(0.235, 5.0, "predator strike delay 1–3 steps", color=HOT, fontsize=8.0)
axD.invert_xaxis()
axD.set_xlabel("time scale  (k_exchange and k_loss both multiplied by this; 1.0 = shipped)")
axD.set_ylabel("steps")
axD.set_title("D   Slowing both rates stretches time and keeps the map", loc='left')
axD.legend(frameon=False, fontsize=8.2, loc='upper left')
axD.grid(color=GRID, lw=.7); axD.set_axisbelow(True); axD.set_ylim(0, 150)
for s in ('top','right'): axD.spines[s].set_visible(False)

fig.savefig('figL_harshness.png', bbox_inches='tight', dpi=140)

# ---- the numbers the page quotes, emitted rather than typed ------------------
valid = [(w, r) for i, r in enumerate(RATIOS) for j, w in enumerate(WORLDS) if grid[i][j]['ok']]
OUT = dict(
    heal_full=HEAL_FULL, walk=WALK, hide_heal_trip=HIDE_HEAL_TRIP,
    n_cells=int(len(WORLDS)*len(RATIOS)), n_valid=len(valid),
    warmest_valid_world=float(max(w for w, _ in valid)),
    lever=[dict(scale=float(s), k_ex=round(K_EX*s, 4), k_loss=round(K_LOSS*s, 5),
                ring=round(l['d1'], 2), fire=round(l['d0'], 1),
                away=l['away'], rewarm=l['rewarm'], burn=l['burn'], ok=l['ok'])
           for s, l in zip(scales, lev)],
    slice=[dict(world=float(w), away=s['away'], ok=s['ok']) for w, s in zip(ws, sl)],
)
json.dump(OUT, open('figL_numbers.json', 'w'), indent=1)
print("wrote figL_harshness.png + figL_numbers.json")
print(f"valid configs: {OUT['n_valid']} of {OUT['n_cells']}; warmest valid world: {OUT['warmest_valid_world']}")
print(f"obligations: full heal {HEAL_FULL} steps; hide-and-heal trip {HIDE_HEAL_TRIP}")
for l in OUT['lever']:
    print(f"  scale {l['scale']:4}: away {l['away']:>4}  rewarm {l['rewarm']:>3}  burn {l['burn']:>3}  "
          f"ring {l['ring']:+.2f}  fire {l['fire']:+.1f}  valid {l['ok']}")
print("slice near the edge:", [(d['world'], d['away'], d['ok']) for d in OUT['slice'] if -22 <= d['world'] <= -17])
