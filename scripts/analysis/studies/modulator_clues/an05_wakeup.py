"""FIGURE an05 - B2 wake-up: when, during training, does the modulator start to matter?

WHAT IS PLOTTED.
  * Top, small multiples: the survival curve (mean episode length per checkpoint interval, from the
    training log) with each run's survival plateau marked, then one panel per registered headline
    wake-up measure (17 as registered: total-loss gradient share, per-term gradient shares, relative
    update size, contextual fraction rho and gain swing per modulated site, freeze cost of the gain
    and of the offset). One thin line per level-05 world; the orange dot is that run's wake point
    under the headline rule. Horizontal: training episodes (millions). Each panel has its own
    vertical scale. After the swing panels, one extra panel: the DESCRIPTIVE CONTROL (below).
  * Bottom, the lag summary: per measure, each run's wake point minus its survival plateau, in
    checkpoint positions (the registered lag scale); the shaded band is the rules' coincidence
    band. Level-05 worlds are dots, May-replication seeds are diamonds. Beside each measure, the
    across-worlds reading the evaluator wrote (sign test over the level-05 worlds), verbatim, then
    descriptive facts the reading alone hides (B2 verdict gate, docs/reviews/plan_b2_wakeup_verdict.md):
      - the direction of each world's change (C1: rho FALLS from its untrained value);
      - where no timing is named, that the net change is inside the curve's own noise band, i.e. the
        rule could not time it - not that nothing changed (M3);
      - for the freeze costs, the post-plateau cost LEVEL in survival steps and the number of worlds
        where it is negative (C3), with no verdict word;
      - for the gain swing, that its per-site curves are one measure: the within-run correlation of
        the site curves (M1).
  * The registered per-run caveat, verbatim: no single run's wake point is evidence, so no per-run
    point carries a word - only a number.

THE DESCRIPTIVE CONTROL (review finding C2; not registered, decides nothing). The main network's
total parameter norm, read from the point files (`update_size.main_prev_norm`, the norm at the start
of each checkpoint interval, so the curve runs from step 0 to the second-to-last checkpoint), is
put through the SAME registered crossing rule and lag (`scripts/analysis/nmn/wakeup.t_cross` and
`lag`, with every constant from the rules' `parameters.B2` at the output's sha). It shows how any
weight norm reads under this rule in this trainer, beside the gain swing, which is a weights-only
ceiling. Its per-world lags are drawn in their own row; it carries no reading word.

WHAT IT READS. The `run_wakeup --summarise` outputs in one folder: `b2_reading.json`,
`curves/<run>.json`, `plateau.json` and, for the control only, `points/<run>/*.json` (default:
results/analysis/algorithmic_null/algorithmic_null_wakeup/). The registered readings, wake points,
plateaus and lags are the driver's; the descriptive additions above are computed here from the
driver's curves and point files. May-replication runs train for 1.5 M episodes on a 15-checkpoint
grid, so their curves are not drawn on the level-05 axes; they appear in the lag summary.

    python scripts/analysis/studies/modulator_clues/an05_wakeup.py [--source <folder>/b2_reading.json] [--out ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glob                                                                # noqa: E402
import itertools                                                           # noqa: E402
import json                                                                # noqa: E402
import math                                                                # noqa: E402
import numpy as np                                                         # noqa: E402
import matplotlib.pyplot as plt                                            # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

sys.path.insert(0, C.ROOT)
from scripts.analysis.nmn import wakeup as W                               # noqa: E402  (pure numpy)

STEM = "an05_wakeup"
DEFAULT = os.path.join(C.RESULTS, "algorithmic_null_wakeup", "b2_reading.json")
NCOL = 4
CONTROL = "main-network weight norm"
CTRL_TAG = "descriptive control — not registered"
ROW_IN = 0.62                                  # lag-panel inches per measure: three 11-pt lines


def counts(r: dict) -> str:
    """The sign test's counts in words. k* is None when no number of worlds can reach the test's
    alpha, which with n_def = 0 simply means no world has a defined lag."""
    base = f"{r['n_late']} late, {r['n_early']} early of {r['n_def']}"
    return base + ("; too few for the test" if r["k_star"] is None else f"; needs {r['k_star']}")


def directions(ds: list) -> str:
    """Each world's direction of change under the rule (rising / falling), counted."""
    n = len(ds)
    c = {d: ds.count(d) for d in set(ds) if d}
    return ", ".join(f"{d} {k}/{n}" for d, k in sorted(c.items(), key=lambda t: -t[1]))


