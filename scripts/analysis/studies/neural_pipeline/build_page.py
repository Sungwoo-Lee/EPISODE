#!/usr/bin/env python3
"""build_page.py - assemble the 'Neural Recording Pipeline' plan page.

Fills docs/experiments/active/neural_analysis/page_template.html with the house style, the unit inventory measured
from trained models (unit_inventory.json, written by unit_inventory.py), the planned recording sizes computed from
it, and the simulated-number figures of mockups.py (each with the data statement the script emitted). Reuses the
half-factorial page's builder helpers (figure, table, house style) by path.

    $P scripts/analysis/studies/neural_pipeline/unit_inventory.py --out docs/experiments/active/neural_analysis/unit_inventory.json
    $P scripts/analysis/studies/neural_pipeline/mockups.py
    $P scripts/analysis/studies/neural_pipeline/build_page.py
"""
import base64
import datetime
import importlib.util
import json
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
_spec = importlib.util.spec_from_file_location(
    "f7b_build_page", os.path.join(ROOT, "scripts", "analysis", "studies", "f7b_across_runs", "build_page.py"))
FB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FB)
BB = FB.BB

PAGE_DIR = os.path.join(ROOT, "docs/experiments/active/neural_analysis")
FB.FIG_DIR = os.path.join(PAGE_DIR, "figures")
FIG = "scripts/analysis/studies/neural_pipeline/mockups.py"

# what each captured key is (model capture names -> plain description); a key missing here fails the build
LAYER = {
    "enc.uni.raw": ("encoder stage 1", "pre-activation"),
    "enc.uni.mod": ("encoder stage 1", "after FiLM"),
    "enc.uni.out": ("encoder stage 1", "post-activation"),
    "enc.raw": ("encoder hub", "pre-activation"),
    "enc.mod": ("encoder hub", "after FiLM"),
    "enc.out": ("encoder hub", "post-activation"),
    "rnn.raw": ("recurrent (GRU)", "output before FiLM"),
    "rnn.mod": ("recurrent (GRU)", "output after FiLM"),
    "rnn.state": ("recurrent (GRU)", "hidden state"),
    "rnn.out": ("recurrent (GRU)", "output to the heads"),
    "actor.raw": ("actor hidden layer", "pre-activation"),
    "actor.mod": ("actor hidden layer", "after FiLM"),
    "actor.out": ("actor hidden layer", "post-activation"),
    "critic.raw": ("critic hidden layer", "pre-activation"),
    "critic.mod": ("critic hidden layer", "after FiLM"),
    "critic.out": ("critic hidden layer", "post-activation"),
    "logits": ("actor output", "action logits"),
    "value": ("critic output", "state value"),
}
SITE = {"unimodal": "encoder stage 1", "multimodal": "encoder hub", "rnn": "recurrent (GRU)",
        "actor": "actor hidden layer", "critic": "critic hidden layer"}

# planned recording sets (section 02): (name, starting injuries, animal conditions, healing conditions, checkpoints)
EPISODES, STEPS = 30, 100
N_RUNS = {"ordinary": 53, "modulated": 53}   # 16 worlds x 3 seeds + world-8 seeds 45/46 + level-05 reference 42-44
SETS = [("Experiment condition, core, final checkpoint", 3, 3, 1, 1, "injury 0 / 20 / 70; no animal, wandering rabbit, predator; healing off"),
        ("Experiment condition, pilot, across training", 3, 3, 1, 10, "as core, 4 runs (2 worlds x 2 agents) x 10 checkpoints"),
        ("Experiment condition, every scene, final checkpoint", 10, 4, 2, 1, "injury 0-90; all four animal settings; healing off and on")]


def inventory():
    return json.load(open(os.path.join(PAGE_DIR, "unit_inventory.json")))


def per_step(inv, agent):
    d = inv[agent]
    return sum(r["n"] for r in d["acts"]) + sum(r["n"] for r in d["film"]) + sum(d["carry_sizes"][1:])


