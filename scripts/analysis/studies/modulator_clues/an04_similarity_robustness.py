"""FIGURE an04 - A1 robustness: does the modulated-vs-ordinary gap survive other ways of scoring?

WHAT IS PLOTTED. Descriptive columns only; none of them decides anything. One row per verdict
layer, one panel per scoring variant (as the driver lists them, e.g. the registered scoring, rare
predictor units excluded, a floor on the standardisation scale, the unweighted mean of per-unit
R^2). Inside each panel, three strips, top to bottom:
  * the smaller of the two directions (the registered combination);
  * R^2(ordinary -> modulated): the ordinary layer predicts the modulated one;
  * R^2(modulated -> ordinary): the registered SUPPORTING READ, the one direction exactly invariant
    to the modulator's per-unit gain (rules revision P2).
Ordinary-ordinary pairs are blue (both directions in the directional strips), modulated-ordinary
pairs at different seeds orange, modulated-modulated hollow orange.

WHAT IT READS. `similarity_robustness.json` from `scripts/analysis/nmn/run_similarity_robustness.py`,
beside `similarity.json`. Per verdict layer and pair (`layers.<layer>.pairs.<A|B>`): `pair_set`, and
per variant (`all_columns`, `admitted`, `floored_scale`) the statistics `<weighted|unit_mean>_<a_to_b|
b_to_a|mutual>` = {point, q_lo, q_hi}. Pair names put the ordinary agent first in a
modulated-ordinary pair, so `b_to_a` is R^2(modulated -> ordinary). Four columns are drawn, named in
COLUMNS below: every column kept (the estimator the interim verdict was computed with), rare
predictor units left out (`admitted`, the current rules' estimator, revision P1), the floored
standardisation scale, and the unweighted mean of per-unit R^2. Points are drawn; the driver's
bootstrap quantiles are not. Nothing is recomputed.

    python scripts/analysis/studies/modulator_clues/an04_similarity_robustness.py [--source ...] [--out ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                                                         # noqa: E402
import matplotlib.pyplot as plt                                            # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

STEM = "an04_similarity_robustness"
DEFAULT = os.path.join(C.RESULTS, "algorithmic_null_mayrep_interim", "similarity_robustness.json")
STRIPS = (("mutual", 2.0, "smaller of both"), ("a_to_b", 1.0, "ordinary \u2192 modulated"),
          ("b_to_a", 0.0, "modulated \u2192 ordinary\n(supporting read)"))
#: (variant, statistic, column title) - the four descriptive columns, in drawing order
COLUMNS = (("all_columns", "weighted", "every unit kept (as the interim verdict)"),
           ("admitted", "weighted", "rare units excluded (current rules, P1)"),
           ("floored_scale", "weighted", "scale floored at the median unit SD"),
           ("all_columns", "unit_mean", "unweighted mean of per-unit R\u00b2"))


def validate(doc):
    for k in ("cell", "variants", "statistics", "layers", "status_of_these_numbers"):
        if k not in doc:
            raise SystemExit(f"{STEM}: robustness output has no '{k}' (run_similarity_robustness schema)")
    for v, stat, _ in COLUMNS:
        if v not in doc["variants"] or stat not in doc["statistics"]:
            raise SystemExit(f"{STEM}: the output lacks variant {v!r} or statistic {stat!r}")
    for layer, L in doc["layers"].items():
        for p, rec in L["pairs"].items():
            if "|" not in p or rec.get("pair_set") not in ("OO", "MO_diff", "MO_same", "MM"):
                raise SystemExit(f"{STEM}: {layer} {p}: bad pair name or pair_set")
            if rec["pair_set"] in ("MO_diff", "MO_same") and not rec["a"].startswith("ordinary"):
                raise SystemExit(f"{STEM}: {layer} {p}: a modulated-ordinary pair must put the "
                                 f"ordinary agent first (the direction convention)")
            for v, stat, _ in COLUMNS:
                for d in ("a_to_b", "b_to_a", "mutual"):
                    if "point" not in rec["variants"][v].get(f"{stat}_{d}", {}):
                        raise SystemExit(f"{STEM}: {layer} {p}: no {v} {stat}_{d} point")


def main():
    a = C.cli(__doc__, DEFAULT)
    doc = C.load(a.source)
    test = C.is_test_input(a.source, doc)
    out = C.check_out(a.out, test)
    validate(doc)
    cols = COLUMNS
    layers = list(doc["layers"])

    house.apply()
    fig, axs = plt.subplots(len(layers), len(cols), figsize=(11.0, 1.9 * len(layers) + 2.6),
                            squeeze=False)
    fig.subplots_adjust(left=0.19, right=0.99, top=0.9, bottom=0.2, hspace=0.75, wspace=0.18)
    drawn = {"OO": 0, "MO_diff": 0, "MM": 0, "MO_same": 0}
    for r, layer in enumerate(layers):
        pairs = doc["layers"][layer]["pairs"]
        for k, (var, stat, ctitle) in enumerate(cols):
            ax = axs[r, k]
            for key, y, _ in STRIPS:
                for ps, col, face, dy in (("OO", C.ORD, C.ORD, 0.18), ("MO_diff", C.MOD, C.MOD, 0.0),
                                          ("MM", C.MOD, "white", -0.18)):
                    vals = []
                    for p, v in pairs.items():
                        if v["pair_set"] != ps:
                            continue
                        row = v["variants"][var]
                        if key != "mutual" and ps in ("OO", "MM"):   # same-arm: both directions
                            vals += [row[f"{stat}_a_to_b"]["point"], row[f"{stat}_b_to_a"]["point"]]
                        else:
                            vals.append(row[f"{stat}_{key}"]["point"])
                    ax.plot(vals, [y + dy] * len(vals), "o", ms=4.5, mfc=face, mec=col, mew=1.2,
                            alpha=0.9)
            ax.set_ylim(-0.6, 2.6)
            ax.set_yticks([s[1] for s in STRIPS])
            ax.set_yticklabels([s[2] for s in STRIPS] if k == 0 else [], fontsize=house.FS_LABEL)
            ax.grid(axis="x", color=house.TICK_LINE, lw=0.9)
            ax.grid(axis="y", visible=False)
            ax.tick_params(axis="x", labelsize=house.FS_LABEL)
            from matplotlib.ticker import MaxNLocator
            ax.xaxis.set_major_locator(MaxNLocator(nbins=2, min_n_ticks=2))
            t = (C.wrap(ctitle, 24) + "\n") if r == 0 else ""
            ax.set_title(t + (layer if k == 0 else ""), fontsize=house.FS_LABEL, color=house.INK,
                         loc="left", pad=6)
            if r == len(layers) - 1:
                ax.set_xlabel("held-out R²", fontsize=house.FS_LABEL)
        for v in pairs.values():
            drawn[v["pair_set"]] += 1
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], marker="o", ls="", color=C.ORD, label="ordinary–ordinary pair"),
          Line2D([], [], marker="o", ls="", color=C.MOD, label="modulated–ordinary, different seeds"),
          Line2D([], [], marker="o", ls="", mfc="white", mec=C.MOD, label="modulated–modulated pair")]
    fig.legend(handles=hs, loc="lower center", bbox_to_anchor=(0.55, 0.12), ncol=3, frameon=False,
               fontsize=house.FS_LABEL)
    C.footer(fig, doc, test, y=0.1, width=150,
             extra=f"{doc['status_of_these_numbers']}: these columns decide nothing; the verdict is "
                   f"Figure A1's. Each panel has its own horizontal range.")

    n_layers = len(layers)
    rows = []
    for ps, what in (("OO", "ordinary\u2013ordinary pairs"), ("MO_diff", "modulated\u2013ordinary pairs, different seeds"),
                     ("MM", "modulated\u2013modulated pairs")):
        rows.append(dict(what=f"{what} (summed over layers)", used=drawn[ps], total=drawn[ps],
                         note=f"every pair in the output, {n_layers} layers"))
    if drawn["MO_same"]:
        rows.append(dict(what="same-seed pairs (summed over layers)", used=0, total=drawn["MO_same"],
                         note="in the output, not drawn: the same-seed comparison is Figure A3"))
    nv = len(doc["variants"]) * len([k for k in doc["statistics"] if k != "mutual"])
    rows.append(dict(what="variant x statistic columns drawn", used=len(cols), total=nv,
                     note="drawn: " + "; ".join(f"{v}/{st}" for v, st, _ in cols)
                     + " (the other variant x statistic pairs are in the output, not drawn)"))
    dropped = total = 0
    for L in doc["layers"].values():
        for rec in L["pairs"].values():
            for f in rec["variants"]["admitted"].get("fits_a_to_b", []) + \
                     rec["variants"]["admitted"].get("fits_b_to_a", []):
                dropped += int(f.get("n_dropped") or 0)
                total += int(f.get("n_columns") or 0) + int(f.get("n_dropped") or 0)
    if total:
        rows.append(dict(what="predictor columns left out as rare, summed over admitted fits",
                         used=dropped, total=total, note="the rare-units-excluded column only"))
    lag = doc.get("row_lag_control") or {}
    if lag:
        rows.append(dict(what="pairs with a recorded cross-agent row-lag control", used=len(lag),
                         total=len(lag), note="the driver raises on a failing pair (rows misaligned), "
                                              "so every recorded pair passed"))
    C.write_data(STEM, out, doc, a.source, test, rows)
    C.finish(fig, STEM, out)


if __name__ == "__main__":
    main()
