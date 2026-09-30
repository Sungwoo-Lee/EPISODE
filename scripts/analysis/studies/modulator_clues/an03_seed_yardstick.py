"""FIGURE an03 - A3 seed yardstick: same seed versus different seeds, and whether survival differs.

WHAT IS PLOTTED. Left, one panel per verdict layer: the registered primary statistic (mutual linear
predictivity) for four sets of agent pairs, top to bottom - ordinary vs ordinary at different seeds
(the yardstick, band [L, U] shaded), modulated vs ordinary at DIFFERENT seeds, modulated vs ordinary
at the SAME seed (the two share their starting weights), modulated vs modulated. The panel title is
the evaluator's A3 pattern for that layer, verbatim, and whether the same-seed excess E holds.
Right, survival - the other half of the pattern: top, each run's stage survival (mean survival steps
over the stage's last episodes, from the training log) against the episode step cap; bottom, the
modulated-minus-ordinary difference with two error bars, +-multiplier x the raw standard error and
+-multiplier x the floored standard error the rules actually use.

WHY THE CEILING IS ON THE FIGURE. Most probe episodes reach the step cap, so "same survival" is
measured near a ceiling; and the difference is beyond the raw standard error but inside the floored
one. Both facts are drawn and stated (plan-reviewer, analysis-verdict gate, 2026-09-30).

WHAT IT READS. `similarity.json` from `run_similarity` (A3 inputs, survival and evaluation), its
probe record `probes/probe_<id>.json` (truncated-episode count), and the run's own saved config
(the step cap). Nothing is recomputed.

    python scripts/analysis/studies/modulator_clues/an03_seed_yardstick.py [--source ...] [--out ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json                                                                # noqa: E402
import numpy as np                                                         # noqa: E402
import matplotlib.pyplot as plt                                            # noqa: E402
import yaml                                                                # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

STEM = "an03_seed_yardstick"
DEFAULT = os.path.join(C.RESULTS, "algorithmic_null_mayrep", "similarity.json")
SETS = (("OO", 3.0, C.ORD, C.ORD), ("MO_diff", 2.0, C.MOD, C.MOD),
        ("MO_same", 1.0, house.INK, house.INK), ("MM", 0.0, C.MOD, "white"))


def step_cap(probe: dict) -> int:
    caps = set()
    for m in probe["store_meta"]:
        cfg = yaml.safe_load(open(os.path.join(m["run_path"], "models", "config.yaml")))
        env = cfg.get("environment") or {}
        if "max_steps" not in env:
            raise SystemExit(f"{m['run_path']}: saved config has no environment.max_steps")
        caps.add(int(env["max_steps"]))
    if len(caps) != 1:
        raise SystemExit(f"the probe's runs disagree on the step cap: {sorted(caps)}")
    return caps.pop()


def main():
    a = C.cli(__doc__, DEFAULT)
    doc = C.load(a.source)
    test = C.is_test_input(a.source, doc)
    out = C.check_out(a.out, test)
    cell = [c for c in doc["cells"] if c.get("primary")][0]
    if not cell["pair_sets"].get("MO_same") or not cell["pair_sets"].get("OO"):
        raise SystemExit(f"{STEM}: needs same-seed and ordinary-ordinary pairs (a yardstick manifest)")
    probe_path = os.path.join(os.path.dirname(os.path.abspath(a.source)), "probes",
                              f"probe_{cell['probe']}.json")
    probe = json.load(open(probe_path))
    cnt = probe["counts"]
    cap = step_cap(probe)
    rules = C.rules_at(doc["decision_rules"]["sha256"])
    mult = C.param(rules, "common.survival.se_multiplier")
    ev = doc.get("evaluation") or {}
    a3 = ev.get("A3") or {}
    summ = ev.get("summaries") or {}
    surv = doc.get("survival") or {}
    per_run = doc.get("survival_per_run") or {}
    layers = list(cell["layers"])

    house.apply()
    fig = plt.figure(figsize=(11.0, 2.05 * len(layers) + 2.4))
    gs = fig.add_gridspec(len(layers), 2, width_ratios=[1.55, 1.0], wspace=0.32, hspace=0.9,
                          left=0.03, right=0.99, top=0.93, bottom=0.25)
    for r, layer in enumerate(layers):
        ax = fig.add_subplot(gs[r, 0])
        pts = cell["layers"][layer]["predictivity"]
        band = summ.get(layer, {}).get("predictivity", {}).get("band")
        if band:
            ax.axvspan(*band, color=C.ORD, alpha=0.14, lw=0)
        for name, y, col, face in SETS:
            items = [v for v in pts.values() if v["pair_set"] == name]
            offs = np.linspace(-0.25, 0.25, len(items)) if len(items) > 1 else [0.0]
            for v, dy in zip(items, offs):
                if v.get("q_lo") is not None and v.get("q_hi") is not None:
                    ax.plot([v["q_lo"], v["q_hi"]], [y + dy] * 2, color=col, lw=1.4)
                ax.plot(v["point"], y + dy, "D" if name == "MO_same" else "o", ms=5.5, mfc=face,
                        mec=col, mew=1.4)
        ax.set_yticks([3, 2, 1, 0])
        ax.set_yticklabels(["ord–ord", "mod–ord, diff. seed", "mod–ord, same seed",
                            "mod–mod"], fontsize=house.FS_LABEL)
        ax.set_ylim(-0.6, 3.6)
        ax.grid(axis="x", color=house.TICK_LINE, lw=0.9)
        ax.grid(axis="y", visible=False)
        if C.allowed(doc) and layer in a3.get("layers", {}):
            L = a3["layers"][layer]
            w = C.verdict(doc, L["pattern"], test)
            e = "" if test else f"   (same-seed excess E {'holds' if L['E'] else 'does not hold'})"
            title = w + e
        else:
            title = doc["verdict_statement"]
        ax.set_title(f"{layer}: " + C.wrap(title, 70), fontsize=house.FS_LABEL, color=house.INK,
                     loc="left", pad=6)
        if r == len(layers) - 1:
            ax.set_xlabel("held-out R², smaller of the two directions", fontsize=house.FS_LABEL)

    # ---- survival --------------------------------------------------------------------------
    trunc = cnt["truncated_episodes"] / cnt["episodes"]
    top = fig.add_subplot(gs[: max(2, len(layers) // 2), 1])
    arms = {"ordinary": 0, "modulated": 1}
    seen = {"ordinary": 0, "modulated": 0}
    for k, v in per_run.items():
        x = arms[v["arm"]] + (seen[v["arm"]] - 1) * 0.12      # seeds side by side, in run order
        seen[v["arm"]] += 1
        top.plot(x, v["S_a3"], "o", ms=7, color=C.ORD if v["arm"] == "ordinary" else C.MOD)
    top.axhline(cap, color=house.INK, lw=1.2)
    top.text(0.5, cap, f"step cap {cap}", transform=top.get_yaxis_transform(), ha="center",
             va="bottom", fontsize=house.FS_LABEL, color=house.INK)
    vals = [v["S_a3"] for v in per_run.values()]
    top.set_ylim(min(vals) - 0.25 * (cap - min(vals)) - 2, cap + 0.25 * (cap - min(vals)) + 2)
    top.set_xlim(-0.6, 1.6)
    top.set_xticks([0, 1])
    top.set_xticklabels(["ordinary", "modulated"], fontsize=house.FS_LABEL)
    top.set_ylabel("stage survival (steps)", fontsize=house.FS_LABEL)
    top.set_title(C.wrap(f"{100 * trunc:.0f} % of the probe's episodes reach the step cap", 42),
                  fontsize=house.FS_LABEL, color=house.INK, loc="left", pad=6)
    bot = fig.add_subplot(gs[max(2, len(layers) // 2) + 1:, 1])
    if surv.get("available"):
        md, se_raw, se_used = surv["mean_diff"], surv["se_raw"], surv["se_used"]
        for y, se, col, lab in ((1.0, se_raw, house.INK_2, "raw SE"),
                                (0.0, se_used, house.INK, "floored SE (used)")):
            bot.plot([md - mult * se, md + mult * se], [y, y], color=col, lw=2.2)
            bot.plot(md, y, "o", color=col, ms=6)
        bot.axvline(0, color=house.RULE, lw=1.2)
        span = mult * max(se_used, se_raw) * 1.4 + abs(md)
        bot.set_xlim(-span, span)
        bot.set_yticks([1, 0])
        bot.set_yticklabels([f"±{mult:g}× raw SE", f"±{mult:g}× floored SE"],
                            fontsize=house.FS_LABEL)
        bot.set_ylim(-0.6, 1.6)
        bot.grid(axis="x", color=house.TICK_LINE, lw=0.9)
        bot.grid(axis="y", visible=False)
        bot.set_xlabel("modulated − ordinary survival (steps)", fontsize=house.FS_LABEL)
        bot.set_title(C.wrap(f"difference {md:+.2f} steps; raw SE {se_raw:.2f}, floored SE "
                             f"{se_used:.2f}", 42), fontsize=house.FS_LABEL, color=house.INK,
                      loc="left", pad=6)
    else:
        C.blank(bot)
        bot.text(0.5, 0.5, "survival not available", ha="center", va="center",
                 fontsize=house.FS_BODY, color=house.INK)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    hs = [Patch(color=C.ORD, alpha=0.3, label="ordinary–ordinary band [L, U]"),
          Line2D([], [], marker="o", ls="", color=C.ORD, label="ordinary–ordinary pair / ordinary run"),
          Line2D([], [], marker="o", ls="", color=C.MOD, label="modulated–ordinary, different seeds / modulated run"),
          Line2D([], [], marker="D", ls="", color=house.INK, label="modulated–ordinary, same seed"),
          Line2D([], [], marker="o", ls="", mfc="white", mec=C.MOD, label="modulated–modulated pair")]
    fig.legend(handles=hs, loc="lower center", bbox_to_anchor=(0.5, 0.13), ncol=2, frameon=False,
               fontsize=house.FS_LABEL)
    C.footer(fig, doc, test, y=0.115, width=150,
             extra="Left panels each have their own horizontal range: compare positions within a panel.")

    # ---- data statement --------------------------------------------------------------------
    sets = cell["pair_sets"]
    rows = [dict(what=f"{n} pairs", used=len(sets.get(n, [])), total=len(sets.get(n, [])),
                 note=w) for n, w in (("OO", "ordinary pairs at different seeds: the yardstick"),
                                      ("MO_diff", "modulated vs ordinary at different seeds"),
                                      ("MO_same", "modulated vs ordinary at the same seed (shared start)"),
                                      ("MM", "modulated pairs at different seeds"))]
    rows.append(dict(what="probe rows (sampled steps)", used=cell["rows_used"], total=cell["rows_available"],
                     note="the same rows for every agent"))
    rows.append(dict(what="probe episodes that reach the step cap", used=cnt["truncated_episodes"],
                     total=cnt["episodes"], note=f"step cap {cap}, read from the runs' saved configs; "
                                                 f"survival is compared near this ceiling"))
    rows.append(dict(what="runs with a stage survival value", used=len(per_run), total=len(per_run),
                     note="mean Episode/Steps over the stage's last window of the training log"))
    info = next(iter(per_run.values()))["S_a3_info"] if per_run else {}
    if info:
        rows.append(dict(what="training-log rows in the survival window, per run (first run)",
                         used=int(info["rows_used"]), total=int(info["rows"]),
                         note=f"window {int(info['window']):,} episodes, rows weighted by {info['weighting']}"))
    rows.append(dict(what="same-seed pairs with a verified shared start",
                     used=sum(bool(v["identical"]) for v in doc["shared_start"]["per_seed"].values()),
                     total=len(doc["shared_start"]["per_seed"]),
                     note="main-network weights bitwise identical at the same seed (Checkpoint 3.3)"))
    C.write_data(STEM, out, doc, a.source, test, rows)
    C.finish(fig, STEM, out)


if __name__ == "__main__":
    main()
