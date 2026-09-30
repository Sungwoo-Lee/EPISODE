"""FIGURE an02 - A2 decoding profiles: where in each agent can a linear readout find a quantity?

WHAT IS PLOTTED. One panel per headline quantity (hunger, true injury, distance to the nearest
predator, survival steps remaining). Horizontal: the layer read, from the raw network input to the
critic's hidden layer. Vertical: held-out R^2 of a ridge readout, the mean over the split repeats.
One thin line per trained agent (blue ordinary, orange modulated); each arm's seed-to-seed range is
shaded; the dashed line is the clock baseline (the best any readout of the time step alone can do),
the same for every agent. The panel title carries the evaluator's profile word, verbatim.

`steps_remaining` is drawn as BLOCKED, not as a number, whenever its held-out episode groups fall
below gate G6's minimum: then the rules decide nothing from it and the page must not show its R^2.

WHAT IT READS. `decoding.json` from `scripts/analysis/nmn/run_decoding.py` (default: the interim
May-replication output). Nothing is recomputed; the shaded ranges are the min and max of the
agents' own R^2 values as the driver wrote them.

    python scripts/analysis/studies/modulator_clues/an02_decoding_profiles.py [--source ...] [--out ...]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                                                         # noqa: E402
import matplotlib.pyplot as plt                                            # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

STEM = "an02_decoding_profiles"
DEFAULT = os.path.join(C.RESULTS, "algorithmic_null_mayrep", "decoding.json")
QUANT = (("satiation", "hunger (satiation)"), ("injury_level", "true injury level"),
         ("nearest_predator_manhattan", "distance to the nearest predator"),
         ("steps_remaining", "survival steps remaining (death-ended episodes)"))


def main():
    a = C.cli(__doc__, DEFAULT)
    doc = C.load(a.source)
    test = C.is_test_input(a.source, doc)
    out = C.check_out(a.out, test)
    cell = doc["cell"]
    rules = C.rules_at(doc["decision_rules"]["sha256"])
    g6 = int(C.param(rules, "gates.G6.test_fold_groups_min"))
    ev = ((doc.get("evaluation") or {}).get("A2") or {}).get("quantities") or {}
    agents = {k: v for k, v in cell["agents"].items() if not v.get("untrained")}
    # the pool each held-out split drew from: every episode group, or for the steps_remaining
    # headline only groups with a death-ended episode (probe record, written by probe_set)
    probe = json.load(open(os.path.join(os.path.dirname(os.path.abspath(a.source)), "probes",
                                        f"probe_{cell['probe']}.json")))
    cnt = probe["counts"]
    pools = {"*": (int(cnt["distinct_episode_seed_groups"]), "all episode groups in the probe"),
             "steps_remaining": (int(cnt["groups_with_a_death_ended_episode"]),
                                 "episode groups with a death-ended episode")}
    untrained = [k for k, v in cell["agents"].items() if v.get("untrained")]

    house.apply()
    fig, axs = plt.subplots(2, 2, figsize=(10.4, 9.6))
    fig.subplots_adjust(left=0.07, right=0.99, top=0.9, bottom=0.27, hspace=0.75, wspace=0.18)
    rows, blocked = [], []
    layers = None
    for ax, (q, qname) in zip(axs.ravel(), QUANT):
        Q = cell["quantities"][q]
        first = next(iter(agents))
        lay = list(Q["agents"][first])
        layers = layers or lay
        xs = np.arange(len(lay) + 1)
        labels = ["input"] + lay
        min_groups = min(Q["held_out_groups_per_repeat"])
        is_blocked = min_groups < g6
        word = None
        if C.allowed(doc) and q in ev:
            word = C.verdict(doc, ev[q]["profile"], test)
            if ev[q].get("note") and not test:
                word += f" — {ev[q]['note']}"
                if ev[q].get("different_layers"):
                    word += ": " + ", ".join(ev[q]["different_layers"])
        ax.set_title(qname + "\n" + C.wrap(word or doc["verdict_statement"], 60),
                     fontsize=house.FS_LABEL, color=house.INK, loc="left", pad=6)
        if is_blocked:
            blocked.append(q)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_facecolor(house.BG_SOFT)
            ax.text(0.5, 0.5, C.wrap(f"BLOCKED by gate G6: {min_groups} held-out episode groups in the "
                                     f"smallest split repeat, the rules need at least {g6}. No R² is "
                                     f"shown, because the rules decide nothing from it.", 44),
                    ha="center", va="center", fontsize=house.FS_BODY, color=house.INK)
        else:
            for arm, col in (("ordinary", C.ORD), ("modulated", C.MOD)):
                names = [k for k, v in agents.items() if v["arm"] == arm]
                ys = np.array([[Q["agents"][k][l]["r2"] for l in lay] for k in names])
                if len(names) > 1:
                    ax.fill_between(xs[1:], ys.min(0), ys.max(0), color=col, alpha=0.18, lw=0)
                for y in ys:
                    ax.plot(xs[1:], y, color=col, lw=1.3, marker="o", ms=4)
            ax.plot(0, Q["reference"]["raw_input"]["r2"], "D", color=house.INK, ms=6)
            ax.axhline(Q["clock_r2"], color=house.INK_2, lw=1.3, ls=(0, (4, 3)))
            ax.set_xticks(xs)
            ax.set_xticklabels(labels, fontsize=house.FS_LABEL, rotation=30, ha="right")
            ax.set_ylabel("held-out R²", fontsize=house.FS_LABEL)
        rows.append(dict(what=f"{q}: probe rows used", used=Q["rows_used"], total=Q["rows_available"],
                         note=doc["data_statement"]["rows_per_quantity"][q]["reason"]))
        pool = pools.get(q, pools["*"])
        rows.append(dict(what=f"{q}: held-out episode groups, smallest split repeat", used=min_groups,
                         total=pool[0], note=(f"of {pool[1]}; gate G6 requires at least {g6} held out: "
                                              + ("BLOCKED, drawn as blocked, no R\u00b2" if is_blocked
                                                 else "met"))))
        drop = sum(Q.get("rows_dropped_no_clock_per_repeat", []))
        rows.append(dict(what=f"{q}: held-out rows without a clock value, summed over repeats", used=drop,
                         total=Q["rows_used"], note="dropped from the layer score and the clock score alike"))
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    hs = [Line2D([], [], color=C.ORD, marker="o", ms=4, label="ordinary agent (one line per seed)"),
          Patch(color=C.ORD, alpha=0.3, label="ordinary seed range"),
          Line2D([], [], color=C.MOD, marker="o", ms=4, label="modulated agent (one line per seed)"),
          Patch(color=C.MOD, alpha=0.3, label="modulated seed range"),
          Line2D([], [], color=house.INK_2, ls=(0, (4, 3)), label="clock baseline (time step alone)"),
          Line2D([], [], color=house.INK, marker="D", ls="", label="raw network input")]
    fig.legend(handles=hs, loc="lower center", bbox_to_anchor=(0.5, 0.155), ncol=3, frameon=False,
               fontsize=house.FS_LABEL)
    C.footer(fig, doc, test, y=0.125, width=150,
             extra="Each panel has its own vertical range. Held-out = scored on episodes the readout "
                   "never saw (grouped by episode_seed).")
    rows.append(dict(what="trained agents drawn", used=len(agents), total=len(agents),
                     note="every trained agent of the output"))
    rows.append(dict(what="untrained reference networks drawn", used=0, total=len(untrained),
                     note="in the output, not drawn here: A2 compares the trained agents"))
    rows.append(dict(what="quantities drawn as blocked by gate G6", used=len(blocked), total=len(QUANT),
                     note=", ".join(blocked) or "none"))
    rows.append(dict(what="all-episode steps_remaining (sensitivity row)", used=0, total=1,
                     note="not drawn: it decides nothing and truncated episodes make it a clock"))
    C.write_data(STEM, out, doc, a.source, test, rows)
    C.finish(fig, STEM, out)


if __name__ == "__main__":
    main()