def units_table(inv):
    rows, seen = [], {}
    for agent in ("ordinary", "modulated"):
        for r in inv[agent]["acts"]:
            if r["key"] not in LAYER:
                raise SystemExit(f"unit_inventory: no description for captured key {r['key']!r}")
            seen.setdefault(r["key"], {})[agent] = r
    order = list(LAYER)
    for k in order:
        if k not in seen:
            continue
        lay, what = LAYER[k]
        shape = next(iter(seen[k].values()))["shape"]
        n = lambda a: f'{seen[k][a]["n"]:,}' if a in seen[k] else "&mdash;"
        rows.append({"layer": lay, "what": what, "key": f"<code>{k}</code>",
                     "shape": " &times; ".join(map(str, shape)), "ord": n("ordinary"), "mod": n("modulated")})
    film = inv["modulated"]["film"]
    for side, lab in (("", "FiLM gain &gamma;"), ("_add", "FiLM bias &beta;")):
        fs = [f for f in film if f["key"].endswith(side) and (side or not f["key"].endswith("_add"))]
        sites = ", ".join(SITE.get(f["key"].replace("film.z_", "").replace("_add", ""), f["key"]) for f in fs)
        rows.append({"layer": "modulator output", "what": f"{lab} ({sites})", "key": "<code>film.z_*</code>",
                     "shape": f'{len(fs)} sites &times; {fs[0]["shape"][0]}', "ord": "&mdash;",
                     "mod": f'{sum(f["n"] for f in fs):,}'})
    mh = inv["modulated"]["carry_sizes"][1]
    rows.append({"layer": "modulator", "what": "recurrent hidden state", "key": "<code>mod_h</code>",
                 "shape": str(mh), "ord": "&mdash;", "mod": f"{mh:,}"})
    rows.append({"layer": "<strong>total per step</strong>", "what": "", "key": "", "shape": "",
                 "ord": f'<strong>{per_step(inv, "ordinary"):,}</strong>',
                 "mod": f'<strong>{per_step(inv, "modulated"):,}</strong>'})
    cols = ["layer", "what", "key", "shape", "ord", "mod"]
    return FB.table(pd.DataFrame(rows), cols, ["layer", "quantity", "capture key", "shape", "ordinary",
                                               "modulated"], num=("ord", "mod"), raw=tuple(cols), min_width=760)


def sizes_table(inv):
    bpv = 2   # float16
    rows = []
    for name, ni, na, nh, nck, desc in SETS:
        steps = ni * na * nh * EPISODES * STEPS
        if "pilot" in name:
            byts = 2 * nck * steps * bpv * (per_step(inv, "ordinary") + per_step(inv, "modulated"))
            nfiles = 4 * nck * ni
        else:
            byts = sum(N_RUNS[a] * nck * steps * bpv * per_step(inv, a) for a in N_RUNS)
            nfiles = sum(N_RUNS.values()) * nck * ni
        rows.append({"set": f"<strong>{name}</strong><br><span style=\"color:var(--ink-3);font-size:0.88em\">{desc}</span>",
                     "steps": f"{steps:,}", "files": f"{nfiles:,}", "per": f"{byts / nfiles / 1e6:,.0f} MB",
                     "tot": f"{byts / 1e9:,.1f} GB"})
    rows.insert(0, {"set": "<strong>Training condition, final checkpoint</strong><br><span style=\"color:var(--ink-3);"
                           "font-size:0.88em\">500 episodes per run in its own world; lengths vary, so sizes are "
                           "measured on the pilot; a few files per run</span>",
                    "steps": "&mdash;", "files": "&mdash;", "per": "&mdash;", "tot": "&mdash;"})
    cols = ["set", "steps", "files", "per", "tot"]
    return FB.table(pd.DataFrame(rows), cols, ["recording set", "steps per run and checkpoint", "files",
                                               "per file (mean)", "total"],
                    num=("steps", "files", "per", "tot"), raw=tuple(cols), min_width=700)


