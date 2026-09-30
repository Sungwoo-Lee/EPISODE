"""FIGURE an01 - A1 layer similarity: is modulated-vs-ordinary as alike as ordinary-vs-ordinary?

WHAT IS PLOTTED. One row per verdict layer of the network. Two panels per row: the registered
primary statistic (mutual linear predictivity, the smaller of the two directions' held-out R^2)
and linear CKA. In each panel, from top to bottom:
  * the ordinary-vs-ordinary pairs (different seeds), with the yardstick band [L, U] shaded - the
    band every verdict is judged against;
  * the six modulated-vs-ordinary pairs at different seeds, each with its bootstrap interval;
  * the bootstrap interval of the mean of those six (the verdict reads it against L);
  * the modulated-vs-modulated pairs - the qualifier the evaluator attaches when they, too, sit
    below the band (the verdict gate's main caveat: "the modulated agents also differ among
    themselves");
  * the untrained-network pairs, the floor that decides whether the statistic is informative.
The left column prints the evaluator's layer verdict and qualifier, verbatim.

WHAT IT READS. `similarity.json` from `scripts/analysis/nmn/run_similarity.py` (default: the
interim May-replication output). Nothing is recomputed. Verdict words come only from the output's
`evaluation.A1`, and only when its policy allows them (`_an_common.verdict`).

    python scripts/analysis/studies/modulator_clues/an01_similarity_layers.py [--source ...] [--out ...]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                                                         # noqa: E402
import matplotlib.pyplot as plt                                            # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

STEM = "an01_similarity_layers"
DEFAULT = os.path.join(C.RESULTS, "algorithmic_null_mayrep", "similarity.json")
INTERIM = os.path.join(C.RESULTS, "algorithmic_null_mayrep_interim", "similarity.json")
LAYER_NAME = {"enc.out": "encoder output", "rnn.state": "memory state (GRU carry)",
              "rnn.out": "memory output", "actor.out": "actor hidden layer",
              "critic.out": "critic hidden layer"}
STATS = (("predictivity", "MUTUAL LINEAR PREDICTIVITY (primary)"),
         ("cka", "LINEAR CKA (beside it)"))
ROWS = (("OO", 4.0), ("MO_diff", 3.0), ("mean", 2.0), ("MM", 1.0), ("UNTRAINED", 0.0))


def changed_phrase(doc) -> str:
    """The wording the rules prescribe when an interim and an evidence verdict disagree, read from
    the rules' interim policy (never typed here)."""
    rule = C.rules_at(doc["decision_rules"]["sha256"])["evidence_status"]["interim"]["rule"]
    m = re.search(r'worded as "([^"]+)"', rule)
    if not m:
        raise SystemExit(f"{STEM}: the rules' interim policy names no wording for a disagreement")
    return m.group(1)


def primary_cell(doc):
    cells = [c for c in doc["cells"] if c.get("primary")]
    if len(cells) != 1:
        raise SystemExit(f"{STEM}: expected one primary cell, found {len(cells)}")
    return cells[0]


