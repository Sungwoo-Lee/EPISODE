"""Figure J — the body-temperature observation channel.

Panel A: where the channel sits in the observation vector, before and after.
Panel B: a worked walk from the cold ground into the comfort ring, showing what
         the new channel reports and how it differs from the thermoceptor.

Run: /home/vncuser/miniconda3/envs/grid_world_pain/bin/python figJ_obs.py
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from sim import gaussian_smooth, body_traj, H, W

SURF='#fcfcfb'; INK='#16181d'; INK2='#4e545e'; GRID='#e3e2de'
COLD='#2a78d6'; HOT='#b02b2b'; WARM='#eb6834'; OK='#0f7a55'; MUTE='#c3c6c2'
plt.rcParams.update({'figure.dpi':100,'figure.facecolor':SURF,'axes.facecolor':SURF,
 'savefig.facecolor':SURF,'text.color':INK,'axes.labelcolor':INK2,'xtick.color':INK2,
 'ytick.color':INK2,'axes.edgecolor':GRID,'font.size':10,'axes.titlesize':11,
 'axes.titleweight':'bold'})

K_EX, K_LOSS, SETPOINT = 0.04, 0.01, 0.0
DEFAULT, A_FIRE, SIGMA = -25.0, 300.0, 0.7

# ---- the field the walk happens in -------------------------------------------
raw = np.full((H, W), DEFAULT); raw[5, 5] += A_FIRE
FIELD = gaussian_smooth(raw, SIGMA)

# the agent walks in along a row toward the fire at (5,5), then stops at d=1
PATH = [(5, 0), (5, 1), (5, 2), (5, 3)] + [(5, 4)]*46      # d=5..1, then holds at d=1
DWELL_START = 4

# ---- Panel A data: the observation layout ------------------------------------
BEFORE = [("Satiation",1),("Intero Nocicept.",1),("Extero Nocicept.",1),
          ("Thermoception",5),("Olfaction",5),("Collision",5),
          ("Proprioception",6),("Visual",8)]
AFTER  = [("Satiation",1),("Body Temperature",1),("Intero Nocicept.",1),
          ("Extero Nocicept.",1),("Thermoception",5),("Olfaction",5),
          ("Collision",5),("Proprioception",6),("Visual",8)]

fig = plt.figure(figsize=(11.4, 8.6))
gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.22], hspace=0.40)

# ================= Panel A =====================================================
axA = fig.add_subplot(gs[0]); axA.set_xlim(0, 33); axA.set_ylim(-2.35, 3.45)
for s in axA.spines.values(): s.set_visible(False)
axA.set_yticks([]); axA.set_xticks(range(0, 34, 4))
axA.set_xlabel("position in the observation vector  (index, 0-based)")
axA.tick_params(axis='x', length=0)

def band(ax, blocks, y, h, hl=None, lab_y=None):
    """Draw one observation vector. Blocks >=4 wide are labelled inside; narrow
    ones are labelled above with a leader, because a 1-wide box cannot hold a name."""
    x = 0
    for name, w in blocks:
        is_new = (name == hl)
        ax.add_patch(Rectangle((x, y), w, h, facecolor=(OK if is_new else MUTE),
                               edgecolor=SURF, linewidth=1.6, zorder=2))
        ax.text(x + w/2, y + h/2, str(w), ha='center', va='center', zorder=3,
                fontsize=9, color='white',
                fontweight='bold' if is_new else 'normal')
        if w >= 4:
            ax.text(x + w/2, y + h + 0.09, name, ha='center', va='bottom',
                    fontsize=8.4, color=INK2, zorder=3)
        else:
            ax.plot([x + w/2, x + w/2], [y + h + 0.04, lab_y - 0.05],
                    color=(OK if is_new else GRID), lw=1.0, zorder=1)
            ax.text(x + w/2, lab_y, name, ha='left', va='bottom', rotation=32,
                    rotation_mode='anchor', fontsize=8.4, zorder=3,
                    color=(OK if is_new else INK2),
                    fontweight='bold' if is_new else 'normal')
        x += w

band(axA, BEFORE, 1.05, 0.50, lab_y=1.65)
band(axA, AFTER,  -1.75, 0.50, hl="Body Temperature", lab_y=-1.15)
axA.text(-0.5, 1.30, "today\n32 values", ha='right', va='center', fontsize=9.5, color=INK2)
axA.text(-0.5, -1.50, "with the\nchannel\n33 values", ha='right', va='center',
         fontsize=9.5, color=INK2)
axA.text(33, 3.20, "one value, inserted after Satiation — every block to its right shifts by one",
         fontsize=9, color=OK, va='center', ha='right')
axA.set_title("A   Where the channel sits.  Hunger is already delivered to the agent; body temperature is not.",
              loc='left', pad=12)

# ================= Panel B =====================================================
axB = fig.add_subplot(gs[1])
T = SETPOINT; body=[]; centre=[]; cell=[]; dist=[]
for (r, c) in PATH:
    f = float(FIELD[r, c])
    body.append(T); centre.append(f - T); cell.append(f)
    dist.append(abs(r-5)+abs(c-5))
    T = T + K_EX*(f - T) - K_LOSS*(T - SETPOINT)
steps = np.arange(len(PATH))

axB.axhspan(-15, 15, color=OK, alpha=0.07, zorder=0)
axB.axhline(0, color=INK2, lw=0.9, ls=(0, (4, 3)), zorder=1)
axB.axhline(15, color=HOT, lw=1.0, zorder=1); axB.axhline(-15, color=COLD, lw=1.0, zorder=1)
axB.plot(steps, body, color=OK, lw=2.6, zorder=4,
         label="Body Temperature — the NEW channel (raw degrees)")
axB.plot(steps, centre, color=WARM, lw=2.0, ls=(0, (5, 2)), zorder=3,
         label="Thermoception, centre cell — field minus body (today's only thermal reading)")
axB.plot(steps, cell, color=COLD, lw=1.5, ls=(0, (1.5, 2)), zorder=2,
         label="temperature of the cell the agent stands on (not observed)")

axB.text(len(PATH)+6.6, 15.9, "death, too hot  (+15)", color=HOT, fontsize=8.6,
         va='bottom', ha='right')
axB.text(len(PATH)+6.6, -15.9, "death, too cold  (−15)", color=COLD, fontsize=8.6,
         va='top', ha='right')
axB.text(len(PATH)+6.6, 0.9, "setpoint 0\ncomfortable", color=INK2, fontsize=8.4,
         ha='right', va='bottom', linespacing=1.3)
axB.axvline(DWELL_START, color=GRID, lw=1.2, zorder=1)
axB.text(len(PATH)+8.6, -29.4, "reaches the comfort ring (one cell from the fire) and stays",
         fontsize=8.6, color=INK2, va='bottom', ha='right')

for s, (ax_, ay_) in zip((0, 12, 40), ((6.0, -23.5), (13.5, 20.5), (36.0, 20.5))):
    axB.plot([s], [body[s]], 'o', ms=6.5, color=OK, zorder=5,
             markeredgecolor=SURF, markeredgewidth=1.4)
    axB.annotate(f"step {s}\nbody {body[s]:+.1f}\nthermoception {centre[s]:+.1f}",
                 xy=(s, body[s]), xytext=(ax_, ay_), fontsize=8.4,
                 color=INK2, linespacing=1.4, zorder=6, ha='left', va='center',
                 bbox=dict(boxstyle='round,pad=0.32', fc=SURF, ec=GRID, lw=0.8),
                 arrowprops=dict(arrowstyle='-', color=INK2, lw=0.9,
                                 shrinkA=2, shrinkB=4))

axB.set_xlim(-1.5, len(PATH)+9); axB.set_ylim(-31, 26)
axB.set_xlabel("step within the episode  (one environment step per unit)")
axB.set_ylabel("temperature  (raw degrees, setpoint = 0)")
axB.grid(axis='y', color=GRID, lw=0.7, zorder=0)
for s in ('top','right'): axB.spines[s].set_visible(False)
axB.legend(loc='upper center', bbox_to_anchor=(0.5, -0.17), frameon=False,
           fontsize=8.8, ncol=1, handlelength=2.6)
axB.set_title("B   The two readings are different quantities, and neither replaces the other.",
              loc='left', pad=10)

fig.savefig('figJ_obs.png', bbox_inches='tight', dpi=140)
print("wrote figJ_obs.png")
for s in (0, 12, 40):
    print(f"  step {s:2d}: body {body[s]:+7.2f}  thermo_centre {centre[s]:+7.2f}  "
          f"cell {cell[s]:+7.2f}  sum {centre[s]+body[s]:+7.2f}  d={dist[s]}")
