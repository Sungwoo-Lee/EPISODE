"""FIGURE D3 — Hypervigilance in controlled scenes: does an injured start make the agent avoid a rabbit more?

WHAT IS PLOTTED. Two fixed test scenes each containing only a harmless rabbit -- one that chases the
agent (moving exactly like a predator) and one that wanders -- each run twice: with the agent starting
uninjured, and with it starting at injury 70. Everything else is identical, so the injured-minus-
uninjured difference is caused by the injury. Two avoidance measures: time in the bush, and time with
the rabbit within reach. Each is averaged over the last 20 saved checkpoints of one training run.

WHICH WORLDS. Level 04 (Wave 2; its scenes use a bush that blocks animals, as in training) and levels 05
and 06 (Wave 2), whose agents freeze in a scene with no fire, so they were run in four survivable
temperature versions; for those, the dot is the median of the four and the bar their range. Wave 1's
animal scenes predate the bush fix and are not used.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house, window_profile as W

house.apply()
EV = os.path.join(C.ROOT, "results/eval/avoidance")
SETS = [("level 04", "lvl04", [os.path.join(EV, "metrics_history_rppo_basicq2_wave2_blocking_bush")]),
        ("level 05", "lvl05", [os.path.join(EV, f"metrics_history_rppo_thermalprobe_{a}_clean")
                               for a in ("neutral", "cool", "fire_by_bush", "fire_away")]),
        ("level 06", "lvl06", [os.path.join(EV, f"metrics_history_rppo_thermalprobe_{a}_clean")
                               for a in ("neutral", "cool", "fire_by_bush", "fire_away")])]
# the empty scene is the REFERENCE: an injured agent hides more anyway, to heal, rabbit or not
SCENES = [("avoid_none", "no animal (reference)"), ("avoid_rabbit", "chasing rabbit"), ("avoid_rabbitwander", "wandering rabbit")]
MEAS = [("bush_hiding", "time in the bush"), ("time_near_animal", "time with the rabbit within reach")]


def shift(O, lvl, arm, scene, m):
    _, a = W.read_series(O, f"{lvl}_{arm}", f"{scene}_inj70", m)
    _, b = W.read_series(O, f"{lvl}_{arm}", f"{scene}_inj00", m)
    return a[-20:].mean() - b[-20:].mean()          # read_series already returns percent


rows = [(f"{sname}, {wname}", lvl, dirs, scene) for wname, lvl, dirs in SETS for scene, sname in SCENES]
fig, ax = plt.subplots(1, 2, figsize=(10.0, 6.4), sharey=True)
y = np.arange(len(rows))[::-1]; out = {}
for p, (m, title) in enumerate(MEAS):
    for i, (lab, lvl, dirs, scene) in enumerate(rows):
        for k, (arm, alab, col) in enumerate(C.ARMS):
            v = np.array([shift(O, lvl, arm, scene, m) for O in dirs]); yy = y[i] + (0.5 - k) * 0.3
            if v.size > 1:
                ax[p].plot([v.min(), v.max()], [yy, yy], color=col, lw=3, alpha=0.35, solid_capstyle="round")
            ax[p].plot([np.median(v)], [yy], "o", ms=7.5, color=col, label=alab if (p == 0 and i == 0) else None)
            out[(m, lab, arm)] = v
    ax[p].axvline(0, color=house.INK, lw=1); ax[p].grid(axis="y", visible=False)
    ax[p].set_title(title, fontsize=10.5, color=house.INK, loc="left", pad=8)
    ax[p].set_xlabel("injured start − uninjured start (pp)")
ax[0].set_yticks(y); ax[0].set_yticklabels([r[0] for r in rows], fontsize=10)
C.legend_below(ax[0], ncol=2, offset=-0.17)
fig.tight_layout(w_pad=1.4)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("d3_rabbit_scenes", "scene")
C.record_samples("d3_rabbit_scenes", [
    dict(what="checkpoints per value", used=20, total=50, note="the newest 20 of each run's 50"),
    dict(what="episodes per checkpoint per scene", used=30, total=30, note="fixed seeds, both agents, both injury starts"),
    dict(what="temperature versions at levels 05/06", used=4, total=4, note="median shown, range as the bar"),
    dict(what="worlds", used=1, total=3, note="Wave 2 only; Wave 1's animal scenes predate the bush fix, the blind world has none")])
house.save(fig, os.path.join(C.FIG, "d3_rabbit_scenes"), column_px=C.COLUMN_PX)
for k, v in out.items(): print(f"  {k[0]:17} {k[1]:30} {k[2]:9} median {np.median(v):+6.1f}  range [{v.min():+6.1f},{v.max():+6.1f}]")
