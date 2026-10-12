"""FIGURE A1 -- How do trained agents' episodes end, level by level?

One bar per trained agent (Wave-2 trajectory stores, 1,000,000 evaluation episodes each): the share of
episodes that survive the 500-step cap, or end by starvation, injury (any source: predator, trap, rock),
cold or over-eating. x: share of episodes (%); y: level and agent. "Old level 06" is today's level 07
(the stores predate the 2026-09-30 renumbering).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _deaths as Dd

house = C.house; house.apply()
D = Dd.deaths(); S = Dd.wave2()
KEYS = [("survived", "max_steps"), ("starvation", "starvation"), ("injury", "injury"), ("cold", "thermal"),
        ("over-eating", "overeating")]
# endings below 0.05 % of every agent's episodes are invisible as a bar segment; they are listed in the
# data statement instead of the legend (over-eating: a handful of episodes in 9 M)
TINY = [k for k in KEYS if max(D[s]["reasons"].get(k[1], 0) / D[s]["episodes"] for s, _, _ in S) < 5e-4]
KEYS = [k for k in KEYS if k not in TINY]
fig, ax = plt.subplots(figsize=(8.6, 4.8))
y = np.arange(len(S))[::-1].astype(float)
left = np.zeros(len(S))
for name, key in KEYS:
    v = np.array([100.0 * D[s]["reasons"].get(key, 0) / D[s]["episodes"] for s, _, _ in S])
    col = C.DEATH_COLOURS[name]
    ax.barh(y, v, left=left, color=col, height=0.66, label=C.DEATH_LABEL[name], edgecolor=house.PAPER, lw=0.6)
    for yy, l0, vv in zip(y, left, v):
        if vv >= 7:
            ax.text(l0 + vv / 2, yy, f"{vv:.0f}", ha="center", va="center", fontsize=9,
                    color=house.INK if name == "survived" else "white")
    left += v
ax.set_yticks(y); ax.set_yticklabels([f"{Dd.LEVEL_LABEL[l]} · {a}" for _, l, a in S])
ax.set_xlim(0, 100); ax.set_xlabel("share of episodes (%)"); ax.grid(axis="y", visible=False)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.legend(loc="lower center", ncol=len(KEYS), frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0))
C.finish(fig, "a1_endings_by_level", "recordings", [
    dict(what=f"{Dd.LEVEL_LABEL[l]}, {a} agent", used=D[s]["episodes"], total=D[s]["episodes"],
         note="every evaluation episode of the agent's Wave-2 trajectory store"
              + "".join(f"; {n}: {D[s]['reasons'].get(k, 0)} episode(s), too few to draw" for n, k in TINY))
    for s, l, a in S])
