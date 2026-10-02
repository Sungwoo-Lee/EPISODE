"""FIGURE an06 - pilot controls: do the tools work? (tool validation - shared seed 42 - not evidence)

WHAT IS PLOTTED. A table, drawn as an image: every control the pilot ran on the level-05 w0000 pair
(one ordinary and one modulated agent, both seed 42), its value for each agent, the bound it is
held to and where that bound is registered. The controls test the tools, not the agents: that a
stored episode replays exactly through its own agent, that the rows the analysis reads are aligned to
the steps they claim, that the layer capture reconstructs the network's own outputs, that a readout
can recover a quantity the agent observes directly and cannot recover shuffled targets, and that an
agent compared with itself scores exactly 1. No number here is evidence about the agents; the
rules forbid any verdict word for the pilot.

WHAT IT READS. The pilot output folder (default results/analysis/algorithmic_null/
algorithmic_null_pilot/): `manifest.json` (bounds as the drivers read them), `acts_*.json` (per-agent
replay, alignment and reconstruction controls), `decoding.json` (gate G4 controls) and
`similarity.json` (same-agent similarity). Gate G4's two bounds are read from the rules file at the
outputs' own sha. Nothing is recomputed.

    python scripts/analysis/studies/modulator_clues/an06_pilot_controls.py [--source <folder>/manifest.json] [--out ...]
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt                                            # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

STEM = "an06_pilot_controls"
DEFAULT = os.path.join(C.RESULTS, "algorithmic_null_pilot", "manifest.json")
BANNER = "tool validation — shared seed 42 — not evidence"


def fmt(v):
    if isinstance(v, bool):
        return "yes" if v else "no"
    if v == 0:
        return "0"
    if abs(v) < 1e-3:
        return f"{v:.1e}"
    return f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) < 10 else f"{v:,.0f}"


def main():
    a = C.cli(__doc__, DEFAULT)
    folder = os.path.dirname(os.path.abspath(a.source))
    man = C.load(a.source)
    sim = C.load(os.path.join(folder, "similarity.json"))
    dec = C.load(os.path.join(folder, "decoding.json"))
    shas = {d["decision_rules"]["sha256"] for d in (man, sim, dec)}
    if len(shas) != 1:
        raise SystemExit(f"{STEM}: the pilot outputs carry different rules shas {sorted(shas)}")
    if man["evidence_status"] != "pilot" or C.allowed(man):
        raise SystemExit(f"{STEM}: draws pilot outputs only (verdict words not allowed); got "
                         f"{man['evidence_status']!r}")
    doc = dict(man, driver="run_activations")
    test = C.is_test_input(a.source, man)
    out = C.check_out(a.out, test)
    rules = C.rules_at(man["decision_rules"]["sha256"])
    g4_min = C.param(rules, "gates.G4.input_satiation_r2_min")
    g4_max = C.param(rules, "gates.G4.shuffled_r2_max")
    G, T = man["gates_read"], man["tool_checks"]
    acts = {}
    for f in sorted(glob.glob(os.path.join(folder, "acts_*.json"))):
        j = json.load(open(f))
        if j["kind"] == "trained":
            acts[j["run_label"]] = j
    labels = sorted(acts, key=lambda s: (not s.startswith("ordinary"), s))
    if len(labels) != 2:
        raise SystemExit(f"{STEM}: expected the pilot pair, found {labels}")

    def per(fn):
        return [fn(acts[l]) for l in labels]

    g4 = dec["cell"]["g4_controls"]
    selfsim = sim["cells"][0]["self_similarity"]
    rows = [
        ("Self-replay: action agreement on the agent's own store", "gate G1",
         f"≥ {fmt(G['G1']['action_agreement_min'])}",
         per(lambda j: j["gate_G1_self_agreement"]["agreement"])),
        ("Aligned rows: logits' action = next stored action", "gate G3",
         f"≥ {fmt(G['G3']['alignment_agreement_min'])}",
         per(lambda j: j["alignment_controls"]["step_discontinuous_all"]["agreement"])),
        ("  same, action-change rows only", "gate G3",
         f"≥ {fmt(G['G3']['alignment_agreement_min'])}",
         per(lambda j: j["alignment_controls"]["step_discontinuous_change_rows"]["agreement"])),
        ("Shifted by one row (must NOT agree)", "gate G3",
         f"< {fmt(G['G3']['shift_control_agreement_max'])}",
         per(lambda j: j["alignment_controls"]["shift_by_one_all_rows_with_t_ge_1"])),
        ("  same, action-change rows only", "tool check",
         f"< {fmt(T['shift_change_rows_max'])}",
         per(lambda j: j["alignment_controls"]["shift_by_one_change_rows"])),
        ("Layer capture rebuilds the outputs: max rel. deviation", "gate G2",
         f"≤ {fmt(G['G2'])}",
         per(lambda j: max(j["chain_assertions"]["max_rel_deviation"].values()))),
        ("Sampled rows = full replay: max rel. deviation", "tool check",
         f"≤ {fmt(T['buffer_index_rel_tol'])}",
         per(lambda j: max(j["sampled_vs_full_capture"]["max_per_row_rel_deviation"].values()))),
        ("  same, rows planted one step off (must fail)", "tool check",
         f"> {fmt(T['buffer_index_rel_tol'])}",
         per(lambda j: min(j["sampled_vs_full_capture"]
                           ["planted_one_step_slot_shift_max_per_row_rel_deviation"].values()))),
        ("Same agent vs itself: |similarity − 1|, worst layer", "tool check",
         f"≤ {fmt(T['self_similarity_atol'])}",
         [max(selfsim[layer][l] for layer in selfsim) for l in labels]),
        ("Hunger read from the raw input (probe-wide)", "gate G4",
         f"≥ {fmt(g4_min)}", [g4["input_satiation_r2"]] * 2),
        ("Shuffled targets, worst quantity (probe-wide)", "gate G4",
         f"≤ {fmt(g4_max)}", [max(g4["shuffled_r2"].values())] * 2),
    ]

    house.apply()
    n = len(rows)
    fig = plt.figure(figsize=(10.4, 0.42 * n + 3.3))
    ax = C.blank(fig.add_axes([0.0, 0.3, 1.0, 0.6]))
    cols = (0.005, 0.50, 0.63, 0.76, 0.88)
    head = ("control", "registered in", "bound", "ordinary", "modulated")
    ax.set_title(BANNER.upper(), fontsize=house.FS_TITLE, color=house.INK, loc="left", pad=10)
    for x, h in zip(cols, head):
        ax.text(x, 1.0, h, ha="left", va="top", fontsize=house.FS_LABEL, color=house.INK_2,
                fontweight="semibold")
    step = 0.93 / n
    for i, (name, where, bound, vals) in enumerate(rows):
        y = 0.93 - i * step
        ax.axhline(y + 0.01, color=house.TICK_LINE, lw=0.8)
        for x, s in zip(cols, (name, where, bound, fmt(vals[0]), fmt(vals[1]))):
            ax.text(x, y - 0.005, s, ha="left", va="top", fontsize=house.FS_LABEL, color=house.INK)
    C.footer(fig, doc, test, y=0.27, width=150,
             extra=f"Agents: {labels[0]} and {labels[1]} (level-05 world w0000). Probe-wide rows are "
                   f"one number for the probe, repeated in both columns.")

    cnt = man["probes"][next(iter(man["probes"]))]["counts"]
    drows = [dict(what="stored episodes in the probe", used=cnt["episodes"], total=cnt["episodes"],
                  note="5,000 from block 0 of each agent's store"),
             dict(what="probe rows kept for the analyses", used=cnt["rows_kept"],
                  total=cnt["decision_rows_total"], note=f"{cnt['rows_per_episode']} sampled rows per episode; "
                                                          f"every step is still replayed"),
             dict(what="decision rows in the self-replay check, first agent",
                  used=acts[labels[0]]["gate_G1_self_agreement"]["rows"],
                  total=acts[labels[0]]["gate_G1_self_agreement"]["rows"],
                  note="every decision row of that agent's own store"),
             dict(what="decision rows in the self-replay check, second agent",
                  used=acts[labels[1]]["gate_G1_self_agreement"]["rows"],
                  total=acts[labels[1]]["gate_G1_self_agreement"]["rows"],
                  note="every decision row of that agent's own store"),
             dict(what="episodes checked by the capture-reconstruction test, first agent",
                  used=len(acts[labels[0]]["chain_assertions"]["episodes"]), total=cnt["episodes"],
                  note="a fixed subset, all steps of each"),
             dict(what="rows checked sampled-vs-full, first agent",
                  used=acts[labels[0]]["sampled_vs_full_capture"]["rows_checked"], total=cnt["rows_kept"],
                  note="a fixed subset of the kept rows"),
             dict(what="controls drawn", used=n, total=n, note="every control in the pilot outputs "
                                                                "except the untrained network's")]
    C.write_data(STEM, out, doc, a.source, test, drows)
    C.finish(fig, STEM, out)


if __name__ == "__main__":
    main()
