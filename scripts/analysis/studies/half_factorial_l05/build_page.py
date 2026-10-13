#!/usr/bin/env python3
"""build_page.py - assemble the 'Predator, Food and Hazard Settings Screen' page.

Fills docs/experiments/active/hypervigilance/half_factorial_l05/page_template.html with the house style, the
figures of figures.py (embedded, each with the data statement its script emitted) and the tables, computed here
from data.py (none typed by hand). The summary prose lives in summary_note.html beside the template. Reuses the
cross-run page's builder helpers (figure, table, num_text, house style) by path, as the lookalike pilot page does.

    $P scripts/analysis/studies/half_factorial_l05/build_page.py
"""
import base64
import datetime
import importlib.util
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
import data as D  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "f7b_build_page", os.path.join(ROOT, "scripts", "analysis", "studies", "f7b_across_runs", "build_page.py"))
FB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FB)
BB = FB.BB

PAGE_DIR = os.path.join(ROOT, "docs/experiments/active/hypervigilance/half_factorial_l05")
FB.FIG_DIR = os.path.join(PAGE_DIR, "figures")
FIG = "scripts/analysis/studies/half_factorial_l05/figures.py"
CASES = (("off", "70"), ("off", "10"), ("on", "70"))
CASE_NAME = {("off", "70"): "healing off, injury 70", ("off", "10"): "healing off, injury 10",
             ("on", "70"): "healing on, injury 70"}


def pp(v):
    t = f"{v:+.1f}"
    return "0.0" if t in ("+0.0", "-0.0") else FB.num_text(t)


def ci_cell(m, lo, hi):
    txt = f'<span class="nw">{pp(m)}</span><br><span class="ci nw">[{pp(lo)}, {pp(hi)}]</span>'
    return f"<strong>{txt}</strong>" if lo > 0 or hi < 0 else txt


@__import__("functools").lru_cache(maxsize=None)
def rt(heal, inj):
    return D.run_table(heal, inj)


def group_table():
    rows = []
    for t in ("A", "B", "C", "D", "AB+CD", "AC+BD", "AD+BC"):
        r = {"term": f"{t}: {D.GROUPS[t]}" if t in D.GROUPS else f"pair {t}"}
        for c in CASES:
            g = D.group_effects(rt(*c)).set_index("term").loc[t]
            mark = "clears" if g["verdict"] == "clears the bar" else ""
            txt = f'<span class="nw">{pp(g["effect"])}</span><br><span class="ci nw">bar {g["bar"]:.1f}' \
                  f'{" &dagger;" if not g["same_sign_6_8_10"] else ""}</span>'
            r["_".join(c)] = f"<strong>{txt}</strong>" if mark else txt
        rows.append(r)
    cols = ["term"] + ["_".join(c) for c in CASES]
    return FB.table(pd.DataFrame(rows), cols, ["setting change"] + [CASE_NAME[c] for c in CASES],
                    num=tuple(cols[1:]), raw=tuple(cols[1:]), min_width=700)


def run_table():
    rows = []
    base = rt("off", "70")
    for i, b in base.iterrows():
        r = {"world": f'{b["world"]}' + ("" if b["world"] > 1 else " (base)"),
             "changed": b["new"] if b["new"] != "-" else "&mdash;", "agent": f'{b["agent"]}, seed {b["seed"]}'}
        for c in CASES:
            x = rt(*c).iloc[i]
            r["_".join(c)] = ci_cell(x["inter"], x["inter_lo"], x["inter_hi"]) + \
                f'<br><span class="ci nw">{x["share_pos"] * 100:.0f} % of checkpoints &gt; 0</span>'
        r["rabbit"] = ci_cell(b["rabbit"], b["rabbit_lo"], b["rabbit_hi"])
        r["sig"] = "yes" if b["signature"] else "no"
        rows.append(r)
    cols = ["world", "changed", "agent"] + ["_".join(c) for c in CASES] + ["rabbit", "sig"]
    heads = ["world", "changed", "agent"] + [CASE_NAME[c] for c in CASES] + \
            ["rabbit alone, unhurt", "pattern"]
    return FB.table(pd.DataFrame(rows), cols, heads, num=tuple(cols[3:8]), raw=("changed",) + tuple(cols[3:7]),
                    min_width=880)