AX = {
    "np_design_matrix": "Horizontal: time in the episode, in steps (0&ndash;99), shared by the event strip at the top and "
                        "the matrix below. Vertical: regressors, grouped (continuous, state boxcars, interaction, events); "
                        "each event block has one row per lag, labelled with its lag range, and the lag-0 row is marked on "
                        "the right. Colour: the regressor's palette colour, light for low values and dark for high; grey "
                        "is zero.",
    "np_unitmap": "No axes in the usual sense: each dot is one unit, columns are layers (labelled below), and a "
                  "dot's position is fixed. Colour: the regressor with the largest unique explained variance "
                  "(&Delta;R&sup2;, legend below); dot area: that &Delta;R&sup2;; hollow dot: &Delta;R&sup2; below "
                  "0.03 for every regressor.",
    "np_tuned_share": "Horizontal: network layer. Vertical: units significantly tuned to the regressor, in percent of "
                      "the layer's units (0&ndash;100). One bar per regressor, colours in the legend.",
    "np_kernels": "Horizontal: time from the rabbit entering the field of view, in steps (&minus;5 to +20). Vertical, "
                  "top: mean absolute kernel coefficient over units (arbitrary units); bottom: recurrent units, sorted "
                  "by peak latency. Colour: kernel coefficient (blue negative, orange positive, arbitrary units).",
    "np_tuning": "Horizontal: starting injury level, 0&ndash;90. Vertical: unit activity, arbitrary units, each panel "
                 "its own range. Hollow circles: no animal; green squares: rabbit present; shading: 95&nbsp;% interval.",
    "np_models": "Horizontal: the nested models, each adding one regressor group to the one on its left. Vertical: "
                 "cross-validated R&sup2;, mean over the layer's units (0&ndash;1). One line per layer.",
    "np_interaction_map": "No axes in the usual sense: the unit layout of Figure 2. Colour: z-scored coefficient of the "
                          "injury &times; rabbit term, blue negative to orange positive (&minus;1 to +1).",
    "np_worlds": "Horizontal: training world, 1&ndash;16. Vertical: recurrent units tuned to injury &times; rabbit, in "
                 "percent of the layer's units. Black circles: ordinary agent; grey squares: modulated agent; small "
                 "marks: single seeds; large marks: mean of three seeds.",
    "np_unitmap_per_regressor": "No axes in the usual sense: one panel per regressor, each in the unit layout of "
                                "Figure 2. Colour: unique explained variance &Delta;R&sup2; of that regressor, white "
                                "0 to dark blue 0.3.",
}
SHOWS = {
    "np_design_matrix": "Illustration only. What the encoding model is given for one episode: continuous and state "
                        "regressors, the interaction, and each event as a diagonal band of lagged copies.",
    "np_unitmap": "Illustration only. How each unit's dominant selectivity will be shown, layer by layer, with the "
                  "modulator's hidden state and its FiLM outputs separated.",
    "np_tuned_share": "Illustration only. Where in the network each variable is represented, layer by layer.",
    "np_kernels": "Illustration only. How quickly, and in which order, recurrent units respond to an event.",
    "np_tuning": "Illustration only. Whether injury scales the response to the rabbit (gain modulation).",
    "np_models": "Illustration only. How much each regressor group adds to the prediction, layer by layer.",
    "np_interaction_map": "Illustration only. Where the injury &times; rabbit interaction is encoded, and with which sign.",
    "np_worlds": "Illustration only. How the share of interaction-tuned units differs between worlds and agents.",
    "np_unitmap_per_regressor": "Illustration only. Mixed selectivity: units that appear in several regressor maps.",
}
TITLE = {"np_design_matrix": "Figure 1", "np_unitmap": "Figure 2", "np_tuned_share": "Figure 3", "np_kernels": "Figure 4",
         "np_tuning": "Figure 5", "np_models": "Figure 6", "np_interaction_map": "Figure 7", "np_worlds": "Figure 8",
         "np_unitmap_per_regressor": "Figure A1"}


def main():
    inv = inventory()
    page = open(os.path.join(PAGE_DIR, "page_template.html")).read()
    tok = {"{{TABLE:units}}": units_table(inv), "{{TABLE:sizes}}": sizes_table(inv),
           "{{N_GROUPS}}": str(len(inv["ordinary"]["obs_groups"])),
           "{{UNIT_TOTALS}}": (f"In total the ordinary agent computes {per_step(inv, 'ordinary'):,} values per step and "
                               f"the modulated agent {per_step(inv, 'modulated'):,}; both observe "
                               f"{inv['ordinary']['obs_dim']} input values and choose among "
                               f"{inv['ordinary']['action_dim']} actions."),
           "{{BUILT}}": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    for stem in AX:
        tok[f"{{{{FIG:{stem}}}}}"] = FB.figure(stem, f"{TITLE[stem]}, simulated numbers.", AX[stem], SHOWS[stem],
                                               f"{FIG}", title=f"{TITLE[stem]} (simulated numbers)")
    house = open(os.path.join(ROOT, "docs/develop/active/meta/house_style_sheet.template.html")).read()
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    vm = re.search(r'(<div class="lb fit" id="lb".*?\n</div>)', house, re.S)
    vs = re.search(r"(\(function \(\) \{\s*// full-size figure viewer.*?\}\)\(\);)", house, re.S)
    sc = re.search(r"(function updateCues\(\).*?)</script>", house, re.S)
    tok["{{HOUSE_STYLE}}"] = m.group(1)
    tok["{{LIGHTBOX}}"] = vm.group(1) + "\n<script>\n" + vs.group(1) + "\n" + sc.group(1) + "</script>"
    for k, v in tok.items():
        page = page.replace(k, v)
    for w in set(re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page)):
        page = page.replace(f"{{{{FONT:{w}}}}}", base64.b64encode(
            open(os.path.join(BB.FONTS, f"Pretendard-{w}.latin.woff"), "rb").read()).decode())
    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        raise SystemExit(f"unsubstituted tokens: {sorted(set(left))}")
    if len(page.encode()) > BB.PAGE_MAX_BYTES:
        raise SystemExit(f"page {len(page.encode()):,} bytes is over the limit")
    out = os.path.join(PAGE_DIR, "neural_recording_pipeline.html")
    open(out, "w").write(page)
    print(f"wrote {out}: {len(page.encode()):,} bytes")


if __name__ == "__main__":
    main()