def control_curve(folder: str, label: str, cks: list, t_plateau: float, B2: dict, band: float) -> dict:
    """The descriptive control for one run: the main network's parameter norm at the start of each
    checkpoint interval, through the registered crossing rule and lag."""
    pts = []
    for f in glob.glob(os.path.join(folder, "points", label, "*.json")):
        if os.path.basename(f).startswith("_"):
            continue
        us = json.load(open(f))["measures"].get("update_size")
        if us:
            pts.append((float(us["interval"][0]), float(us["main_prev_norm"])))
    pts.sort()
    x = [p[0] for p in pts]
    want = [0.0] + [float(c) for c in cks[:-1]]
    if x != want:
        raise SystemExit(f"{label}: the stored main-network norms are not on the run's grid "
                         f"(step 0 and every checkpoint but the last)")
    m = [p[1] for p in pts]
    kw = {k: B2[k] for k in ("sustain", "final_k", "noise_k", "min_noise_points",
                             "noise_window_divisor", "noise_window_max_fraction")}
    res = W.t_cross(x, m, mode=B2["threshold_mode_headline"], f=B2["f"], anchored=True,
                    label=f"{label} / {CONTROL}", **kw)
    lg = W.lag(res.t, t_plateau, cks, band)
    return {"x": x, "m": m, "t": res.t, "direction": res.direction, "reason": res.reason,
            "delta": lg["delta_positions"], "n_points": len(x), "n_grid": len(cks) + 1}