CURVES_AXES = ("Horizontal: starting injury of the test, 0 (unhurt) to 90 in steps of 10. Vertical: bush dwell, the "
               "share of the test's 100 steps spent on the bush (%), 0&ndash;100 in every panel. Left column: healing "
               "switched off in the test scene, so the starting injury lasts the whole test; right column: healing on, as "
               "in training. Grey open circles: no animal; orange squares: a harmless wandering rabbit. Each point is the "
               "mean over the run's newest 20 tested checkpoints; dashed edges and shading: 95&nbsp;% interval. One row per agent.")
EXTRA_AXES = ("Horizontal: starting injury of the test, 0 to 90. Vertical: the rabbit's extra bush dwell &mdash; bush "
              "dwell with the wandering rabbit minus bush dwell with no animal, in percentage points (pp), mean over the "
              "newest 20 tested checkpoints, with a 95&nbsp;% interval (dashed edges, shading). Blue diamonds: healing off; "
              "green open triangles: healing on. The dotted line in each colour marks that curve's value for an unhurt "
              "agent; a curve above its dotted line means injury makes the rabbit matter more. Every world's figure "
              "uses the same vertical range.")
TRAIN_AXES = ("Horizontal: training, in million steps (0&ndash;10); the shaded part is the newest 20 tested checkpoints, "
              "the window every summary on this page uses. Vertical: the injury contrast in percentage points &mdash; the "
              "rabbit's extra bush dwell at the injury named above the column minus the same when unhurt. Above zero: "
              "injury makes the rabbit matter more. Left column: injury 70 (fixed in the design); right: injury 10. "
              "Blue: healing off; green: healing on. Thin lines: single checkpoints; thick lines: the average of 5 "
              "neighbouring checkpoints. Every world's figure uses the same vertical range.")
GROUP_AXES = ("Horizontal: the effect of one setting change on the injury contrast, in percentage points of bush dwell: "
              "the mean over the 4 worlds with the change minus the mean over the 4 without it, averaged over the two "
              "agents. Vertical: the four setting changes A&ndash;D and the three pairs of two-way interactions the design "
              "cannot separate. Filled diamond: both agents averaged (black if it clears the bar and keeps its sign at "
              "6, 8 and 10 M steps, light grey otherwise); open circle: ordinary agent; open square: modulated agent. Shaded "
              "band: inside the bar, &plusmn;2 times the expected noise of such a contrast. Panels: healing off at injury "
              "70 (the headline), healing off at injury 10, healing on at injury 70.")
ANIMAL_AXES = ("Columns: four test scenes &mdash; no animal, the harmless rabbit wandering, the rabbit chasing the agent, "
               "and the hunting predator &mdash; first unhurt (injury 0), then at injury 70. Rows: one per run, world 1 "
               "(both seeds) first, then worlds 2&ndash;8, ordinary above modulated. Colour and number: bush dwell, the "
               "share of the test's 100 steps spent on the bush (%), mean over the newest 20 tested checkpoints, healing "
               "off in the test scene. No intervals are shown.")


