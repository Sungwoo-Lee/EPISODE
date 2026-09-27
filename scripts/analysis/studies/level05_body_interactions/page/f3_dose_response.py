"""FIGURE 3 — What the hiding curves behind measure 1 look like.

Share of decision steps spent in a bush (cover), per 10-point bin of TRUE injury (0-10 ... 90-100),
split by nutrition band (fed = nutrition >= 100, hungry = nutrition < 60, the same bands as measure 1),
for both agents, final-checkpoint recordings (1,000,000 evaluation episodes per run). A share is
drawn only where its bin holds >= 200 steps (dose_tables.json sets it to null otherwise).

Four worlds, chosen here from the data rather than by hand:
  plain level 05 (no rule on) and all four rules on, always; plus the two OTHER worlds with the
  largest |modulator - ordinary| on measure 1 (true injury), read from state_contrasts.json.
The chosen worlds and their gaps are written to the figure's data statement.
Measure 1 is read off these curves: (fed rise from injury 0-20 to 60-100) minus (hungry rise).
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _common as C

house = C.house; house.apply()
dt = C.load("dose_response/dose_tables.json")
sc = C.load("state_contrasts.json")["worlds"]
fixed = ["w0000", "w1111"]
rank = sorted((w for w in C.WORLDS if w not in fixed), key=lambda w: -abs(sc[w]["D_M1_true"]))
chosen = fixed + rank[:2]
assert dt["fed"][0] == 100.0 and dt["hungry"] == [0.0, 60.0], (dt["fed"], dt["hungry"])

STY = {("ordinary", "fed"): dict(color=house.INK, ls="-", marker="o", mfc=house.INK),
       ("ordinary", "hungry"): dict(color=house.INK, ls="--", marker="o", mfc="white"),
       ("modulated", "fed"): dict(color=C.GREY, ls="-", marker="s", mfc=C.GREY),
       ("modulated", "hungry"): dict(color=C.GREY, ls="--", marker="s", mfc="white")}
NAME = {"ordinary": "ordinary agent", "modulated": "modulator agent"}

fig, axs = plt.subplots(2, 2, figsize=(9.8, 7.6), sharex=True, sharey=True)
used = {}
for a, w in zip(axs.ravel(), chosen):
    for ag in ("ordinary", "modulated"):
        run = dt["runs"][f"{w}_{ag}"]; e = np.array(run["injury_edges"]); mid = (e[:-1] + e[1:]) / 2
        for band in ("fed", "hungry"):
            tb = run["tables"][f"cover|{band}"]
            s = np.array([np.nan if b["share"] is None else 100 * b["share"] for b in tb])
            used[(w, ag, band)] = (sum(b["n"] for b in tb if b["share"] is not None), sum(b["n"] for b in tb))
            st = STY[(ag, band)]
            a.plot(mid, s, color=st["color"], ls=st["ls"], lw=1.6, marker=st["marker"], ms=5,
                   mfc=st["mfc"], mec=st["color"], mew=1.2)
    for lo, hi in ((0, 20), (60, 100)):
        a.axvspan(lo, hi, color=house.BG_SOFT, lw=0, zorder=0)
    a.text(10, 84, "low injury", ha="center", va="top", fontsize=C.SMALLEST_PT, color=house.INK_2, path_effects=house.halo(house.BG_SOFT))
    a.text(80, 84, "high injury", ha="center", va="top", fontsize=C.SMALLEST_PT, color=house.INK_2, path_effects=house.halo(house.BG_SOFT))
    d = 100 * sc[w]["D_M1_true"]
    on = C.rules_on(w)
    a.set_title("plain level 05 (no rule on)" if not on else ("all four rules on" if len(on) == 4 else "on: " + ",\n     ".join(on)),
                fontsize=C.SMALLEST_PT + 1, loc="left", pad=6)
    a.text(0.98, 0.04, f"measure 1, modulator minus ordinary: {d:+.1f} points", transform=a.transAxes,
           ha="right", va="bottom", fontsize=C.SMALLEST_PT, color=house.INK_2, path_effects=house.halo(house.BG_SOFT))
    a.set_ylim(0, 85); a.set_xlim(0, 100); a.set_xticks([0, 20, 40, 60, 80, 100])
for a in axs[1]:
    a.set_xlabel("true injury (10-point bins)")
for a in axs[:, 0]:
    a.set_ylabel("steps in cover (%)")
fig.tight_layout(h_pad=1.6, w_pad=1.2, rect=(0, 0.1, 1, 1))
h = [Line2D([], [], lw=1.6, ms=5, mec=STY[k]["color"], **STY[k]) for k in STY]
fig.legend(h, [f"{NAME[ag]}, {band}" for ag, band in STY], loc="lower center", ncol=2, frameon=False,
           bbox_to_anchor=(0.5, 0.0), fontsize=C.SMALLEST_PT)

C.record_kind("f3_dose_response", "recordings")
rows = [dict(what="worlds shown", used=4, total=16,
             note=("plain level 05 and all four rules, always; plus the two other worlds with the largest "
                   "modulator-minus-ordinary difference on measure 1, either sign: " +
                   ", ".join(f"{C.world_words(w)} ({100*sc[w]['D_M1_true']:+.1f} points)" for w in rank[:2])))]
for w in chosen:
    for ag in ("ordinary", "modulated"):
        uf, tf = used[(w, ag, "fed")]; uh, th = used[(w, ag, "hungry")]
        rows.append(dict(what=f"{C.world_words(w)}, {NAME[ag]}: fed + hungry decision steps", used=uf + uh,
                         total=tf + th, note="all injury bins hold >= 200 steps" if uf + uh == tf + th
                         else "bins under 200 steps are not drawn"))
C.record_samples("f3_dose_response", rows)
print("  chosen:", chosen, [round(100 * sc[w]["D_M1_true"], 1) for w in chosen])
C.save(fig, "f3_dose_response")