def main():
    a = C.cli(__doc__, DEFAULT)
    doc = C.load(a.source, policy_from_rules=True)
    test = C.is_test_input(a.source, doc)
    out = C.check_out(a.out, test)
    folder = os.path.dirname(os.path.abspath(a.source))
    plateau = json.load(open(os.path.join(folder, "plateau.json")))
    plat = {r["label"]: r for r in plateau["runs"]}
    wp = doc["per_run_wake_points"]
    labels = list(wp)
    curves = {}
    for lab in labels:
        cj = json.load(open(os.path.join(folder, "curves", f"{lab}.json")))
        if cj["decision_rules"]["sha256"] != doc["decision_rules"]["sha256"]:
            raise SystemExit(f"{lab}: curves file and b2_reading.json carry different rules shas")
        curves[lab] = cj
    names = list(doc["headline_curves"])
    l05 = [l for l in labels if not curves[l]["continual"]]
    may = [l for l in labels if curves[l]["continual"]]
    rules = C.rules_at(doc["decision_rules"]["sha256"])
    B2 = C.param(rules, "B2")
    band = float(B2["lag_coincident_max_intervals"])
    measure = {n: curves[labels[0]]["curves"][n]["measure"] for n in names}

    def run_cks(lab):         # the run's checkpoints: the grid of any unanchored curve
        return next(c["x"] for c in curves[lab]["curves"].values() if not c["anchored"])

    # ---- descriptive additions (review of the B2 verdict; none registered) -------------------
    ctrl = {lab: control_curve(folder, lab, run_cks(lab), float(curves[lab]["t_plateau_episode"]),
                               B2, band) for lab in labels}
    swing_names = [n for n in names if measure[n] == "swing"]
    swing_r = []
    for lab in l05:
        cs = [np.asarray(curves[lab]["curves"][n]["m"]) for n in swing_names]
        swing_r += [float(np.corrcoef(p, q)[0, 1]) for p, q in itertools.combinations(cs, 2)]
    freeze_cost = {}
    for n in names:
        if measure[n] != "freeze":
            continue
        per = []
        for lab in l05:
            c, t = curves[lab]["curves"][n], float(curves[lab]["t_plateau_episode"])
            post = [v for xv, v in zip(c["x"], c["m"]) if xv > t]
            if post:
                per.append(float(np.mean(post)))
        freeze_cost[n] = per

    house.apply()
    swing_end = max(i for i, n in enumerate(names) if n in swing_names) + 1 if swing_names else len(names)
    panel_names = names[:swing_end] + [CONTROL] + names[swing_end:]
    n_small = len(panel_names) + 1
    n_rows = math.ceil(n_small / NCOL)
    n_lag = len(names) + 1
    lag_h = max(ROW_IN * n_lag, 1.6)
    below = 3.6                              # inches under the lag panel: x label, legend, footer
    top_h = 2.3 * n_rows                     # small multiples
    gap = 1.0                                # between the small multiples' x labels and the lag title
    H = 0.3 + top_h + gap + lag_h + below
    fig = plt.figure(figsize=(11.0, H))
    # two grids, so the tall lag panel does not inflate the small multiples' spacing
    gs = fig.add_gridspec(n_rows, NCOL, hspace=0.85, wspace=0.28, left=0.07, right=0.99,
                          top=1 - 0.3 / H, bottom=(below + lag_h + gap) / H)
    gl = fig.add_gridspec(1, NCOL, wspace=0.28, left=0.07, right=0.99,
                          top=(below + lag_h) / H, bottom=below / H)
    panels = [fig.add_subplot(gs[i // NCOL, i % NCOL]) for i in range(n_small)]
    for i in range(n_small, n_rows * NCOL):
        C.blank(fig.add_subplot(gs[i // NCOL, i % NCOL])).set_visible(False)
    # survival + plateau
    ax = panels[0]
    for lab in l05:
        p = plat[lab]
        run_x = run_cks(lab)
        if len(run_x) != len(p["curve"]):
            raise SystemExit(f"{lab}: cannot place the plateau table's survival curve on the grid")
        ax.plot(np.array(run_x) / 1e6, p["curve"], color=house.INK_2, lw=0.8, alpha=0.55)
        if math.isfinite(p["t_plateau_episode"]):
            y = p["curve"][run_x.index(p["t_plateau_episode"])]
            ax.plot(p["t_plateau_episode"] / 1e6, y, "o", color=C.ORD, ms=4.5)
    ax.set_title("survival (steps); blue = plateau", fontsize=house.FS_LABEL, color=house.INK,
                 loc="left", pad=5)
    n_def_pts = n_all = 0
    reasons = {}
    for ax, name in zip(panels[1:], panel_names):
        if name == CONTROL:
            for lab in l05:
                c = ctrl[lab]
                ax.plot(np.array(c["x"]) / 1e6, c["m"], color=house.INK_2, lw=0.8, alpha=0.55)
                if math.isfinite(c["t"]):
                    ax.plot(c["t"] / 1e6, c["m"][c["x"].index(c["t"])], "s", color=house.INK, ms=4.5)
            ax.set_title("main-net weight norm\ncontrol, not registered", fontsize=house.FS_LABEL,
                         color=house.INK,
                         loc="left", pad=5)
            continue
        for lab in l05:
            c = curves[lab]["curves"][name]
            ax.plot(np.array(c["x"]) / 1e6, c["m"], color=house.INK_2, lw=0.8, alpha=0.55)
        ax.set_title(name, fontsize=house.FS_LABEL, color=house.INK, loc="left", pad=5)
        for lab in labels:
            h = wp[lab][name]["headline"]
            n_all += 1
            if h["t"] is not None and math.isfinite(h["t"]):
                n_def_pts += 1
                if lab in l05:
                    c = curves[lab]["curves"][name]
                    ax.plot(h["t"] / 1e6, c["m"][c["x"].index(h["t"])], "o", color=C.MOD, ms=4.5)
            else:
                reasons[h["reason"]] = reasons.get(h["reason"], 0) + 1
    for ax in panels:
        ax.tick_params(labelsize=house.FS_LABEL)
        ax.locator_params(axis="both", nbins=4)
        if l05:                              # training starts at 0: no negative episode ticks
            ax.set_xlim(0, max(max(run_cks(l)) for l in l05) / 1e6 * 1.02)
    for ax in panels[-NCOL:]:
        ax.set_xlabel("training episodes (M)", fontsize=house.FS_LABEL)

    # ---- lag summary --------------------------------------------------------------------------
    lg = fig.add_subplot(gl[0, :2])
    tx = C.blank(fig.add_subplot(gl[0, 2:]))
    rows_lag = names + [CONTROL]
    ys = np.arange(len(rows_lag))[::-1]
    from matplotlib.transforms import blended_transform_factory
    row_tf = blended_transform_factory(tx.transAxes, lg.transData)   # text on the lag rows
    lg.axvspan(-band, band, color=C.ORD, alpha=0.14, lw=0)
    lg.axvline(0, color=house.RULE, lw=1)
    n_lag_pts = 0
    first_swing = swing_names[0] if swing_names else None
    for y, name in zip(ys, rows_lag):
        is_ctrl = name == CONTROL
        for grp, mk, col, dy in ((l05, "s" if is_ctrl else "o", house.INK if is_ctrl else house.INK_2, 0.12),
                                 (may, "D", C.MOD, -0.18)):
            d = [ctrl[l]["delta"] if is_ctrl else wp[l][name]["lag"]["delta_positions"] for l in grp]
            d = [v for v in d if v is not None]
            if not is_ctrl:
                n_lag_pts += len(d)
            if not d:
                continue
            jit = np.linspace(-0.08, 0.08, len(d)) if len(d) > 1 else [0.0]
            lg.plot(d, [y + dy + j for j in jit], mk, color=col, ms=4, alpha=0.8, ls="")
        n = len(l05)
        if is_ctrl:
            dl = [ctrl[l]["delta"] for l in l05 if ctrl[l]["delta"] is not None]
            txt = (f"{CTRL_TAG}\nafter the band in {sum(v > band for v in dl)}/{n}, before it in "
                   f"{sum(v < -band for v in dl)}/{n} \u00b7 "
                   f"{directions([ctrl[l]['direction'] for l in l05])}")
        else:
            r = doc["reading"][name]
            if not C.allowed(doc):
                txt = doc["verdict_statement"]
            elif test:
                txt = C.verdict(doc, r["reading"], test)
            else:
                lines = [C.verdict(doc, r["reading"], test)]
                dirs = [wp[l][name]["headline"]["direction"] for l in l05]
                if r["n_def"]:
                    lines.append(f"{counts(r)} \u00b7 {directions(dirs)}")
                else:
                    noise = sum(wp[l][name]["headline"]["reason"] == W.R_NOISE for l in l05)
                    lines.append(f"no timing reading: change within its noise in {noise}/{n}")
                if name in freeze_cost and freeze_cost[name]:
                    fc = freeze_cost[name]
                    lines.append(f"not registered: post-plateau cost {np.mean(fc):+.0f} steps, "
                                 f"below 0 in {sum(v < 0 for v in fc)}/{len(fc)}")
                if name == first_swing and swing_r:
                    lines.append(f"{len(swing_names)} sites, one measure: within-run r "
                                 f"{min(swing_r):.2f}–{max(swing_r):.2f}")
                txt = "\n".join(lines)
        tx.text(0.0, y, "\n".join(C.wrap(t, 66) for t in txt.split("\n")), transform=row_tf,
                ha="left", va="center", fontsize=house.FS_LABEL,
                color=house.INK_2 if is_ctrl else house.INK, linespacing=1.1)
    lg.set_yticks(ys)
    lg.set_yticklabels(rows_lag[:-1] + [f"{CONTROL} (control)"], fontsize=house.FS_LABEL)
    lg.set_ylim(-0.7, len(rows_lag) - 0.3)
    lg.grid(axis="x", color=house.TICK_LINE, lw=0.9)
    lg.grid(axis="y", visible=False)
    lg.set_xlabel("wake point minus survival plateau (checkpoint positions)", fontsize=house.FS_LABEL)
    lg.set_title("lag per run; shaded = coincidence band", fontsize=house.FS_LABEL, color=house.INK,
                 loc="left", pad=5)
    tx.set_title("across-worlds reading (level-05 sign test), then descriptive facts",
                 fontsize=house.FS_LABEL, color=house.INK, loc="left", pad=5)
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=house.INK_2, lw=1, label="one level-05 world"),
          Line2D([], [], marker="o", ls="", color=C.MOD, label="wake point (headline rule)"),
          Line2D([], [], marker="o", ls="", color=C.ORD, label="survival plateau"),
          Line2D([], [], marker="o", ls="", color=house.INK_2, label="lag, level-05 world"),
          Line2D([], [], marker="D", ls="", color=C.MOD, label="lag, May seed"),
          Line2D([], [], marker="s", ls="", color=house.INK, label=f"{CONTROL}: {CTRL_TAG}")]
    fig.legend(handles=hs, loc="upper center", bbox_to_anchor=(0.5, (below - 0.75) / H), ncol=3,
               frameon=False, fontsize=house.FS_LABEL)
    C.footer(fig, doc, test, y=(below - 1.35) / H, width=150,
             extra="Registered per-run caveat: " + doc["per_run_caveat"])

    fb = doc.get("b2_family_bound", {})
    ctrl_def = sum(c["delta"] is not None for c in ctrl.values())
    c0 = ctrl[labels[0]]
    rows = [dict(what="level-05 worlds drawn as curves", used=len(l05), total=len(l05),
                 note="16 registered; a partial sweep has fewer"),
            dict(what="May-replication seeds drawn as curves", used=0, total=len(may),
                 note="1.5 M episodes on a 15-checkpoint grid: shown in the lag summary only"),
            dict(what="runs summarised against the registered family", used=len(labels),
                 total=int(fb.get("family_size", 0)) // max(len(names), 1),
                 note="b2_family_bound.family_size / headline curves"),
            dict(what="headline curves with a defined wake point", used=n_def_pts, total=n_all,
                 note="undefined: " + (", ".join(f"{k} ({v})" for k, v in sorted(reasons.items())) or "none")),
            dict(what="headline curves with a defined lag (drawn in the lag summary)", used=n_lag_pts, total=n_all,
                 note="a lag needs both a wake point and a plateau"),
            dict(what="points per level-05 curve", used=len(curves[l05[0]]["curves"][names[1]]["x"]) if l05 else 0,
                 total=len(curves[l05[0]]["curves"][names[1]]["x"]) if l05 else 0,
                 note="every saved checkpoint plus step 0 where anchorable; nothing thinned"),
            dict(what=f"control ({CONTROL}): runs with a defined lag", used=ctrl_def, total=len(labels),
                 note=f"{CTRL_TAG}; registered crossing rule and lag applied to update_size.main_prev_norm"),
            dict(what=f"control: points per curve ({labels[0]})", used=c0["n_points"], total=c0["n_grid"],
                 note="the norm is stored at each interval's start, so the last checkpoint's norm is missing"),
            dict(what="gain-swing site pairs correlated within a run", used=len(swing_r), total=len(swing_r),
                 note=f"{len(swing_names)} sites x {len(l05)} level-05 worlds; Pearson r of the site curves"),
            ] + [dict(what=f"{n}: level-05 worlds with a post-plateau cost", used=len(v), total=len(l05),
                      note="descriptive mean of the curve after the run's plateau; not a registered test")
                 for n, v in freeze_cost.items()]
    C.write_data(STEM, out, doc, a.source, test, rows)
    C.finish(fig, STEM, out)


if __name__ == "__main__":
    main()
