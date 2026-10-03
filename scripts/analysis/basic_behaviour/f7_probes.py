#!/usr/bin/env python3
"""f7_probes.py - Figure 7: the probe-scene sweep of the Basic Behaviour page (exploratory).

Reads only what probes.py wrote to <out-root>/probes/ (seconds). One figure per call:

    $P scripts/analysis/basic_behaviour/f7_probes.py --out-root <abs .../hvsmell> --fig-dir <page>/figures \
        --figure {traces,levels,confusion,threat,budget,training,other} [--world hv2ch|hv1ch|hv1chm]

  traces     bush dwell per checkpoint, one figure per world: rows = scene, columns = agent x injury,
             one line per training seed; the newest-20 window shaded
  levels     newest-20 means with lag-1-corrected 95 % intervals, scene x injury panels
  confusion  confusion contrast at each injury, its injury shift, and the wandering rabbit response
  threat     predator - no animal, chasing rabbit - no animal, at each injury
  budget     world differences vs seed-to-seed SD vs checkpoint-to-checkpoint SD, per agent
  training   probe bush dwell vs training-world bush dwell, per run
  other      survival, closest distance to the animal, spatial spread (newest-20 means)

Worlds with a pond (BASIC_BEHAVIOUR_WATER Revision 2; probes.py output marked "water"):
  pond_traces  --map 10|15|20: rows = scene, columns = smell reach x injury; bush time before the
               first pond step (solid) and share of episodes reaching the pond (dotted), per agent
  pond_levels  newest-20 means (within-run 95 % intervals) of the pre-pond bush share, 9 worlds
  pond_visits  the same for the share of episodes reaching the pond

Encoding, shared with Figures 1-6: colour = world, marker shape = agent; a hollow marker = a value
that is reported but not interpreted (survival under 95 steps in a scene it uses, or no-animal bush
dwell above 90 %, pre-stated rules 1 and 9); the black horizontal dash = mean of the three seeds;
grey dash-dot = a reference line.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _fig as FG                                                       # noqa: E402
import probes as PR                                                     # noqa: E402

H = FG.H
FIGS = ("traces", "levels", "confusion", "threat", "budget", "training", "other")
WORLDS = ["hv2ch", "hv1ch", "hv1chm"]
AGENTS = ["t1none", "t16quad"]
COL = {w: H.SERIES[i] for i, w in enumerate(WORLDS)}
MK = {"t1none": FG.MARKERS[0], "t16quad": FG.MARKERS[1]}
WSHORT = {"hv2ch": "control", "hv1ch": "single-channel", "hv1chm": "matched"}
WLONG = {"hv2ch": "two-channel smell (control)", "hv1ch": "single-channel smell",
         "hv1chm": "matched-strength smell"}
STEM = {f: f"f7_probe_{f}" for f in FIGS}
SHORT_SCENE = {"none": "no animal", "pred": "hunting predator", "rabbit": "chasing rabbit",
               "rabbit_olfzero": "chasing rabbit, no smell", "rabbitwander": "wandering rabbit",
               "rabbitwander_predsmell": "predator-smelling rabbit"}
NOTE_FLAG = ("a hollow marker is reported, not interpreted (survival under 95 steps in a scene it "
             "uses, or bush dwell over 90 % with no animal)")


def load(out_root):
    d = os.path.join(out_root, "probes")
    for f in ("run_summary.csv", "series.csv.gz", "world_summary.csv", "training_world.csv",
              "completeness.json", "provenance.json"):
        if not os.path.exists(os.path.join(d, f)):
            raise SystemExit(f"no {d}/{f} - run probes.py first")
    return {"R": pd.read_csv(os.path.join(d, "run_summary.csv")),
            "S": pd.read_csv(os.path.join(d, "series.csv.gz"), dtype={"injury": str}),
            "WS": pd.read_csv(os.path.join(d, "world_summary.csv")),
            "TW": pd.read_csv(os.path.join(d, "training_world.csv")),
            "comp": json.load(open(os.path.join(d, "completeness.json")))}


def inj_str(x):
    return f"{int(x):02d}" if str(x) not in ("", "nan") else ""


def positions():
    """x of each (world, agent, seed): one tick per world; the two agents (marker shape) side by
    side inside it, the three seeds spread inside each agent."""
    pos, ticks, labels = {}, [], []
    for k, w in enumerate(WORLDS):
        for j, a in enumerate(AGENTS):
            for i, s in enumerate((42, 43, 44)):
                pos[(w, a, s)] = k + (j - 0.5) * 0.46 + (i - 1) * 0.1
        ticks.append(k)
        labels.append(WSHORT[w])
    return pos, ticks, labels


def wrap_title(text, width=30):
    import textwrap
    return "\n".join(textwrap.wrap(text, width))


def flag(r):
    return bool(r.get("short_survival", False)) or bool(r.get("at_ceiling", False))


def dot_panel(ax, sub, pos, ticks, labels, show_mean=True, ci=True):
    """One marker per run (world colour, agent shape, hollow if flagged) with its 95 % interval;
    the mean of the seeds as a black dash."""
    for r in sub.to_dict("records"):
        x = pos[(r["world"], r["agent"], int(r["seed"]))]
        c = COL[r["world"]]
        if ci and np.isfinite(r["lo"]):
            ax.plot([x, x], [r["lo"], r["hi"]], color=c, lw=1.3, alpha=0.75, solid_capstyle="butt")
        hollow = flag(r)
        ax.plot(x, r["mean"], ls="", marker=MK[r["agent"]], ms=6.5, color=c,
                mfc=H.PAPER if hollow else c, mew=1.6)
    if show_mean:
        for (w, a), g in sub.groupby(["world", "agent"]):
            if len(g) == 3:
                x0 = pos[(w, a, 43)]
                ax.plot([x0 - 0.17, x0 + 0.17], [g["mean"].mean()] * 2, color=H.INK, lw=2.2,
                        solid_capstyle="butt")
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, fontsize=H.FS_LABEL)
    ax.set_xlim(ticks[0] - 0.5, ticks[-1] + 0.5)
    ax.grid(axis="x", visible=False)


def legend(fig, extra=(), y=0.0, ncol=4, worlds=WORLDS, agents=True):
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], ls="", marker="o", ms=8, color=COL[w], label=WLONG[w]) for w in worlds]
    if agents:
        hs += [Line2D([], [], ls="", marker=MK[a], ms=8, color=H.INK_2, label=FG.alabel(a)) for a in AGENTS]
    hs += list(extra)
    return fig.legend(handles=hs, loc="lower center", ncol=ncol, frameon=False, fontsize=H.FS_LABEL,
                      bbox_to_anchor=(0.5, y))


def mean_handle():
    from matplotlib.lines import Line2D
    return Line2D([], [], color=H.INK, lw=2.2, label="mean of the three seeds")


def hollow_handle():
    from matplotlib.lines import Line2D
    return Line2D([], [], ls="", marker="o", ms=8, color=H.INK_2, mfc=H.PAPER, mew=1.6,
                  label="reported, not interpreted")


def extras(sub):
    """Legend extras for a dot figure; the hollow-marker entry only when a hollow marker is drawn."""
    hs = [mean_handle(), ci_handle()]
    if len(sub) and sub.apply(flag, axis=1).any():
        hs.append(hollow_handle())
    return hs


def ci_handle():
    from matplotlib.lines import Line2D
    return Line2D([], [], color=H.INK_2, lw=1.3, label="95% interval (checkpoint-to-checkpoint)")


def zero(ax):
    ax.axhline(0, color=H.RULE, lw=1.1, zorder=0)


# ------------------------------------------------------------------ data statements

def window_rows(D, what_prefix, kind_filter, hollow=True):
    """Per world: newest-20 checkpoints used out of the checkpoints found, summed over runs."""
    rows = []
    comp = pd.DataFrame(D["comp"]["rows"])
    runs = {r["label"]: r for r in D["comp"]["runs"]}
    R = D["R"][kind_filter(D["R"])]
    for w in WORLDS:
        labels = [l for l, r in runs.items() if r["world"] == w]
        c = comp[comp.label.isin(labels)]
        found = int(c.found.sum())
        exp = int(c.expected.sum())
        used = int(len(c[c.found >= PR.WINDOW]) * PR.WINDOW)
        rows.append({"what": f"{what_prefix}, {WLONG[w]} (6 runs x 12 scenes)", "used": used, "total": found,
                     "note": "the newest 20 saved checkpoints of each run and scene (pre-stated window); "
                             "older checkpoints are drawn in the traces but not summarised"})
        if found < exp:
            rows.append({"what": f"checkpoints evaluated, {WLONG[w]}", "used": found, "total": exp,
                         "note": "DRAFT: the sweep has not finished every checkpoint"})
        nflag = int(R[(R.world == w)].apply(flag, axis=1).sum()) if len(R) else 0
        if nflag and hollow:
            rows.append({"what": f"values shown hollow (not interpreted), {WLONG[w]}", "used": nflag,
                         "total": len(R[R.world == w]), "note": NOTE_FLAG})
    rows.append({"what": "episodes behind each checkpoint value", "used": 30, "total": 30,
                 "note": "30 evaluation episodes per checkpoint and scene, fixed episode seeds"})
    return rows


# ------------------------------------------------------------------ figures

def fig_traces(D, world):
    import matplotlib.pyplot as plt
    S = D["S"]
    S = S[(S.measure == "bush_hiding") & S.label.str.startswith(world + "_")]
    cols = [(a, i) for a in AGENTS for i in PR.INJURIES]
    fig, axs = plt.subplots(len(PR.SCENES), len(cols), figsize=(12.0, 2.05 * len(PR.SCENES) + 1.4),
                            sharex=True, sharey=True)
    for ri, (scene, sname) in enumerate(PR.SCENES):
        for ci, (a, inj) in enumerate(cols):
            ax = axs[ri, ci]
            sub = S[(S.scene == scene) & (S.injury == inj) & S.label.str.contains(f"_{a}_")]
            last = []
            for lab, g in sub.groupby("label"):
                g = g.sort_values("step")
                ax.plot(g.step / 1e6, g.value, color=COL[world], lw=1.1, alpha=0.8,
                        marker=MK[a], ms=2.6)
                if len(g) >= PR.WINDOW:
                    last.append(g.step.iloc[-PR.WINDOW] / 1e6)
            if last:
                ax.axvspan(max(last), 10.2, color=H.INK_2, alpha=0.08, lw=0)
            ax.set_ylim(-4, 104)
            ax.set_yticks([0, 50, 100])
            ax.set_xlim(0, 10.3)
            ax.set_xticks([0, 5, 10])
            if ri == 0:
                ax.set_title(f"{FG.alabel(a)},\n{PR.INJ_NAME[inj]}", fontsize=H.FS_BODY, loc="left")
            if ci == 0:
                ax.set_ylabel(sname.replace(" that ", "\nthat ").replace(", ", ",\n"), fontsize=H.FS_LABEL)
    fig.supxlabel("training progress (millions of environment steps)", fontsize=H.FS_BODY, y=0.045)
    fig.supylabel("bush dwell: share of the scene's steps on the bush (%)", fontsize=H.FS_BODY, x=0.005)
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend(fig, extra=[Line2D([], [], color=COL[world], lw=1.1, label="one line per training seed"),
                       Patch(color=H.INK_2, alpha=0.15, label="the newest 20 checkpoints (summarised)")],
           y=-0.005, ncol=3, worlds=[world], agents=False)
    fig.tight_layout(rect=(0.02, 0.06, 1, 1), h_pad=0.9, w_pad=0.9)
    return fig, window_rows(D, "checkpoints summarised", lambda R: (R.kind == "level") & (R.measure == "bush_hiding")
                            & (R.world == world), hollow=False)


def fig_levels(D):
    import matplotlib.pyplot as plt
    R = D["R"]
    R = R[(R.kind == "level") & (R.measure == "bush_hiding")].copy()
    R["injury"] = R["injury"].map(inj_str)
    pos, ticks, labels = positions()
    fig, axs = plt.subplots(3, 4, figsize=(12.0, 12.6), sharey=True)
    for k, (scene, sname) in enumerate(PR.SCENES):
        for j, inj in enumerate(PR.INJURIES):
            ax = axs[k // 2, (k % 2) * 2 + j]
            dot_panel(ax, R[(R.scene == scene) & (R.injury == inj)], pos, ticks, labels)
            ax.set_title(f"{SHORT_SCENE[scene]} · inj. {int(inj)}", fontsize=H.FS_LABEL + 1, loc="left")
            ax.set_ylim(-4, 104)
            if (k % 2) * 2 + j == 0:
                ax.set_ylabel("bush dwell (%)")
    legend(fig, extra=extras(R), y=-0.01, ncol=4)
    fig.tight_layout(rect=(0, 0.06, 1, 1), h_pad=1.6, w_pad=0.8)
    return fig, window_rows(D, "checkpoints summarised", lambda R: (R.kind == "level") & (R.measure == "bush_hiding"))


def contrast_fig(D, panels, ncol, size):
    import matplotlib.pyplot as plt
    R = D["R"][D["R"].kind == "contrast"]
    pos, ticks, labels = positions()
    nrow = int(np.ceil(len(panels) / ncol))
    fig, axs = plt.subplots(nrow, ncol, figsize=size, squeeze=False)
    used = []
    lo = min([R[R.quantity == q]["lo"].min() for q, _ in panels if (R.quantity == q).any()] + [-5])
    hi = max([R[R.quantity == q]["hi"].max() for q, _ in panels if (R.quantity == q).any()] + [5])
    pad = 0.06 * (hi - lo)
    for k, (q, title) in enumerate(panels):
        ax = axs[k // ncol, k % ncol]
        dot_panel(ax, R[R.quantity == q], pos, ticks, labels)
        zero(ax)
        ax.set_ylim(lo - pad, hi + pad)
        ax.set_title(title, fontsize=H.FS_LABEL + 1, loc="left")
        if k % ncol == 0:
            ax.set_ylabel("difference in bush dwell\n(percentage points)")
        used.append(q)
    for k in range(len(panels), nrow * ncol):
        axs[k // ncol, k % ncol].set_visible(False)
    return fig, used


def contrast_rows(D, qs):
    R = D["R"][(D["R"].kind == "contrast") & D["R"].quantity.isin(qs)]
    rows = window_rows(D, "checkpoints summarised (levels behind the differences)",
                       lambda X: (X.kind == "contrast") & X.quantity.isin(qs))
    n_exp = 18 * len(qs)
    rows.insert(0, {"what": "run-level differences drawn", "used": int(len(R)), "total": n_exp,
                    "note": "18 runs x the panels' differences; a difference whose scenes have fewer than "
                            "20 checkpoints in common is not computed" if len(R) < n_exp else
                            "every run, every panel"})
    return rows


def fig_confusion(D):
    panels = [("confusion_00", "confusion contrast, injury 0\n(predator-smelling minus ordinary\nwandering rabbit)"),
              ("confusion_70", "confusion contrast, injury 70\n(predator-smelling minus ordinary\nwandering rabbit)"),
              ("confusion_shift", "injury shift of the\nconfusion contrast\n(injury 70 minus injury 0)"),
              ("rabbit_resp_00", "wandering rabbit response,\ninjury 0\n(wandering rabbit minus no animal)"),
              ("rabbit_resp_70", "wandering rabbit response,\ninjury 70\n(wandering rabbit minus no animal)")]
    fig, used = contrast_fig(D, panels, 3, (12.0, 10.6))
    legend(fig, extra=extras(D["R"][D["R"].quantity.isin(used)]), y=-0.005, ncol=4)
    fig.tight_layout(rect=(0, 0.07, 1, 1), h_pad=1.8, w_pad=1.0)
    return fig, contrast_rows(D, used)


def fig_threat(D):
    panels = [("threat_pred_00", "threat discrimination, injury 0\n(hunting predator minus no animal)"),
              ("threat_pred_70", "threat discrimination, injury 70\n(hunting predator minus no animal)"),
              ("threat_chase_00", "chasing rabbit, injury 0\n(chasing rabbit minus no animal)"),
              ("threat_chase_70", "chasing rabbit, injury 70\n(chasing rabbit minus no animal)")]
    fig, used = contrast_fig(D, panels, 2, (11.0, 10.8))
    legend(fig, extra=extras(D["R"][D["R"].quantity.isin(used)]), y=-0.005, ncol=4)
    fig.tight_layout(rect=(0, 0.08, 1, 1), h_pad=1.8, w_pad=1.2)
    return fig, contrast_rows(D, used)


BUDGET_SHOWN = ["threat_pred_00", "rabbit_resp_00", "confusion_00", "confusion_70", "confusion_shift"]
BUDGET_TITLE = {"threat_pred_00": "threat discrimination, injury 0",
                "rabbit_resp_00": "wandering rabbit response, injury 0",
                "confusion_00": "confusion contrast, injury 0", "confusion_70": "confusion contrast, injury 70",
                "confusion_shift": "injury shift of the confusion contrast"}


def fig_budget(D):
    import matplotlib.pyplot as plt
    WS = D["WS"]
    items = [("diff_hv1chm_hv2ch", "matched − control"), ("diff_hv1ch_hv2ch", "single-channel − control"),
             ("diff_hv1ch_hv1chm", "single-channel − matched"), ("seed_sd", "seed-to-seed SD"),
             ("ckpt_sd", "checkpoint-to-checkpoint SD")]
    fig, axs = plt.subplots(len(BUDGET_SHOWN), 2, figsize=(12.0, 2.3 * len(BUDGET_SHOWN) + 1.2))
    # one horizontal scale per ROW (both agents of a quantity share it): the quantities differ by an
    # order of magnitude, and one scale for all would flatten the small ones to slivers
    row_max = {}
    for q in BUDGET_SHOWN:
        v = [abs(float(x)) for c, _ in items if c in WS for x in WS[WS.quantity == q][c]]
        row_max[q] = max([1.0] + v) * 1.55
    for ri, q in enumerate(BUDGET_SHOWN):
        for ci, a in enumerate(AGENTS):
            ax = axs[ri, ci]
            sub = WS[(WS.quantity == q) & (WS.agent == a)]
            ax.set_yticks(range(len(items)))
            ax.set_yticklabels([lab for _, lab in items] if ci == 0 else [""] * len(items), fontsize=H.FS_LABEL)
            ax.set_ylim(len(items) - 0.4, -0.6)
            ax.grid(axis="y", visible=False)
            ax.grid(axis="x", color=H.TICK_LINE)
            xmax = row_max[q]
            ax.set_xlim(0, xmax)
            share = (f"\nbetween worlds: {100 * sub['share_between'].iloc[0]:.0f}% of the nine runs' variance"
                     if len(sub) else "")
            ax.set_title(f"{BUDGET_TITLE[q]}, {FG.alabel(a)}{share}", fontsize=H.FS_LABEL + 1, loc="left")
            if not len(sub):
                ax.text(0.5 * xmax, 2, "not computed (fewer than\n20 checkpoints)", ha="center", va="center",
                        fontsize=H.FS_LABEL, color=H.INK_2)
                continue
            r = sub.iloc[0]
            for k, (c, _) in enumerate(items):
                v = abs(float(r[c]))
                if c.startswith("diff"):
                    sep = bool(r["sep" + c[4:]])
                    ax.barh(k, v, height=0.62, color=H.INK if sep else H.TEXT_LIGHT)
                    ax.text(v + 0.012 * xmax, k, f"{r[c]:+.1f}".replace("-", "\u2212") + (" (seeds apart)" if sep else ""),
                            va="center", fontsize=H.FS_LABEL, color=H.INK)
                else:
                    ax.barh(k, v, height=0.62, color=H.BG_SOFT, edgecolor=H.TEXT_LIGHT, hatch="///", lw=0.6)
                    ax.text(v + 0.012 * xmax, k, f"{v:.1f}", va="center", fontsize=H.FS_LABEL, color=H.INK)
    for ax in axs.ravel():
        ax.set_xlabel("percentage points of bush dwell", fontsize=H.FS_LABEL, color=H.INK_2,
                      fontweight="normal")
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=H.TEXT_LIGHT, label="difference between worlds (mean of three seeds each)"),
                        Patch(color=H.INK, label="… with all three seeds of one world beyond all three of the other"),
                        Patch(facecolor=H.BG_SOFT, edgecolor=H.TEXT_LIGHT, hatch="///",
                              label="spread: seed-to-seed (between runs) or checkpoint-to-checkpoint (within a run)")],
               loc="lower center", ncol=1, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.005))
    fig.tight_layout(rect=(0, 0.075, 1, 1), h_pad=1.6, w_pad=1.2)
    rows = []
    for a in AGENTS:
        for q in BUDGET_SHOWN:
            sub = WS[(WS.quantity == q) & (WS.agent == a)]
            n = int(sub["n_runs"].iloc[0]) if len(sub) else 0
            rows.append({"what": f"runs behind the {BUDGET_TITLE[q]}, {FG.alabel(a)}", "used": n, "total": 9,
                         "note": "three seeds per world; every run-level value is a newest-20 checkpoint mean"
                         if n == 9 else "a world with fewer than two seeds has no seed-to-seed SD; not drawn"})
            if len(sub) and int(sub["flagged_runs"].iloc[0]):
                k = int(sub["flagged_runs"].iloc[0])
                rows.append({"what": f"of those, runs shown hollow in Figures 7b-7d ({BUDGET_TITLE[q]}, {FG.alabel(a)})",
                             "used": k, "total": n,
                             "note": f"{k} run(s) under the survival or ceiling rule are still counted here, since the "
                                     "budget describes spread, not an effect; read this quantity's world differences "
                                     "with that in mind"})
    rows += window_rows(D, "checkpoints summarised", lambda X: (X.kind == "contrast") & X.quantity.isin(BUDGET_SHOWN))
    return fig, rows


def fig_training(D):
    import matplotlib.pyplot as plt
    from scipy import stats
    R = D["R"]
    R = R[(R.kind == "level") & (R.measure == "bush_hiding")].copy()
    R["injury"] = R["injury"].map(inj_str)
    TW = D["TW"].set_index("label")
    scenes = [(k, SHORT_SCENE[k]) for k in ("none", "pred", "rabbitwander_predsmell")]
    fig, axs = plt.subplots(1, 3, figsize=(12.0, 5.6), sharey=True)
    xs_all = TW.bush_dwell.dropna()
    xlo, xhi = (float(xs_all.min()), float(xs_all.max())) if len(xs_all) else (0.0, 5.0)
    xpad = max(0.5, 0.12 * (xhi - xlo))
    ymax = float(R[(R.scene.isin([s for s, _ in scenes])) & (R.injury == "00")]["mean"].max())
    ymax = min(104.0, max(10.0, ymax * 1.15))
    nused = 0
    for ax, (scene, sname) in zip(axs, scenes):
        sub = R[(R.scene == scene) & (R.injury == "00")]
        xs, ys = [], []
        for r in sub.to_dict("records"):
            x = TW.bush_dwell.get(r["label"], np.nan)
            if not np.isfinite(x):
                continue
            hollow = flag(r)
            ax.plot(x, r["mean"], ls="", marker=MK[r["agent"]], ms=7.5, color=COL[r["world"]],
                    mfc=H.PAPER if hollow else COL[r["world"]], mew=1.6)
            xs.append(x); ys.append(r["mean"])
        nused = max(nused, len(xs))
        rho = stats.spearmanr(xs, ys).statistic if len(xs) >= 4 else np.nan
        rtxt = f"{rho:+.2f}".replace("-", "\u2212")
        ax.set_title(f"{sname} · inj. 0\nrank correlation across runs: {rtxt}",
                     fontsize=H.FS_LABEL + 1, loc="left")
        ax.set_xlim(xlo - xpad, xhi + xpad)
        ax.set_ylim(0, ymax)
        ax.set_xlabel("training-environment bush dwell\n(% of chosen steps, final checkpoint;\naxis not from zero)")
        ax.grid(axis="x", color=H.TICK_LINE)
    axs[0].set_ylabel("experiment-test bush dwell\n(%, newest 20 checkpoints)")
    legend(fig, extra=[hollow_handle()], y=-0.02, ncol=3)
    fig.tight_layout(rect=(0, 0.13, 1, 1), w_pad=1.4)
    rows = []
    for lab, r in TW.iterrows():
        rows.append({"what": f"training-environment episodes, run {lab}", "used": int(r.n_episodes), "total": int(r.n_episodes),
                     "note": f"every evaluation episode of the run's trajectory store at checkpoint {int(r.checkpoint):,} "
                             "(the same numbers as Figure 1)"})
    rows.append({"what": "runs with both a training-environment and an experiment-test value", "used": nused, "total": 18,
                 "note": "every run" if nused == 18 else "a run without 20 experiment-test checkpoints is not drawn"})
    return fig, rows


def fig_other(D):
    import matplotlib.pyplot as plt
    R = D["R"]
    R = R[R.kind == "level"].copy()
    R["injury"] = R["injury"].map(inj_str)
    meas = [("survival_steps", "survival (recorded steps;\n101 = the whole scene)"),
            ("closest_approach", "closest distance to the animal (squares)"),
            ("spatial_spread", "spatial spread (squares)")]
    cells = [(s, i) for s, _ in PR.SCENES for i in PR.INJURIES]
    fig, axs = plt.subplots(len(meas), 1, figsize=(12.0, 12.8), sharex=True)
    off = {(w, a): (k - 2.5) * 0.12 for k, (w, a) in enumerate([(w, a) for w in WORLDS for a in AGENTS])}
    for ax, (m, lab) in zip(axs, meas):
        sub = R[R.measure == m]
        for (w, a), o in off.items():
            for k, (s, i) in enumerate(cells):
                g = sub[(sub.world == w) & (sub.agent == a) & (sub.scene == s) & (sub.injury == i)]
                g = g[np.isfinite(g["mean"])]
                if not len(g):
                    continue
                x = k + o
                ax.plot([x, x], [g["mean"].min(), g["mean"].max()], color=COL[w], lw=1.4, alpha=0.85, ls=":")
                for yv in (g["mean"].min(), g["mean"].max()):
                    ax.plot([x - 0.035, x + 0.035], [yv, yv], color=COL[w], lw=1.4, alpha=0.85)
                ax.plot(x, g["mean"].mean(), ls="", marker=MK[a], ms=6, color=COL[w])
        if m == "closest_approach":
            ax.set_ylim(bottom=-0.12)
        if m == "survival_steps":
            ax.axhline(PR.SURVIVAL_FLOOR, color=H.TEXT_LIGHT, lw=1.4, ls="-.")
            ax.text(len(cells) - 0.5, PR.SURVIVAL_FLOOR - 1.5, "95 steps: validity floor", ha="right", va="top",
                    fontsize=H.FS_LABEL, color=H.INK_2)
        ax.set_ylabel(lab if "\n" in lab else lab.replace(" (", "\n("))
        for k in range(1, len(PR.SCENES)):
            ax.axvline(2 * k - 0.5, color=H.TICK_LINE, lw=0.9)
    axs[-1].set_xticks(range(len(cells)))
    axs[-1].set_xticklabels([f"{PR.SCENE_NAME[s].replace(' that ', chr(10) + 'that ').replace(', ', ',' + chr(10))}"
                             f"\n{PR.INJ_NAME[i]}" for s, i in cells], fontsize=H.FS_LABEL, rotation=90)
    axs[-1].set_xlim(-0.6, len(cells) - 0.4)
    for ax in axs:
        ax.grid(axis="x", visible=False)
    from matplotlib.lines import Line2D
    legend(fig, extra=[Line2D([], [], color=H.INK_2, lw=1.8, ls=":",
                              label="range of 3 seeds, not an interval (marker: their mean)")],
           y=-0.005, ncol=3)
    fig.tight_layout(rect=(0, 0.06, 1, 1), h_pad=1.2)
    rows = window_rows(D, "checkpoints summarised", lambda X: (X.kind == "level") & X.measure.isin([m for m, _ in meas]),
                       hollow=False)
    rows.insert(0, {"what": "closest distance in the no-animal scenes", "used": 0,
                    "total": 2 * 18, "note": "not defined: there is no animal to be close to"})
    return fig, rows


# ------------------------------------------------------------------ worlds with a pond
# (docs/develop/active/behavior/BASIC_BEHAVIOUR_WATER.md, Revision 2). probes.py has already put the
# bush share BEFORE THE FIRST POND STEP in `bush_hiding`, and carries `pond_visit_share` (%) and
# `n_overdrink`. Nine worlds = map size x smell reach; one run per world x agent, so every interval is
# within-run (checkpoint-to-checkpoint), never seed-to-seed. Colour = agent here (the world is the
# panel or the horizontal position), a stated departure from the page's colour = world encoding.
WATER_FIGS = ("pond_traces", "pond_levels", "pond_visits")
W_MAPS = ("10", "15", "20")
W_REACH = ("W", "5", "3")
W_REACH_NAME = {"W": "smell across the map", "5": "smell 5 squares", "3": "smell 3 squares"}
W_WORLDS = [f"g{m}s{r}" for m in W_MAPS for r in W_REACH]
W_COL = {"t1none": H.SERIES[0], "t16quad": H.SERIES[1]}


def wlabel_water(w):
    return f"{w[1:3]}×{w[1:3]}, {W_REACH_NAME[w[-1]]}"


def water_rows(D, worlds, measure, what):
    """Data statement rows; every count comes from probes.py's completeness record and series."""
    comp = pd.DataFrame(D["comp"]["rows"])
    runs = {r["label"]: r for r in D["comp"]["runs"]}
    rows = []
    for w in worlds:
        c = comp[comp.label.isin([l for l, r in runs.items() if r["world"] == w])]
        found, exp = int(c.found.sum()), int(c.expected.sum())
        n_runs, n_scenes = c.label.nunique(), len(c.groupby(["scene", "injury"]))
        rows.append({"what": f"{what}, {wlabel_water(w)} ({n_runs} runs x {n_scenes} scenes)",
                     "used": int(len(c[c.found >= PR.WINDOW]) * PR.WINDOW) if measure else found,
                     "total": found if measure else exp,
                     "note": ("the newest 20 saved checkpoints of each run and scene; older ones are drawn in "
                              "the traces only" if measure else "every saved checkpoint of each run and scene; "
                              "no scene x checkpoint cell is dropped")})
        if found < exp:
            rows.append({"what": f"checkpoints evaluated, {wlabel_water(w)}", "used": found, "total": exp,
                         "note": "DRAFT: the sweep has not finished every checkpoint"})
    S = D["S"]
    n = S[(S.measure == "n_episodes") & S.label.str.match("|".join(f"{w}_" for w in worlds))]["value"]
    if not len(n):
        raise SystemExit("probes series has no n_episodes rows (re-run probes.py on the pond CSVs)")
    rows.append({"what": "episodes behind the checkpoint values", "used": int(n.sum()), "total": int(n.sum()),
                 "note": f"{int(n.min())}-{int(n.max())} evaluation episodes per checkpoint and scene; every "
                         f"episode counted, its bush time read up to its first pond step"})
    return rows