def world_tabs():
    tl, panels = [], []
    for w in D.WORLDS:
        sel = "true" if w == 1 else "false"
        lab = "W1" if w == 1 else f"W{w} &middot; {'+'.join(D.NEW[w])}"
        tl.append(f'<button class="tab" role="tab" id="tab-w{w}" aria-controls="panel-w{w}" aria-selected="{sel}"'
                  + ("" if w == 1 else ' tabindex="-1"') + f">{lab}</button>")
        name = ("world 1, the lookalike world (no change)" if w == 1 else
                f"world {w}, changed: " + "; ".join(f"{g} {D.GROUP_PLAIN[g]}" for g in D.NEW[w]))
        body = [f'<p class="wname"><strong>{name[0].upper() + name[1:]}.</strong></p>']
        for k, (kind, axes, shows, alt) in enumerate((
                ("curves", CURVES_AXES, "Whether hiding rises with injury, and whether the rabbit line separates from "
                 "the no-animal line more at some injuries than when unhurt.",
                 "Panels of bush dwell against starting injury, healing off and on, no animal and rabbit"),
                ("extra", EXTRA_AXES, "At which injuries, if any, the rabbit adds more hiding than it adds to an unhurt "
                 "agent.", "Panels of the rabbit's extra bush dwell against starting injury, healing off and on"),
                ("train", TRAIN_AXES, "Whether the injury contrast is steady across training or rises and falls.",
                 "Panels of the injury contrast across training, injury 70 and 10, healing off and on")), start=2):
            body.append(FB.figure(f"hf_{kind}__w{w}", alt + f", world {w}.", axes, shows,
                                  f"{FIG} --figure {kind} --world {w}", title=f"Figure {k} &mdash; world {w}"))
        panels.append(f'<div class="tabpanel" role="tabpanel" id="panel-w{w}" aria-labelledby="tab-w{w}" tabindex="0"'
                      + ("" if w == 1 else " hidden") + ">" + "\n".join(body) + "</div>")
    return ('<div class="tabs" data-tabs><p class="cue" hidden>&larr; more worlds &mdash; scroll the tabs sideways</p>'
            '<div class="tablist" role="tablist" aria-label="Training world">'
            + "".join(tl) + "</div>" + "\n".join(panels) + "</div>")


def main():
    page = open(os.path.join(PAGE_DIR, "page_template.html")).read()
    tok = {"{{TABLE:group}}": group_table(), "{{TABLE:runs}}": run_table(), "{{WORLD_TABS}}": world_tabs()}
    tok["{{FIG:group}}"] = FB.figure(
        "hf_group", "Three panels of setting-change effects against the bar.", GROUP_AXES,
        "Which setting changes move the injury contrast by more than seed-to-seed noise would, in world 1's scenes.",
        f"{FIG} --figure group", title="Figure 1 &mdash; the setting changes against the bar")
    tok["{{FIG:animals}}"] = FB.figure(
        "hf_animals", "Heat map of bush dwell per run and test scene, healing off.", ANIMAL_AXES,
        "How much each run hides with each animal, unhurt and injured; how much room is left for the rabbit to add.",
        f"{FIG} --figure animals", title="Figure 5 &mdash; hiding with each animal")
    tok["{{BUILT}}"] = datetime.date.today().isoformat()
    house = open(BB.HOUSE).read()
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    vm = re.search(r'(<div class="lb fit" id="lb".*?\n</div>)', house, re.S)
    vs = re.search(r"(\(function \(\) \{\s*// full-size figure viewer.*?\}\)\(\);)", house, re.S)
    sc = re.search(r"(function updateCues\(\).*?)</script>", house, re.S)
    tok["{{HOUSE_STYLE}}"] = m.group(1)
    tok["{{LIGHTBOX}}"] = vm.group(1) + "\n<script>\n" + vs.group(1) + "\n" + sc.group(1) + "</script>"
    tok["{{SUMMARY}}"] = open(os.path.join(PAGE_DIR, "summary_note.html")).read()
    for k, v in tok.items():
        page = page.replace(k, v)
    for w in set(re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page)):
        page = page.replace(f"{{{{FONT:{w}}}}}", base64.b64encode(
            open(os.path.join(BB.FONTS, f"Pretendard-{w}.latin.woff"), "rb").read()).decode())
    page = re.sub(r'<p class="prov">.*?</p>', lambda mm: mm.group(0).replace("--", "&#8209;&#8209;"), page, flags=re.S)
    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        raise SystemExit(f"unsubstituted tokens: {sorted(set(left))}")
    if len(page.encode()) > BB.PAGE_MAX_BYTES:
        raise SystemExit(f"page {len(page.encode()):,} bytes is over the limit")
    out = os.path.join(PAGE_DIR, "half_factorial_l05.html")
    open(out, "w").write(page)
    print(f"wrote {out}: {len(page.encode()):,} bytes")


if __name__ == "__main__":
    main()
