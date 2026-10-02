"""FIGURE — does the agent hide WHEN IT MATTERS, or just hide?

QUESTION. Time in a bush, on its own, cannot tell a vigilant agent from a timid one. An agent that
sits in cover permanently scores high on "hiding" while doing nothing useful with it. The question
that separates them is SELECTIVITY: how much more does the agent hide when a predator is present
than when the world is empty?

    selectivity = hiding under a predator  MINUS  hiding with no animal at all

Positive means cover is being spent on threat. Zero means hiding is unconditional. NEGATIVE means
the agent hides more when it is safe than when it is hunted, which is not caution but a failure to
discriminate.

WHY IT MATTERS HERE. Reading the raw hiding panels, the modulated agent looked less impressive than
its control on the headline number -- it simply hides less. Selectivity inverts that reading, and it
is the honest comparison, because the two arms differ in how much they hide at BASELINE.

HOW IT IS COMPUTED. Both terms come from the same checkpoint sweep: each saved checkpoint is rolled
out against twelve fixed probe scenarios, thirty episodes each, and `bush_hiding` is the share of
the 100-step probe episode spent on a bush. This figure takes the predator probe and the no-animal
probe at the SAME checkpoint and subtracts, so training time is held fixed and the difference is a
within-checkpoint contrast rather than two curves compared by eye. Uninjured probes throughout, so
the contrast is threat against no-threat and not threat against injury.
"""
import sys, os, csv
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "style"))
import numpy as np, matplotlib.pyplot as plt
import house

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "docs/experiments/active/basic_levels_q2_default/figures")
STEM = "w01_threat_selectivity"

COHORTS = [("Wave 1 - bush does not heal", "wave1", "lvl04"),
           ("Wave 2 - bush heals",         "wave2", "lvl04")]
ARM_COL = {"control": "#9a7d19", "modulated": "#17807a"}   # hues used in no other figure here


def series(wave, lvl, arm, cond):
    p = os.path.join(ROOT, f"results/eval/avoidance/metrics_history_rppo_basicq2_{wave}",
                     f"{lvl}_{arm}", f"avoid_{cond}_inj00.csv")
    if not os.path.exists(p): return None, None
    rows = sorted(csv.DictReader(open(p)), key=lambda r: float(r["step_M"]))
    return (np.array([float(r["step_M"]) for r in rows]),
            np.array([float(r["bush_hiding"]) * 100.0 for r in rows]))


house.apply(series=[ARM_COL["control"], ARM_COL["modulated"]])
fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.3), sharey=True)
rows_acc, n_ck = [], 0
for ax, (title, wave, lvl) in zip(axes, COHORTS):
    ax.axhline(0, color=house.INK_2, lw=1.0)
    for arm in ("control", "modulated"):
        x, pred = series(wave, lvl, arm, "pred")
        _, none = series(wave, lvl, arm, "none")
        if x is None or none is None: continue
        n = min(len(pred), len(none)); sel = pred[:n] - none[:n]
        n_ck += n
        rows_acc.append(dict(what=f"{wave} {arm}: checkpoints with BOTH probes",
                             used=n, total=max(len(pred), len(none)),
                             note="a checkpoint counts only where the predator probe and the "
                                  "no-animal probe were both evaluated; the subtraction is "
                                  "within-checkpoint"))
        # Raw per-checkpoint selectivity swings by tens of points between neighbouring
        # checkpoints, so the raw trace alone invites reading noise as a difference. Draw it
        # faintly and carry the argument on a rolling median, which is what the project's other
        # checkpoint-history figures do.
        k = 7
        pad = np.pad(sel, (k//2, k//2), mode="edge")
        smooth = np.array([np.median(pad[i:i+k]) for i in range(len(sel))])
        ax.plot(x[:n], sel, lw=0.9, color=ARM_COL[arm], alpha=0.30)
        ax.plot(x[:n], smooth, lw=2.4, color=ARM_COL[arm], label=arm)
    ax.set_title(title, fontsize=house.FS_BODY, color=house.INK, loc="left", pad=6)
    ax.set_xlabel("training, million steps")
axes[0].set_ylabel("selectivity, percentage points\n(hiding with a predator MINUS hiding with none)")
house.legend_below(axes[0], ncol=2)

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, f"{STEM}.data.txt"), "w") as fh:
    for r in rows_acc:
        fh.write(f"{r['what']}|{r['used']}|{r['total']}|{100.0*r['used']/max(r['total'],1):.1f}|{r['note']}\n")
house.save(fig, os.path.join(OUT, STEM))
for title, wave, lvl in COHORTS:
    for arm in ("control", "modulated"):
        x, pred = series(wave, lvl, arm, "pred"); _, none = series(wave, lvl, arm, "none")
        if x is None or none is None: continue
        n = min(len(pred), len(none)); sel = pred[:n] - none[:n]
        print(f"  {wave:6} {arm:10} final {sel[-1]:+7.1f} pp   mean last 10 ckpt {sel[-10:].mean():+7.1f} pp")
