"""FIGURE A1 — How long each agent survives, and what ends its episodes (Sensor Ladder figures 1 and 3).

WHAT IS PLOTTED. For every world and level, from the agent's own training world replayed for one
million episodes at its final checkpoint: mean survival in steps (top), and how the ways an episode
can end are redistributed by the modulator (bottom) -- the neuromodulated agent's share of episodes
ending each way MINUS the ordinary agent's. A positive bar means the modulated agent ends that way
more often. Survival, not reward, is the project's performance measure.

WHAT CLUE IT OFFERS. Whether the modulator changes what the agent dies of -- e.g. trading predator
deaths for starvation would suggest it hides at the expense of foraging -- and whether that shifts
at the thermal levels, where cold becomes a new way to die.

WHAT IT CANNOT SAY. One final checkpoint per run (the filtered 1M sample); Wave 1 levels 02/03 are
absent because their two agents trained for different lengths and their 1M stores are unmatched.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
COLS = [c for c in C.COLUMNS if c[0] == "blind" or c[1] >= 4]
OVEREAT = "over-eating"
CAUSE = [("starved", "starved", house.ORANGE), ("killed by predator", "died of injury", house.RED),
         ("frozen or overheated", "froze or overheated", house.BLUE), (OVEREAT, "over-ate", house.GREEN)]
fig, ax = plt.subplots(2, 1, figsize=(10.0, 7.2), sharex=True, gridspec_kw={"height_ratios": [1, 1.2]})
x = np.arange(len(COLS)); w = 0.2
missing = []
#: The ladder aggregate names four termination codes; over-eating (code 3, possible only since Wave 2)
#: arrives under its bare number. Mapped here by NAME rather than read as "3" in the drawing code.
OVEREAT = "over-eating"


def outcomes(d):
    t = {(OVEREAT if k == "3" else k): v for k, v in d["term_pct"].items()}
    tot = sum(t.values())
    assert abs(tot - 100.0) < 0.05, f"{d['arm']}: outcome shares sum to {tot:.2f}, not 100"
    return t


for i, (world, lvl) in enumerate(COLS):
    d = {arm: C.ladder(world, lvl, arm) for arm, _, _ in C.ARMS}
    if None in d.values():
        missing.append(i); continue
    for arm in d: d[arm] = dict(d[arm], term_pct=outcomes(d[arm]))
    for k, (arm, lab, col) in enumerate(C.ARMS):
        ax[0].plot(x[i] + (k - 0.5) * 0.18, d[arm]["mean_survival"], "o", ms=8, color=col,
                   label=lab if i == 0 else None)
    for j, (key, lab, col) in enumerate(CAUSE):
        g = d["modulated"]["term_pct"].get(key, 0.0) - d["control"]["term_pct"].get(key, 0.0)
        ax[1].bar(x[i] + (j - 1.5) * w, g, width=w, color=col, label=lab if i == 0 else None)
for i in missing:
    for a in ax:
        a.annotate("pending", xy=(x[i], 0.5), xycoords=("data", "axes fraction"), ha="center",
                   fontsize=10, color=house.TEXT_LIGHT)
ax[0].set_ylabel("mean survival (steps)"); ax[0].set_ylim(0, 520)
ax[0].set_title("survival, both agents", fontsize=10.5, color=house.INK, loc="left", pad=8)
ax[1].axhline(0, color=house.INK, lw=1)
ax[1].set_ylabel("neuromodulated − ordinary\n(% of episodes)")
ax[1].set_title("how episodes end: the modulator's shift", fontsize=10.5, color=house.INK, loc="left", pad=8)
ax[1].set_xticks(x); ax[1].set_xticklabels([C.col_label(*c) for c in COLS], fontsize=10)
for a in ax:
    a.axvline(0.5, color=house.RULE, lw=1)
    a.set_xlim(-0.6, len(COLS) - 0.4)   # every column, including ones still pending
h0 = ax[0].legend(loc="lower right", frameon=False, fontsize=house.FS_LABEL)
C.legend_below(ax[1], ncol=4, offset=-0.30)
fig.tight_layout(h_pad=1.8)
C.assert_ticks_dont_collide(ax[1]); C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("a1_outcomes", "observational")
C.record_samples("a1_outcomes", [
    dict(what="world × level cells", used=len(COLS) - len(missing), total=len(COLS),
         note="blind plus levels 04-06 of both waves; Wave 1 levels 02/03 excluded (unmatched training length)"),
    dict(what="episodes per agent per cell", used=1000000, total=1000000,
         note="the full final-checkpoint store, paired seeds across agents"),
    dict(what="checkpoints", used=1, total=5,
         note="final only: the filtered analyses need the 1M sample; coarse measures carry a late-checkpoint spread elsewhere")])
house.save(fig, os.path.join(C.FIG, "a1_outcomes"), column_px=C.COLUMN_PX)
print("missing:", [C.col_label(*COLS[i]).replace(chr(10), " ") for i in missing])
