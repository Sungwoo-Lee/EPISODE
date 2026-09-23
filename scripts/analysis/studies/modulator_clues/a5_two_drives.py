"""FIGURE A5 — A wound says hide, hunger says forage: which steers more, and does the modulator shift the balance? (Sensor Ladder 13)

THE QUESTION. The agent carries internal states that pull in opposite directions: a wound argues for
staying in cover, an empty stomach for leaving it, since bushes hold no food. At levels 03-06 both are
handed out at random at the start of each episode, so each can be tested causally, on the same footing.

HOW IT IS COMPUTED. Over the first 25 steps of every episode (where the assigned values are still
largely intact), hiding is the share of steps on a bush, pooled within groups of episodes:
  * injury span: most-injured quarter of the starting injury (75-100) minus least (0-25);
  * hunger span: hiding when furthest BELOW the body's fullness target (75-100 below) minus when at it
    (0-25 below). Fullness is measured from each run's OWN target, because Wave 1's target is the top of
    a 0-100 range and Wave 2's is the middle of 0-200 -- fixed bins would compare different things;
  * over-full span (Wave 2 only, where being too full became possible): 25-100 ABOVE target minus at it.

WHAT CLUE IT OFFERS. Whether the modulator changes the relative pull of the two drives, and whether
the new over-full state in Wave 2 moves behaviour at all.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
COLS = [c for c in C.COLUMNS if c[0] == "blind" or c[1] >= 4]
TARGET = {"blind": 100.0, "w1": 100.0, "w2": 100.0}


def npz(world, lvl, arm):
    if world == "blind":
        p = os.path.join(C.A, "nmn_olf_gae_grid/ladderstyle",
                         f"{'t1none' if arm == 'control' else 't16quad_ALL'}_episodes.npz")
    else:
        p = os.path.join(C.INT, "ladderstyle", f"{world}_lvl{lvl:02d}_{arm}_episodes.npz")
    return np.load(p) if os.path.exists(p) else None


def spans(z, world):
    be, se = z["bush_early"].astype(float), z["steps_early"].astype(float)
    rate = lambda m: 100 * be[m].sum() / se[m].sum() if se[m].sum() > 5000 else np.nan
    inj = z["inj0"]; dev = z["nut0"] - TARGET[world]            # negative = below target
    inj_span = rate(inj >= 75) - rate(inj < 25)
    hunger = rate((dev <= -75) & (dev >= -100)) - rate((dev > -25) & (dev <= 0))
    over = rate((dev > 25) & (dev <= 100)) - rate((dev > -25) & (dev <= 0)) if world == "w2" else np.nan
    return inj_span, hunger, over


ROWS = ["injury span", "hunger span", "over-full span"]
V = {}
for j, (world, lvl) in enumerate(COLS):
    for arm, _, _ in C.ARMS:
        z = npz(world, lvl, arm)
        if z is not None: V[(j, arm)] = spans(z, world)
fig, ax = plt.subplots(3, 1, figsize=(10.0, 7.0), sharex=True)
x = np.arange(len(COLS))
for i, name in enumerate(ROWS):
    for k, (arm, lab, col) in enumerate(C.ARMS):
        ys = [V[(j, arm)][i] if (j, arm) in V else np.nan for j in range(len(COLS))]
        ax[i].plot(x + (k - 0.5) * 0.16, ys, "o", ms=8, color=col, label=lab if i == 0 else None)
    ax[i].axhline(0, color=house.INK, lw=1); ax[i].axvline(0.5, color=house.RULE, lw=1)
    ax[i].set_ylabel(f"{name}\n(pp)", fontsize=10); ax[i].set_xlim(-0.6, len(COLS) - 0.4)
ax[2].annotate("Wave 1 and blind: not possible", xy=(1.0, 0.82), xycoords=("data", "axes fraction"),
               fontsize=9.6, color=house.TEXT_LIGHT)
ax[0].set_title("change in hiding, first 25 steps of randomly-assigned episodes", fontsize=10, color=house.INK_2, loc="left", pad=8)
ax[2].set_xticks(x); ax[2].set_xticklabels([C.col_label(*c) for c in COLS], fontsize=10)
C.legend_below(ax[2], ncol=2, offset=-0.5)
fig.tight_layout(h_pad=1.0)
C.assert_ticks_dont_collide(ax[2]); C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("a5_two_drives", "causal")
C.record_samples("a5_two_drives", [
    dict(what="world × level cells", used=len({j for j, _ in V}), total=len(COLS),
         note="blind plus levels 04-06; Wave 1 levels 02/03 excluded (unmatched training length)"),
    dict(what="episodes per agent per cell", used=1000000, total=1000000, note="final-checkpoint store; every episode has a random start"),
    dict(what="steps per episode used", used=25, total=500, note="the first 25, while the assigned values are still intact"),
    dict(what="minimum steps per group", used=5000, total=5000, note="groups with fewer steps are left blank")])
house.save(fig, os.path.join(C.FIG, "a5_two_drives"), column_px=C.COLUMN_PX)
for (j, arm), v in sorted(V.items()):
    print(f"  {C.col_label(*COLS[j]).replace(chr(10),' '):18} {arm:9} inj {v[0]:+6.2f} hunger {v[1]:+6.2f} over {v[2]:+6.2f}")
