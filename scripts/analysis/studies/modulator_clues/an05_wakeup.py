"""FIGURE an05 - B2 wake-up: when, during training, does the modulator start to matter?

WHAT IS PLOTTED.
  * Top, small multiples: the survival curve (mean episode length per checkpoint interval, from the
    training log) with each run's survival plateau marked, then one panel per registered headline
    wake-up measure (17 as registered: total-loss gradient share, per-term gradient shares, relative
    update size, contextual fraction rho and gain swing per modulated site, freeze cost of the gain
    and of the offset). One thin line per level-05 world; the orange dot is that run's wake point
    under the headline rule. Horizontal: training episodes (millions). Each panel has its own
    vertical scale.
  * Bottom, the lag summary: per measure, each run's wake point minus its survival plateau, in
    checkpoint positions (the registered lag scale); the shaded band is the rules' coincidence
    band. Level-05 worlds are dots, May-replication seeds are diamonds. Beside each measure, the
    across-worlds reading the evaluator wrote (sign test over the level-05 worlds), verbatim.
  * The registered per-run caveat, verbatim: no single run's wake point is evidence, so no per-run
    point carries a word - only a number.

WHAT IT READS. The `run_wakeup --summarise` outputs in one folder: `b2_reading.json`,
`curves/<run>.json` and `plateau.json` (default: results/analysis/algorithmic_null/
algorithmic_null_wakeup/). Nothing is recomputed: wake points, plateaus, lags and readings are the
driver's. May-replication runs train for 1.5 M episodes on a 15-checkpoint grid, so their curves are
not drawn on the level-05 axes; they appear in the lag summary.

    python scripts/analysis/studies/modulator_clues/an05_wakeup.py [--source <folder>/b2_reading.json] [--out ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json                                                                # noqa: E402
import math                                                                # noqa: E402
import numpy as np                                                         # noqa: E402
import matplotlib.pyplot as plt                                            # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

STEM = "an05_wakeup"
DEFAULT = os.path.join(C.RESULTS, "algorithmic_null_wakeup", "b2_reading.json")
NCOL = 4


def counts(r: dict) -> str:
    """The sign test's counts in words. k* is None when no number of worlds can reach the test's
    alpha, which with n_def = 0 simply means no world has a defined lag."""
    if not r["n_def"]:
        return "no world with a defined lag"
    base = f"{r['n_late']} late, {r['n_early']} early of {r['n_def']}"
    return base + ("; too few for the test" if r["k_star"] is None else f"; needs {r['k_star']}")


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
    band = float(C.param(rules, "B2.lag_coincident_max_intervals"))

    house.apply()
    n_small = len(names) + 1
    n_rows = math.ceil(n_small / NCOL)
    lag_h = max(0.52 * len(names), 1.6)     # two 11-pt label lines per measure fit in 0.52 in
    below = 3.4                              # inches under the lag panel: x label, legend, footer
    H = 2.45 * n_rows + lag_h + below + 0.4
    fig = plt.figure(figsize=(11.0, H))
    gs = fig.add_gridspec(n_rows + 1, NCOL, height_ratios=[1.0] * n_rows + [lag_h / 1.75],
                          hspace=0.85, wspace=0.28, left=0.07, right=0.99,
                          top=1 - 0.3 / H, bottom=below / H)
    panels = [fig.add_subplot(gs[i // NCOL, i % NCOL]) for i in range(n_small)]
    for i in range(n_small, n_rows * NCOL):
        C.blank(fig.add_subplot(gs[i // NCOL, i % NCOL])).set_visible(False)
    # survival + plateau
    ax = panels[0]
    for lab in l05:
        p = plat[lab]
        # the plateau curve is binned on the run's checkpoints: the grid of any unanchored curve
        run_x = next((c["x"] for c in curves[lab]["curves"].values() if not c["anchored"]), None)
        if run_x is None or len(run_x) != len(p["curve"]):
            raise SystemExit(f"{lab}: cannot place the plateau table's survival curve on the grid")
        ax.plot(np.array(run_x) / 1e6, p["curve"], color=house.INK_2, lw=0.8, alpha=0.55)
        if math.isfinite(p["t_plateau_episode"]):
            y = p["curve"][run_x.index(p["t_plateau_episode"])]
            ax.plot(p["t_plateau_episode"] / 1e6, y, "o", color=C.ORD, ms=4.5)
    ax.set_title("survival (steps); blue = plateau", fontsize=house.FS_LABEL, color=house.INK,
                 loc="left", pad=5)
    n_def_pts = n_all = 0
    reasons = {}
    for ax, name in zip(panels[1:], names):
        for lab in l05:
            c = curves[lab]["curves"][name]
            x = np.array(c["x"]) / 1e6
            ax.plot(x, c["m"], color=house.INK_2, lw=0.8, alpha=0.55)
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
            ax.set_xlim(0, max(max(curves[l]["curves"][names[0]]["x"]) for l in l05) / 1e6 * 1.02)
    for ax in panels[-NCOL:]:
        ax.set_xlabel("training episodes (M)", fontsize=house.FS_LABEL)

    # ---- lag summary --------------------------------------------------------------------------
    lg = fig.add_subplot(gs[n_rows, :2])
    tx = C.blank(fig.add_subplot(gs[n_rows, 2:]))
    ys = np.arange(len(names))[::-1]
    from matplotlib.transforms import blended_transform_factory
    row_tf = blended_transform_factory(tx.transAxes, lg.transData)   # text on the lag rows
    lg.axvspan(-band, band, color=C.ORD, alpha=0.14, lw=0)
    lg.axvline(0, color=house.RULE, lw=1)
    n_lag = 0
    for y, name in zip(ys, names):
        for grp, mk, col, dy in ((l05, "o", house.INK_2, 0.12), (may, "D", C.MOD, -0.18)):
            d = [wp[l][name]["lag"]["delta_positions"] for l in grp]
            d = [v for v in d if v is not None]
            n_lag += len(d)
            if not d:
                continue
            ax_j = np.linspace(-0.08, 0.08, len(d)) if len(d) > 1 else [0.0]
            lg.plot(d, [y + dy + j for j in ax_j], mk, color=col, ms=4, alpha=0.8, ls="")
        r = doc["reading"][name]
        if C.allowed(doc):
            w = C.verdict(doc, r["reading"], test)
            txt = w if test else f"{w}\n{counts(r)}"
        else:
            txt = doc["verdict_statement"]
        tx.text(0.0, y, "\n".join(C.wrap(t, 60) for t in txt.split("\n")), transform=row_tf, ha="left",
                va="center", fontsize=house.FS_LABEL, color=house.INK, linespacing=1.1)
    lg.set_yticks(ys)
    lg.set_yticklabels(names, fontsize=house.FS_LABEL)
    lg.set_ylim(-0.7, len(names) - 0.3)
    lg.grid(axis="x", color=house.TICK_LINE, lw=0.9)
    lg.grid(axis="y", visible=False)
    lg.set_xlabel("wake point minus survival plateau (checkpoint positions)", fontsize=house.FS_LABEL)
    lg.set_title("lag per run; shaded = coincidence band", fontsize=house.FS_LABEL, color=house.INK,
                 loc="left", pad=5)
    tx.set_title("across-worlds reading (level-05 sign test)", fontsize=house.FS_LABEL,
                 color=house.INK, loc="left", pad=5)
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=house.INK_2, lw=1, label="one level-05 world"),
          Line2D([], [], marker="o", ls="", color=C.MOD, label="wake point (headline rule)"),
          Line2D([], [], marker="o", ls="", color=C.ORD, label="survival plateau"),
          Line2D([], [], marker="o", ls="", color=house.INK_2, label="lag, level-05 world"),
          Line2D([], [], marker="D", ls="", color=C.MOD, label="lag, May seed")]
    fig.legend(handles=hs, loc="upper center", bbox_to_anchor=(0.5, (below - 0.75) / H), ncol=5,
               frameon=False, fontsize=house.FS_LABEL)
    C.footer(fig, doc, test, y=(below - 1.15) / H, width=150,
             extra="Registered per-run caveat: " + doc["per_run_caveat"])

    fb = doc.get("b2_family_bound", {})
    rows = [dict(what="level-05 worlds drawn as curves", used=len(l05), total=len(l05),
                 note="16 registered; a partial sweep has fewer"),
            dict(what="May-replication seeds drawn as curves", used=0, total=len(may),
                 note="1.5 M episodes on a 15-checkpoint grid: shown in the lag summary only"),
            dict(what="runs summarised against the registered family", used=len(labels),
                 total=int(fb.get("family_size", 0)) // max(len(names), 1),
                 note="b2_family_bound.family_size / headline curves"),
            dict(what="headline curves with a defined wake point", used=n_def_pts, total=n_all,
                 note="undefined: " + (", ".join(f"{k} ({v})" for k, v in sorted(reasons.items())) or "none")),
            dict(what="headline curves with a defined lag (drawn in the lag summary)", used=n_lag, total=n_all,
                 note="a lag needs both a wake point and a plateau"),
            dict(what="points per level-05 curve", used=len(curves[l05[0]]["curves"][names[1]]["x"]) if l05 else 0,
                 total=len(curves[l05[0]]["curves"][names[1]]["x"]) if l05 else 0,
                 note="every saved checkpoint plus step 0 where anchorable; nothing thinned")]
    C.write_data(STEM, out, doc, a.source, test, rows)
    C.finish(fig, STEM, out)


if __name__ == "__main__":
    main()
