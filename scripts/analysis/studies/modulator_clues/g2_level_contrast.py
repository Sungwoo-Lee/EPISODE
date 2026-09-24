"""FIGURE G2 — How strongly each agent's hiding follows the starting injury, level by level.

WHAT IS PLOTTED. For every scene version, the slope of time-in-bush on starting injury (least squares
over the ten injury levels, points per 10 injury), computed at each of the newest 20 checkpoints;
dot = mean, bar = +-1 SD across those checkpoints. Rows are the scene versions of levels 02-06; columns
the three scenes. A black mark at the right means the pre-stated reading rule holds for that row: the
two agents' means differ by more than either agent's checkpoint SD. The rule's per-level tallies are
written to results/analysis/injury_dependence/reading_rule.json for the page text.
"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import numpy as np, matplotlib.pyplot as plt
import _common as C, _inj as I, house

house.apply()
rows = I.rows_versions()
fig, ax = plt.subplots(1, len(I.SCENES), figsize=(10.4, 7.8), sharey=True)
y = np.arange(len(rows))[::-1]; rule = {}; samples = []
for k, (scene, sname) in enumerate(I.SCENES):
    a = ax[k]
    for r, (lv, ver) in enumerate(rows):
        st = {}
        for q, (arm, alab, col) in enumerate(C.ARMS):
            s, sl = I.slope_series(ver, f"{lv}_{arm}", scene)
            if s is None:
                continue
            sl = sl[-I.LAST:]
            st[arm] = (sl.mean(), sl.std(), len(sl))
            yy = y[r] + (0.5 - q) * 0.32
            a.plot([sl.mean() - sl.std(), sl.mean() + sl.std()], [yy, yy], color=col, lw=2.4, alpha=0.4,
                   solid_capstyle="round")
            a.plot([sl.mean()], [yy], "o", color=col, ms=5.5, label=alab if (k == 0 and r == 0) else None)
        if len(st) == 2:
            (mc, sc, _), (mm, sm, _) = st["control"], st["modulated"]
            passed = abs(mm - mc) > max(sc, sm)
            rule.setdefault(lv, {}).setdefault(scene, []).append(
                dict(version=ver, control=mc, modulated=mm, sd_control=sc, sd_modulated=sm,
                     modulated_larger=bool(mm > mc), passes=bool(passed)))
            if passed:
                a.plot([1.0], [y[r]], marker="D", color=house.INK, ms=4.5, transform=a.get_yaxis_transform(),
                       clip_on=False)
            samples_n = st["control"][2] + st["modulated"][2]
        else:
            samples_n = sum(v[2] for v in st.values())
        samples.append(dict(what=f"{sname}, {lv} {I.version_label(ver) or 'core'}", used=samples_n,
                            total=2 * I.LAST, note="checkpoints (both agents) with all ten injury levels measured"))
    a.axvline(0, color=house.INK, lw=0.9)
    a.set_title(sname, loc="left", fontsize=10.5, color=house.INK)
    a.set_xlabel("slope (points per 10 injury)")
    a.grid(axis="y", visible=False)
labels = [f"{lv[-2:]}  {I.version_label(v)}".strip() for lv, v in rows]
ax[0].set_yticks(y); ax[0].set_yticklabels(labels, fontsize=9.5)
ax[0].set_ylabel("level and scene version")
fig.tight_layout(w_pad=1.2)
C.legend_below(ax[0], ncol=2, offset=-0.1)
fig.tight_layout(w_pad=1.2)
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
C.record_kind("g2_level_contrast", "scene")
C.record_samples("g2_level_contrast", samples)
house.save(fig, os.path.join(C.FIG, "g2_level_contrast"), column_px=C.COLUMN_PX)
os.makedirs(I.ID, exist_ok=True)
json.dump(rule, open(os.path.join(I.ID, "reading_rule.json"), "w"), indent=1)
for lv, d in rule.items():
    for sc, L in d.items():
        print(f"  {lv} {sc:20} modulated larger in {sum(x['modulated_larger'] for x in L)}/{len(L)}, "
              f"rule passes {sum(x['passes'] for x in L)}/{len(L)} "
              f"(of which modulated larger {sum(x['passes'] and x['modulated_larger'] for x in L)})")
