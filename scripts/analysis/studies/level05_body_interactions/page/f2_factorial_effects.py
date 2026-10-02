"""FIGURE 2 — Which body rules change the pre-registered measure, and do they change the modulator's
more than the ordinary agent's?

Measure 1 (true injury): how much more the agent hides when badly hurt than when barely hurt, when
fed, minus the same when hungry (design doc §4.1). The 16 worlds are a 2^4 factorial, so the 15
effects (4 main, 6 pairwise, 4 three-way, 1 four-way) are computed three times (§4.2): on the
ordinary agent's own measure, on the modulator's own measure, and on the per-world difference
modulator minus ordinary (the gap). Each panel has its own Lenth margins (§4.3): ME (single-effect,
2.57 x PSE) as a dotted line and SME (simultaneous over 15, 5.22 x PSE) as a dashed line. An effect
is "noted" when |effect| > SME: drawn as a filled marker, every other effect is open.

All numbers are read from factorial_effects.json (factorial_effects.py); none is recomputed here.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C

house = C.house; house.apply()
d = C.load("factorial_effects.json")
m = d["measures"]["M1_true"]
PANELS = [("ordinary", "ordinary agent's own\nmeasure"), ("modulated", "modulator agent's own\nmeasure"),
          ("D (modulated - ordinary)", "the gap:\nmodulator minus ordinary")]
assert d["factors"] == C.FACTORS, d["factors"]
NAME = dict(zip(C.FACTORS, ["healing slower when hungry", "healing uses up food",
                            "cold or hot uses up food", "less food per bite"]))
SHORT = dict(zip(C.FACTORS, ["slow healing", "healing food", "cold/hot food", "less food"]))


def label(e):
    parts = e.split(" x ")
    if len(parts) == 1:
        return NAME[parts[0]]
    if len(parts) == 4:
        return "all four together"
    return " × ".join(SHORT[p] for p in parts)


effects = [e["effect"] for e in m[PANELS[2][0]]["effects"]]
for key, _ in PANELS:
    assert [e["effect"] for e in m[key]["effects"]] == effects
n = len(effects); assert n == 15
y = np.arange(n)[::-1].astype(float)
fig, ax = plt.subplots(1, 3, figsize=(9.8, 7.4), sharey=True)
noted = {}
for a, (key, title) in zip(ax, PANELS):
    blk = m[key]; L = blk["lenth"]
    me, sm = 100 * L["ME"], 100 * L["SME"]          # effects are fractions; the axis is in points
    a.axvspan(-sm, sm, color=house.BG_SOFT, lw=0, zorder=0)
    for s in (-1, 1):
        a.axvline(s * me, color=house.INK, lw=0.8, ls=":")
        a.axvline(s * sm, color=house.INK, lw=0.9, ls="--")
    a.axvline(0, color=C.GREY, lw=0.8)
    vals = np.array([100 * e["value"] for e in blk["effects"]])
    sme = np.array([e["exceeds_SME"] for e in blk["effects"]])
    assert np.array_equal(sme, np.abs(vals) > 100 * L["SME"])       # the flag is what the margin says
    noted[key] = [effects[i] for i in np.flatnonzero(sme)]
    for i in range(n):
        a.plot([0, vals[i]], [y[i]] * 2, color=house.INK, lw=1.2, solid_capstyle="butt")
        a.plot([vals[i]], [y[i]], "o", ms=6.5, mec=house.INK, mew=1.2, mfc=house.INK if sme[i] else "white",
               zorder=3)
    a.set_title(title, fontsize=11, loc="center", pad=8)
    a.set_xlim(-26, 26); a.set_xticks([-20, -10, 0, 10, 20])
    a.grid(axis="y", visible=False); a.grid(axis="x", visible=True)
    for yy in (10.5, 4.5, 0.5):
        a.axhline(yy, color=house.RULE, lw=0.8)
ax[0].set_yticks(y); ax[0].set_yticklabels([label(e) for e in effects], fontsize=C.SMALLEST_PT)
ax[0].set_ylim(-0.7, n - 0.3)
ax[1].set_xlabel("effect of switching the rule(s) on, on measure 1 (percentage points)")
fig.tight_layout(w_pad=1.0, rect=(0, 0.07, 1, 1))
from matplotlib.lines import Line2D
h = [Line2D([], [], color=house.INK, ls=":", lw=0.8), Line2D([], [], color=house.INK, ls="--", lw=0.9),
     Line2D([], [], ls="", marker="o", mfc=house.INK, mec=house.INK, ms=6.5),
     Line2D([], [], ls="", marker="o", mfc="white", mec=house.INK, ms=6.5)]
fig.legend(h, ["single-effect margin (ME)", "margin over all 15 (SME)", "noted (beyond SME)", "within SME"],
           loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=C.SMALLEST_PT)

C.record_kind("f2_factorial_effects", "recordings")
rows = [dict(what="worlds entering every effect", used=16, total=16,
             note="one run per agent per world, seed 42; no world collapsed, so none was left out")]
for key, _ in PANELS:
    L = m[key]["lenth"]; lab = {"ordinary": "ordinary agent", "modulated": "modulator agent"}.get(key, "gap")
    rows.append(dict(what=f"{lab}: effects beyond SME (noted)", used=len(noted[key]), total=15,
                     note=(f"PSE {100*L['PSE']:.2f}, ME {100*L['ME']:.2f}, SME {100*L['SME']:.2f} points; noted: "
                           + (", ".join(label(e) for e in noted[key]) or "none"))))
C.record_samples("f2_factorial_effects", rows)
print("  noted:", {k: noted[k] for k in noted})
C.save(fig, "f2_factorial_effects")