def fig_pond_traces(D, mp):
    """Rows = scene, columns = smell reach x injury; solid = bush share before the first pond step,
    dotted = share of the 30 episodes that reached the pond; one colour per agent; a cross at the top
    where any episode died of over-drinking."""
    import matplotlib.pyplot as plt
    S = D["S"]
    worlds = [f"g{mp}s{r}" for r in W_REACH]
    cols = [(w, i) for w in worlds for i in PR.INJURIES]
    xmax = max(S.step.max() / 1e6, 1.0)
    fig, axs = plt.subplots(len(PR.SCENES), len(cols), figsize=(12.0, 2.0 * len(PR.SCENES) + 1.6),
                            sharex=True, sharey=True)
    for ri, (scene, sname) in enumerate(PR.SCENES):
        for ci, (w, inj) in enumerate(cols):
            ax = axs[ri, ci]
            sub = S[(S.scene == scene) & (S.injury == inj) & S.label.str.startswith(w + "_")]
            for a in AGENTS:
                g = sub[sub.label.str.contains(f"_{a}_")]
                b = g[g.measure == "bush_hiding"].sort_values("step")
                v = g[g.measure == "pond_visit_share"].sort_values("step")
                o = g[(g.measure == "n_overdrink") & (g.value > 0)]
                ax.plot(b.step / 1e6, b.value, color=W_COL[a], lw=1.2)
                ax.plot(v.step / 1e6, v.value, color=W_COL[a], lw=1.0, ls=":")
                if len(o):
                    ax.plot(o.step / 1e6, [101] * len(o), ls="", marker="x", ms=4, color=W_COL[a])
            ax.set_ylim(-4, 106)
            ax.set_yticks([0, 50, 100])
            ax.set_xlim(0, xmax * 1.03)
            if ri == 0:
                ax.set_title(f"{W_REACH_NAME[w[-1]]},\n{PR.INJ_NAME[inj]}", fontsize=H.FS_LABEL + 1, loc="left")
            if ci == 0:
                ax.set_ylabel(SHORT_SCENE[scene].replace(", ", ",\n"), fontsize=H.FS_LABEL)
    fig.supxlabel("training progress (millions of training episodes at the checkpoint)", fontsize=H.FS_BODY, y=0.045)
    fig.supylabel("share (%): bush time before the first pond step, solid; episodes reaching the pond, dotted",
                  fontsize=H.FS_BODY, x=0.005)
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=W_COL[a], lw=1.6, label=FG.alabel(a)) for a in AGENTS]
    hs += [Line2D([], [], color=H.INK_2, lw=1.2, label="bush time before the first pond step"),
           Line2D([], [], color=H.INK_2, lw=1.0, ls=":", label="share of episodes reaching the pond"),
           Line2D([], [], ls="", marker="x", color=H.INK_2, label="an over-drinking death at that checkpoint")]
    fig.legend(handles=hs, loc="lower center", ncol=3, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.005))
    fig.tight_layout(rect=(0.02, 0.07, 1, 1), h_pad=0.9, w_pad=0.7)
    return fig, water_rows(D, worlds, False, "checkpoints drawn")


