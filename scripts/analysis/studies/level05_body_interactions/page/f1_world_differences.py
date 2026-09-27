"""FIGURE 1 — In each of the 16 worlds, does the modulator's injury-driven hiding depend on hunger
more than the ordinary agent's? (pre-registered measure 1, TRUE injury; design doc §4.1)

For one agent and one nutrition band (fed = nutrition >= 100, hungry = nutrition < 60):
  hiding contrast = share of decision steps in a bush at injury 60-100  minus  the same at 0-20.
Measure 1 = fed hiding contrast minus hungry hiding contrast.
Panel 2 draws, per world, modulator minus ordinary on the hiding contrast, once for fed and once for
hungry; panel 3 draws modulator minus ordinary on measure 1 itself (the per-world gap D_w that the
factorial of Figure 2 is computed on). Everything is in percentage points of steps.

Intervals: 95 % percentile intervals from a block bootstrap. Each recording is 200 blocks of 5,000
whole evaluation episodes (shard_cells.py); blocks are resampled with replacement, independently for
the two agents, 4,000 times. They show evaluation-episode noise ONLY: with one training seed per
world they say nothing about how a second training run would differ.
Point values are asserted equal to state_contrasts.json before drawing.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _common as C

house = C.house; house.apply()
sc = C.load("state_contrasts.json")
blocks = json.load(open(os.path.join(C.PAGE_OUT, "shard_cells.json")))
R, rng = 4000, np.random.default_rng(20260928)


def boot(label):
    """(R+1) x {fed, hungry} hiding contrasts; row 0 is the full-data value."""
    cells = blocks[label]["cells"]
    nb = len(cells["fed|low"])
    w = np.vstack([np.ones(nb), rng.multinomial(nb, np.full(nb, 1 / nb), size=R)])   # block weights
    out = {}
    for band in ("fed", "hungry"):
        sh = {}
        for g in ("low", "high"):
            a = np.array(cells[f"{band}|{g}"], float)          # blocks x [n, k]
            sh[g] = (w @ a[:, 1]) / (w @ a[:, 0])
        out[band] = 100 * (sh["high"] - sh["low"])
    return out


res = {}
for wld in C.WORLDS:
    o, m = boot(f"{wld}_ordinary"), boot(f"{wld}_modulated")
    d = {b: m[b] - o[b] for b in ("fed", "hungry")}
    d["M1"] = d["fed"] - d["hungry"]
    assert abs(d["M1"][0] - 100 * sc["worlds"][wld]["D_M1_true"]) < 1e-9, wld   # same numbers as the analysis
    res[wld] = {k: (v[0], *np.percentile(v[1:], [2.5, 97.5])) for k, v in d.items()}

worlds = C.WORLDS
y = np.arange(len(worlds))[::-1].astype(float)
fig, ax = plt.subplots(1, 3, figsize=(9.8, 7.4), sharey=True, gridspec_kw=dict(width_ratios=[1.1, 1.45, 1.05]))
C.draw_rule_matrix(ax[0], worlds, y)
BAND = {"fed": dict(marker="o", color=house.INK, mfc=house.INK, off=0.17, label="fed (nutrition 100 or more)"),
        "hungry": dict(marker="D", color=C.GREY, mfc="white", off=-0.17, label="hungry (nutrition under 60)")}
for wld, yy in zip(worlds, y):
    for b, st in BAND.items():
        v, lo, hi = res[wld][b]
        ax[1].plot([lo, hi], [yy + st["off"]] * 2, color=st["color"], lw=1.6, solid_capstyle="butt")
        ax[1].plot([v], [yy + st["off"]], st["marker"], color=st["color"], mfc=st["mfc"], mec=st["color"],
                   mew=1.3, ms=5.5, label=st["label"] if wld == worlds[0] else None)
    v, lo, hi = res[wld]["M1"]
    ax[2].plot([lo, hi], [yy] * 2, color=house.INK, lw=1.6, solid_capstyle="butt")
    ax[2].plot([v], [yy], "s", color=house.INK, ms=5.5, label="measure 1 (fed minus hungry)" if wld == worlds[0] else None)
for a in ax[1:]:
    a.axvline(0, color=C.GREY, lw=0.9)
    a.grid(axis="y", visible=False); a.grid(axis="x", visible=True)
lim = max(abs(x) for r in res.values() for k in ("fed", "hungry") for x in r[k][1:]) * 1.08
# No Lenth margin is drawn here on purpose: ME / SME are margins for the 15 EFFECTS (contrasts over
# all 16 worlds, Figure 2), not for a single world's value, so drawing them on this axis would
# mislabel the scale. The intervals below cover evaluation-episode noise only (see docstring).
lim2 = max(abs(x) for r in res.values() for x in r["M1"][1:]) * 1.08
ax[1].set_xlim(-lim, lim); ax[2].set_xlim(-lim2, lim2)
ax[1].set_xlabel("hiding contrast, modulator\nminus ordinary (points)")
ax[2].set_xlabel("measure 1, modulator\nminus ordinary (points)")
ax[0].set_ylim(-0.7, len(worlds) - 0.3)
fig.tight_layout(w_pad=0.8, rect=(0, 0.1, 1, 1))
h, l = [], []
for a in ax[1:]:
    hh, ll = a.get_legend_handles_labels(); h += hh; l += ll
h.append(Line2D([], [], color=house.INK, lw=1.6)); l.append("95 % interval, evaluation episodes only")
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=C.SMALLEST_PT)

C.record_kind("f1_world_differences", "recordings")
excl = sum(1 for r in res.values() if r["M1"][1] > 0 or r["M1"][2] < 0)
rows = [dict(what="evaluation episodes (32 runs x 1,000,000)", used=32_000_000, total=32_000_000,
             note="final checkpoint, greedy policy; one training seed per world"),
        dict(what="bootstrap blocks per run (5,000 whole episodes each)",
             used=min(v["blocks"] for v in blocks.values()), total=200,
             note=f"{R:,} resamples per agent, independently; interval = evaluation noise only, not seed noise")]
tot_n = tot_in = 0
for wld in worlds:
    for ag in ("ordinary", "modulated"):
        run = sc["runs"][f"{wld}_{ag}"]["final"]
        tot_in += sum(c["n"] for c in run["true"]["cells"].values())
        tot_n += run["survival_store"]["mean_length"] * run["survival_store"]["episodes"]
rows.append(dict(what="decision steps inside the four fed/hungry x low/high cells", used=int(tot_in), total=int(round(tot_n)),
                 note="the rest have nutrition 60-100 or injury 20-60, which measure 1 does not use"))
rows.append(dict(what="worlds whose measure-1 interval excludes zero", used=excl, total=16,
                 note="evaluation noise only; the pre-registered noise judgement is Figure 2's"))
C.record_samples("f1_world_differences", rows)
print("  M1 gap range %.1f..%.1f, intervals excluding 0: %d" % (min(r["M1"][0] for r in res.values()),
                                                                 max(r["M1"][0] for r in res.values()), excl))
for wld in worlds:
    print("   ", wld, " ".join(f"{k} {v[0]:+.1f} [{v[1]:+.1f},{v[2]:+.1f}]" for k, v in res[wld].items()))
C.save(fig, "f1_world_differences")