def main():
    a = C.cli(__doc__, DEFAULT, extra=[("--interim", dict(
        default=INTERIM, help="an interim similarity.json whose layer verdicts are shown beside the "
                              "evidence ones, as the rules require when they differ; '' for none"))])
    doc = C.load(a.source)
    inter = None
    if a.interim and doc["evidence_status"] == "evidence":
        inter = C.load(a.interim)
        if inter["evidence_status"] != "interim":
            raise SystemExit(f"{STEM}: --interim must be an interim output")
    changed = changed_phrase(doc) if inter else None
    ia1 = (((inter or {}).get("evaluation") or {}).get("A1") or {}).get("layers") or {}
    test = C.is_test_input(a.source, doc)
    out = C.check_out(a.out, test)
    cell = primary_cell(doc)
    sets = cell["pair_sets"]
    if not sets.get("OO"):
        raise SystemExit(f"{STEM}: this output has no ordinary-vs-ordinary pairs (no yardstick); "
                         f"a pilot output is shown by an06_pilot_controls")
    layers = list(cell["layers"])
    ev = doc.get("evaluation") or {}
    summ = ev.get("summaries") or {}
    a1 = (ev.get("A1") or {}).get("layers") or {}

    house.apply()
    fig = plt.figure(figsize=(11.0, 3.0 * len(layers) + 1.6))
    gs = fig.add_gridspec(len(layers), 3, width_ratios=[1.05, 1.5, 1.5], wspace=0.22, hspace=0.6,
                          left=0.01, right=0.99, top=0.95, bottom=0.12)
    nonfinite, entries = 0, 0
    for r, layer in enumerate(layers):
        tx = C.blank(fig.add_subplot(gs[r, 0]))
        head = f"{layer}\n{LAYER_NAME.get(layer, '')}"
        if C.allowed(doc) and layer in a1:
            w = C.verdict(doc, a1[layer]["verdict"], test)
            lead = "end of training: " if inter else "layer verdict: "
            body = lead + w
            if a1[layer].get("qualifier") and not test:
                body += "\nqualifier: " + a1[layer]["qualifier"]
            if inter and layer in ia1 and not test:
                wi = C.verdict(inter, ia1[layer]["verdict"])
                body += "\nend of stage 1 (interim): " + wi
                if C.strip_prefix(inter, wi) != w:
                    body += "\n" + changed
        else:
            body = doc["verdict_statement"]
        tx.set_title(head, fontsize=house.FS_BODY, color=house.INK, loc="left", pad=6)
        tx.text(0.0, 1.0, "\n".join(C.wrap(p, 33) for p in body.split("\n")), ha="left",
                va="top", fontsize=house.FS_LABEL, color=house.INK_2, linespacing=1.2)
        for k, (stat, title) in enumerate(STATS):
            ax = fig.add_subplot(gs[r, k + 1])
            pts = cell["layers"][layer][stat]
            groups = {name: [(p, v) for p, v in pts.items() if v["pair_set"] == name]
                      for name in ("OO", "MO_diff", "MM", "UNTRAINED")}
            trained = [v for n in ("OO", "MO_diff", "MM") for _, v in groups[n]]
            lo_hi = [x for v in trained for x in (v["point"], v.get("q_lo"), v.get("q_hi"))
                     if x is not None]
            sm = summ.get(layer, {}).get(stat, {})
            if sm.get("band"):
                lo_hi += list(sm["band"])
            xlo, xhi = min(lo_hi), max(lo_hi)
            pad = 0.12 * (xhi - xlo or 0.01)
            untr = [v["point"] for _, v in groups["UNTRAINED"]]
            if untr and min(untr) >= xlo - 3 * (xhi - xlo) and max(untr) <= xhi + 3 * (xhi - xlo):
                xlo, xhi = min(xlo, min(untr)), max(xhi, max(untr))
                untr_in_view = True
            else:
                untr_in_view = False
            xlo, xhi = xlo - pad, xhi + pad
            if sm.get("band"):
                ax.axvspan(*sm["band"], color=C.ORD, alpha=0.14, lw=0)
            if untr_in_view and sm.get("untrained_band"):
                ax.axvspan(*sm["untrained_band"], color=C.UNTR, alpha=0.14, lw=0)
            for name, y in ROWS:
                if name == "mean":
                    q = sm.get("mo_diff_mean_q")
                    if q and None not in q:
                        ax.plot(q, [y, y], color=C.MOD, lw=5, solid_capstyle="butt")
                    continue
                items = groups[name]
                col = {"OO": C.ORD, "MO_diff": C.MOD, "MM": C.MOD, "UNTRAINED": C.UNTR}[name]
                face = "white" if name == "MM" else col
                offs = np.linspace(-0.28, 0.28, len(items)) if len(items) > 1 else [0.0]
                for (pname, v), dy in zip(items, offs):
                    entries += 1
                    nonfinite += int(v.get("nonfinite_draws") or 0)
                    if name == "UNTRAINED" and not untr_in_view:
                        continue
                    if v.get("q_lo") is not None and v.get("q_hi") is not None:
                        ax.plot([v["q_lo"], v["q_hi"]], [y + dy, y + dy], color=col, lw=1.4)
                    ax.plot(v["point"], y + dy, "o", ms=5.5, mfc=face, mec=col, mew=1.4)
            if untr and not untr_in_view:
                side_left = max(untr) < xlo
                ax.text(0.01 if side_left else 0.99, 0.05,
                        ("← " if side_left else "") + f"untrained {min(untr):.2f}–{max(untr):.2f}"
                        + ("" if side_left else " →"),
                        transform=ax.transAxes, ha="left" if side_left else "right", va="bottom",
                        fontsize=house.FS_LABEL, color=house.INK_2)
            ax.set_xlim(xlo, xhi)
            ax.set_ylim(-0.6, 4.6)
            ax.set_yticks([])
            ax.grid(axis="x", color=house.TICK_LINE, lw=0.9)
            ax.grid(axis="y", visible=False)
            if C.allowed(doc) and layer in a1:
                word = C.verdict(doc, a1[layer][stat]["word"], test)
            else:
                word = doc["verdict_statement"]
            ax.set_title((title + "\n" if r == 0 else "") + C.wrap(word, 46),
                         fontsize=house.FS_LABEL, color=house.INK, loc="left", pad=6)
            if r == len(layers) - 1:
                ax.set_xlabel("held-out R², smaller of the two directions" if stat == "predictivity"
                              else "linear CKA (1 = same geometry)", fontsize=house.FS_LABEL)
    # legend: one proxy per row of every panel, top to bottom
    lax = C.blank(fig.add_axes([0.35, 0.045, 0.64, 0.03]))
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    hs = [Patch(color=C.ORD, alpha=0.3, label="ordinary–ordinary band [L, U]"),
          Line2D([], [], marker="o", ls="", color=C.ORD, label="ordinary–ordinary pair"),
          Line2D([], [], marker="o", ls="", color=C.MOD, label="modulated–ordinary, different seeds"),
          Line2D([], [], color=C.MOD, lw=5, label="mean of those (bootstrap 5–95 %)"),
          Line2D([], [], marker="o", ls="", mfc="white", mec=C.MOD, label="modulated–modulated pair"),
          Line2D([], [], marker="o", ls="", color=C.UNTR, label="untrained–untrained pair")]
    lax.legend(handles=hs, loc="center", ncol=3, frameon=False, fontsize=house.FS_LABEL)
    C.footer(fig, doc, test, y=0.035, width=135,
             extra=((f"Interim marks: {C.rel(a.interim)}, {C.status_text(inter)}, rules "
                     f"{inter['decision_rules']['sha256'][:12]}. ") if inter else "") +"Rows in every panel, top to bottom: ordinary–ordinary; modulated–ordinary "
                   "(different seeds); their mean; modulated–modulated; untrained. Each panel has "
                   "its own horizontal range: compare positions within a panel, not across panels.")
    # the footer sits in the left third; make room for it below the legend
    fig.subplots_adjust(bottom=0.16)

    # ---- data statement --------------------------------------------------------------------
    g5 = doc.get("gate_G5") or {}
    rules = C.rules_at(doc["decision_rules"]["sha256"])
    g6 = C.param(rules, "gates.G6.test_fold_groups_min")
    ds = doc["data_statement"]
    fits = ds.get("ridge", {})
    boot = ds.get("bootstrap", {})
    rows = [
        dict(what="probe rows (sampled steps)", used=cell["rows_used"], total=cell["rows_available"],
             note="the same sampled rows of the same stored episodes are fed to every agent"),
        dict(what="held-out episode groups, smallest split repeat", used=min(cell["test_groups_per_repeat"]),
             total=cell["groups"], note=f"one group = one episode_seed (every store's copy of that reset); "
                                        f"gate G6 needs at least {g6} held out"),
    ]
    if g5:
        ent = sum(len(v) for v in g5.get("entered", {}).values())
        rows.append(dict(what="training runs entered after gate G5", used=ent,
                         total=len(g5.get("per_run", {})),
                         note="a run that fails stage-1 competence is dropped before any pair is formed"))
    for name, what in (("OO", "ordinary–ordinary pairs"), ("MO_diff", "modulated–ordinary pairs, different seeds"),
                       ("MM", "modulated–modulated pairs"), ("UNTRAINED", "untrained–untrained pairs")):
        n = len(sets.get(name, []))
        rows.append(dict(what=what, used=n, total=n, note="every pair the rules form is drawn"))
    ms = sets.get("MO_same", [])
    rows.append(dict(what="modulated–ordinary pairs, same seed", used=0, total=len(ms),
                     note="not drawn here: the same-seed comparison is Figure an03"))
    ref = cell.get("refused_layers") or {}
    rows.append(dict(what="verdict layers", used=len(layers), total=len(layers) + len(ref),
                     note="a layer is refused when its probe has too few rows per column"))
    rows.append(dict(what="drawn statistics with a non-finite bootstrap draw", used=nonfinite, total=entries,
                     note="count of non-finite draws summed over drawn pair entries; a non-finite draw "
                          "leaves that interval undrawn"))
    if fits:
        rows.append(dict(what="ridge fits at the edge of the penalty grid", used=int(fits.get("fits_at_grid_edge", 0)),
                         total=int(fits.get("fits", 0)), note="flagged by the driver; listed in the output"))
    if boot:
        rows.append(dict(what="bootstrap draws per interval", used=int(boot.get("cka_draws", 0)),
                         total=int(boot.get("cka_draws", 0)),
                         note=f"CKA; predictivity pools {boot.get('pooled_predictivity_draws')} over the "
                              f"split repeats; resampling unit: {boot.get('unit', '')}"))
    if inter:
        rows.append(dict(what="interim layer verdicts shown beside the evidence ones", used=len(ia1),
                         total=len(layers), note=f"from {C.rel(a.interim)} (rules "
                         f"{inter['decision_rules']['sha256'][:12]}); words only, no interim numbers drawn"))
    C.write_data(STEM, out, doc, a.source, test, rows)
    C.finish(fig, STEM, out)


if __name__ == "__main__":
    main()