def fig_pond_window(D, measure, ylabel):
    """Newest-20 checkpoint means with lag-1-corrected 95 % intervals (within-run), per world,
    one marker per agent; panels = scene x injury."""
    import matplotlib.pyplot as plt
    R = D["R"]
    R = R[(R.kind == "level") & (R.measure == measure)].copy()
    R["injury"] = R["injury"].map(inj_str)
    fig, axs = plt.subplots(6, 2, figsize=(12.0, 17.0), sharey=True, sharex=True)
    for k, (scene, sname) in enumerate(PR.SCENES):
        for j, inj in enumerate(PR.INJURIES):
            ax = axs[k, j]
            sub = R[(R.scene == scene) & (R.injury == inj)]
            for xi, w in enumerate(W_WORLDS):
                for ai, a in enumerate(AGENTS):
                    r = sub[(sub.world == w) & (sub.agent == a)]
                    if not len(r):
                        continue
                    r = r.iloc[0]
                    x = xi + (ai - 0.5) * 0.3
                    if np.isfinite(r["lo"]):
                        ax.plot([x, x], [r["lo"], r["hi"]], color=W_COL[a], lw=1.3, alpha=0.75)
                    ax.plot(x, r["mean"], ls="", marker=MK[a], ms=6, color=W_COL[a])
            for b in (2.5, 5.5):
                ax.axvline(b, color=H.RULE, lw=1)
            ax.set_xticks(range(len(W_WORLDS)))
            ax.set_xticklabels([f"{w[1:3]}·{'map' if w[-1] == 'W' else w[-1]}" for w in W_WORLDS],
                               fontsize=H.FS_LABEL)
            ax.set_xlim(-0.6, len(W_WORLDS) - 0.4)
            ax.set_ylim(-4, 104)
            ax.grid(axis="x", visible=False)
            ax.set_title(f"{SHORT_SCENE[scene]} · inj. {int(inj)}", fontsize=H.FS_LABEL + 1, loc="left")
            if j == 0:
                ax.set_ylabel(ylabel, fontsize=H.FS_LABEL)
    fig.supxlabel("world: map size · smell reach (squares, or the whole map)", fontsize=H.FS_BODY, y=0.03)
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], ls="", marker=MK[a], ms=8, color=W_COL[a], label=FG.alabel(a)) for a in AGENTS]
    hs.append(Line2D([], [], color=H.INK_2, lw=1.3, label="95% interval, within-run (checkpoint-to-checkpoint)"))
    fig.legend(handles=hs, loc="lower center", ncol=3, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.003))
    fig.tight_layout(rect=(0, 0.045, 1, 1), h_pad=1.3, w_pad=0.8)
    return fig, water_rows(D, W_WORLDS, True, "checkpoints summarised")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--fig-dir", required=True)
    ap.add_argument("--figure", required=True, choices=FIGS + WATER_FIGS)
    ap.add_argument("--world", choices=WORLDS, help="required for --figure traces")
    ap.add_argument("--map", choices=W_MAPS, help="required for --figure pond_traces")
    a = ap.parse_args(argv)
    H.apply()
    D = load(os.path.abspath(a.out_root))
    if a.figure in WATER_FIGS:
        if not json.load(open(os.path.join(os.path.abspath(a.out_root), "probes", "provenance.json"))).get("water"):
            raise SystemExit(f"--figure {a.figure} is for probe scenes with a pond; probes.py found none")
        if a.figure == "pond_traces":
            if not a.map:
                raise SystemExit("--figure pond_traces needs --map")
            fig, rows = fig_pond_traces(D, a.map)
            stem = f"f7_pond_traces__g{a.map}"
        elif a.figure == "pond_levels":
            fig, rows = fig_pond_window(D, "bush_hiding", "bush time before the\nfirst pond step (%)")
            stem = "f7_pond_levels"
        else:
            fig, rows = fig_pond_window(D, "pond_visit_share", "episodes reaching\nthe pond (%)")
            stem = "f7_pond_visits"
        FG.record_samples(os.path.abspath(a.fig_dir), stem, rows)
        FG.save(fig, os.path.abspath(a.fig_dir), stem)
        return
    if a.figure == "traces":
        if not a.world:
            raise SystemExit("--figure traces needs --world")
        fig, rows = fig_traces(D, a.world)
        stem = f"{STEM['traces']}__{a.world}"
    else:
        fig, rows = {"levels": fig_levels, "confusion": fig_confusion, "threat": fig_threat,
                     "budget": fig_budget, "training": fig_training, "other": fig_other}[a.figure](D)
        stem = STEM[a.figure]
    FG.record_samples(os.path.abspath(a.fig_dir), stem, rows)
    FG.save(fig, os.path.abspath(a.fig_dir), stem)


if __name__ == "__main__":
    main()
