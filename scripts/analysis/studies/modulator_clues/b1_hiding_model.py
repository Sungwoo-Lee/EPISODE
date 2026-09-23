"""FIGURE B1 — Which factors drive hiding, and does the modulator re-weight them? ("What makes this agent hide?")

WHAT IS FITTED. For each agent and world, one regression over a million episodes: the share of the
episode spent in a bush, predicted jointly by everything fixed at the episode's start -- the agent's
starting injury and fullness, and how many predators, rabbits, bushes, rocks and food items the world
spawned, plus how far the agent started from a bush. Fitting them together means each effect is
adjusted for the others: an injury effect cannot be a predator effect in disguise. The effect shown
is in percentage points of hiding per one standard deviation of that factor. The smell panel uses
the same model restricted to episodes with exactly one predator and one rabbit, which adds how
predator-like each animal smells.

HOW TO READ A CELL. The large number is the neuromodulated agent's effect MINUS the ordinary agent's.
The small line gives the two agents' own effects (ordinary / neuromodulated). Colour follows the gap.

A CAVEAT THAT DIFFERS BY COLUMN. Fullness is fitted as a straight line. In the blind world and Wave 1,
more food is always better, so a line is right. In Wave 2 the body has a target in the MIDDLE of its
range, so fullness can be too low or too high and a straight line averages the two sides away. Read
the Wave 2 fullness row as unreliable.
"""
import sys, os, csv; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
COLS = [c for c in C.COLUMNS if c[0] == "blind" or c[1] >= 4]
M1 = "M1 exogenous, all episodes"; M3 = "M3 + rabbit smell, 1 predator + 1 rabbit"
TERMS = [(M1, "start_injury", "starting injury"), (M1, "start_nutrition", "starting fullness"),
         (M1, "n_predators", "number of predators"), (M1, "n_rabbits", "number of rabbits"),
         (M1, "n_bushes", "number of bushes"), (M1, "n_food", "number of food items"),
         (M1, "spawn_dist_to_bush", "start distance to a bush"),
         (M3, "pred_smell_predatorness", "predator smells predator-like"),
         (M3, "rab_smell_predatorness", "rabbit smells predator-like")]


N3 = []   # episode count behind each smell-row fit, read from the fit itself


def glm(world, lvl, arm):
    if world == "blind":
        p = os.path.join(C.A, "nmn_olf_gae_grid/glm", "t1none" if arm == "control" else "t16quad_ALL", "multivariate.csv")
    else:
        p = os.path.join(C.INT, "glm", f"{world}_lvl{lvl:02d}_{arm}", "multivariate.csv")
    if not os.path.exists(p):
        return None
    rows = list(csv.DictReader(open(p)))
    N3.append(next(int(r["n"]) for r in rows if r["model"] == M3 and r["term"] == "const"))
    return {(r["model"], r["term"]): float(r["dpp_per_sd"]) for r in rows}


G = np.full((len(TERMS), len(COLS)), np.nan); RAW = {}
for j, (world, lvl) in enumerate(COLS):
    d = {arm: glm(world, lvl, arm) for arm, _, _ in C.ARMS}
    if None in d.values():
        continue
    for i, (m, t, _) in enumerate(TERMS):
        a, b = d["control"].get((m, t)), d["modulated"].get((m, t))
        if a is None or b is None:
            continue
        G[i, j] = b - a; RAW[(i, j)] = (a, b)
lim = max(3.0, np.nanmax(np.abs(G)) if np.isfinite(G).any() else 3.0)
fig, ax = plt.subplots(figsize=(10.0, 6.4))
ax.imshow(G, cmap="RdBu_r", vmin=-lim, vmax=lim, aspect="auto")
for i in range(len(TERMS)):
    for j in range(len(COLS)):
        if np.isnan(G[i, j]):
            ax.text(j, i, "pending" if (i, j) not in RAW else "—", ha="center", va="center",
                    fontsize=9.6, color=house.TEXT_LIGHT); continue
        a, b = RAW[(i, j)]
        ax.text(j, i, f"{G[i, j]:+.1f}\n{a:+.1f} / {b:+.1f}", ha="center", va="center", fontsize=9.6,
                color="white" if abs(G[i, j]) > 0.62 * lim else house.INK)
ax.set_xticks(range(len(COLS))); ax.set_xticklabels([C.col_label(*c) for c in COLS], fontsize=10)
ax.xaxis.tick_top()
ax.set_yticks(range(len(TERMS))); ax.set_yticklabels([n for _, _, n in TERMS], fontsize=10)
ax.axvline(0.5, color="white", lw=3); ax.axhline(6.5, color="white", lw=3)
ax.grid(False)
fig.suptitle("Effect on hiding, pp per standard deviation. Big number: neuromodulated − ordinary; small: ordinary / neuromodulated. Below the line: 1 predator + 1 rabbit episodes.",
             fontsize=9.6, color=house.INK_2, x=0.005, ha="left", y=0.01, va="bottom", wrap=True)
fig.tight_layout(rect=(0, 0.05, 1, 1))
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("b1_hiding_model", "observational")
C.record_samples("b1_hiding_model", [
    dict(what="world × level cells fitted", used=int(np.isfinite(G[0]).sum()), total=len(COLS),
         note="blind plus levels 04-06 of both waves; Wave 1 levels 02/03 excluded (unmatched training length)"),
    dict(what="episodes per upper-row fit", used=1000000, total=1000000, note="every episode of the final-checkpoint store"),
    dict(what="episodes per smell-row fit (smallest cell)", used=min(N3), total=1000000,
         note="only episodes with exactly one predator and one rabbit carry both smell terms"),
    dict(what="checkpoints", used=1, total=5, note="final only — this regression needs the 1M sample")])
house.save(fig, os.path.join(C.FIG, "b1_hiding_model"), column_px=C.COLUMN_PX)
print(np.round(G, 2))
