"""FIGURE A2 — Does being injured change behaviour more in the neuromodulated agent? (Sensor Ladder 8)

THE CAUSAL TEST. In most episodes an agent's injury is a consequence of what it did. But at levels
03-06 the environment hands the agent a random starting injury before it acts, so behaviour that
tracks THAT number is caused by it. Three measures, all on the first 25 steps of those episodes:
  * state span -- extra share of steps in a bush when badly hurt vs unhurt, nothing threatening;
  * threat trend -- how the extra hiding a nearby predator causes changes per step of injury;
  * entry change -- how the rate of STEPPING INTO cover (a decision, not a location) changes from
    least to most injured, with a predator near. Unlike the first two it cannot be inflated by a
    hurt agent freezing wherever it happens to be standing.

WHAT IS PLOTTED. Each measure as neuromodulated MINUS ordinary, per world and level. The dot is the
median over the five late checkpoints; the whisker is their full range, pairing the two agents'
checkpoints in order. This spread is policy drift WITHIN one training run -- not the gap between two
runs, which one seed per agent cannot estimate.

EMPTY CELLS. Level 02 never randomises the starting injury. The blind world has no late-checkpoint
stores (its saved config no longer loads), so it shows the final checkpoint only, without a range.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
COLS = [c for c in C.COLUMNS if c != ("w1", 2)]
MEAS = [("state span (pp)", lambda d: C.causal_metric(d, "state_span")),
        ("threat trend (pp per injury bin)", lambda d: C.causal_metric(d, "proximity_effect_trend_per_bin")),
        ("entry change (pp)", C.entry_change)]


def series(world, lvl, arm):
    """Checkpoint-ordered JSONs: the late stores, plus the final 1M store for full-length runs."""
    s = C.late(world, lvl, arm)
    if (world, lvl) not in C.MATCHED and world != "blind":
        f = C.context_final(world, lvl, arm)
        if f is not None: s = s + [f]
    if world == "blind":
        f = C.context_final(world, lvl, arm); s = [f] if f else []
    return s


fig, ax = plt.subplots(3, 1, figsize=(10.0, 7.6), sharex=True)
x = np.arange(len(COLS)); n_used = {}
for j, (world, lvl) in enumerate(COLS):
    sc, sm = series(world, lvl, "control"), series(world, lvl, "modulated")
    k = min(len(sc), len(sm)); n_used[(world, lvl)] = k
    for i, (name, f) in enumerate(MEAS):
        if k == 0:
            ax[i].annotate("pending", xy=(x[j], 0.5), xycoords=("data", "axes fraction"),
                           ha="center", fontsize=9.6, color=house.TEXT_LIGHT); continue
        g = np.array([f(sm[t]) - f(sc[t]) for t in range(k)], float)
        g = g[np.isfinite(g)]
        if not g.size: continue
        ax[i].plot([x[j], x[j]], [g.min(), g.max()], color=house.TEXT_LIGHT, lw=2.4, solid_capstyle="round")
        ax[i].plot([x[j]], [np.median(g)], "o", ms=8, color=C.GAP)
for i, (name, _) in enumerate(MEAS):
    ax[i].axhline(0, color=house.INK, lw=1); ax[i].axvline(0.5, color=house.RULE, lw=1)
    ax[i].set_ylabel(name, fontsize=10)
    ax[i].set_xlim(-0.6, len(COLS) - 0.4)
ax[0].set_title("neuromodulated − ordinary; dot = median of late checkpoints, bar = their range (one run)",
                fontsize=10, color=house.INK_2, loc="left", pad=8)
ax[2].set_xticks(x); ax[2].set_xticklabels([C.col_label(*c) for c in COLS], fontsize=10)
fig.tight_layout(h_pad=1.2)
C.assert_ticks_dont_collide(ax[2]); C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("a2_injury_dose", "causal")
C.record_samples("a2_injury_dose", [
    dict(what="world × level cells", used=sum(1 for v in n_used.values() if v), total=len(COLS),
         note="level 02 excluded (no random starting injury); Wave 2 levels 02/03 still training"),
    dict(what="checkpoints per Wave-1/2 cell", used=max(n_used.values()), total=5,
         note="five late checkpoints: four 100k stores plus the final 1M store, or five matched 100k stores"),
    dict(what="episodes per late checkpoint", used=100000, total=100000,
         note="enough for these coarse measures: they moved by 0.02-0.34 pp between 100k and 1M in a check"),
    dict(what="blind-world checkpoints", used=1, total=5, note="final only; its saved config no longer loads")])
house.save(fig, os.path.join(C.FIG, "a2_injury_dose"), column_px=C.COLUMN_PX)
print({f"{w}{l}": k for (w, l), k in n_used.items()})
