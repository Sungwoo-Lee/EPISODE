"""FIGURE S4 — Maps of the best choice: food energy x injury, at three body temperatures.

Rows: today's level 05 (with B1) and the worlds ranked highest by the reading rule (passing worlds
first, by combination gain; if fewer than three pass, the next-highest by combination gain, labelled
"does not pass"). Columns: body temperature -8, -3 and +3 deg. Each cell: the ideal planner's best
choice at open ground on the map without a warm bush (the more common map, 59 % of episodes); pale
cells are ties (best and second-best choice within 0.5 return units). A map whose colour boundaries
run diagonally, or move between columns, is one where the best choice depends on combinations.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, to_rgb
import _common as C, planner as PL

house = C.house; house.apply()
rule = json.load(open(os.path.join(C.OUT, "reading_rule.json")))
rows = [k for k in rule if k != "_meta"]
passing = sorted([k for k in rows if rule[k]["passes"]], key=lambda k: -rule[k]["combination_gain"])
others = sorted([k for k in rows if not rule[k]["passes"] and rule[k]["group"] != "baseline"],
                key=lambda k: -rule[k]["combination_gain"])
chosen = ["baseline__level 05__today"] + (passing + others)[:3]
TEMPS = (-8.0, -3.0, 3.0)
GN, GI, GT = PL.grids(PL.World())
cmap = ListedColormap([C.CHOICE_COLOURS[c] for c in PL.CATEGORIES])
fig, ax = plt.subplots(len(chosen), len(TEMPS), figsize=(10.0, 2.3 * len(chosen) + 1.0), sharex=True, sharey=True,
                       squeeze=False)
samples = []
for r, name in enumerate(chosen):
    z = np.load(os.path.join(C.SWEEP, f"{name}.npz"))
    cat = z["cat_warm0"].reshape(len(GN), len(GI), len(GT)); tie = z["tie_warm0"].reshape(cat.shape)
    info = rule[name]
    title = "today" if info["group"] == "baseline" else f"{info['group']}: {info['label']} = {info['value']:g}"
    if info["group"] != "baseline" and not info["passes"]:
        title += " (does not pass)"
    for j, t in enumerate(TEMPS):
        k = int(np.argmin(np.abs(GT - t)))
        img = cmap(cat[:, :, k].T.astype(float) / (len(PL.CATEGORIES) - 1))
        img[..., :3] = np.where(tie[:, :, k].T[..., None], 1 - 0.45 * (1 - img[..., :3]), img[..., :3])
        ax[r, j].imshow(img, origin="lower", aspect="auto", extent=(GN[0], GN[-1], GI[0], GI[-1]), interpolation="nearest")
        if r == 0:
            ax[r, j].set_title(f"body temperature {t:+g} deg", loc="left", fontsize=10)
        ax[r, j].grid(False)
    ax[r, 0].set_ylabel("injury"); ax[r, 0].text(0.0, 1.04, title, transform=ax[r, 0].transAxes, fontsize=9.5,
                                                  color=house.INK, va="bottom") if r > 0 else None
    samples.append(dict(what=title, used=int(cat.size), total=int(cat.size), note="grid states, map without a warm bush"))
for j in range(len(TEMPS)):
    ax[-1, j].set_xlabel("food energy")
fig.tight_layout(h_pad=1.8, w_pad=0.6, rect=(0, 0.05, 1, 1))
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color=C.CHOICE_COLOURS[c], label=c) for c in PL.CATEGORIES], loc="lower center",
           ncol=4, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=9.5)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("s4_choice_maps", "planner")
C.record_samples("s4_choice_maps", samples)
house.save(fig, os.path.join(C.FIG, "s4_choice_maps"), column_px=C.COLUMN_PX)
print("rows:", chosen)
