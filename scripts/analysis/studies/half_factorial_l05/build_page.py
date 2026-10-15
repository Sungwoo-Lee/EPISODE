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


def rt_ref(heal, inj):
    """Table 2's rows: the plain level-05 reference first (user, 2026-10-15), then the design's runs."""
    ref = pd.DataFrame([D.run_row(D.REF, a, heal, inj, s) for a in D.AGENTS for s in D.ref_seeds(a)])
    return pd.concat([ref, rt(heal, inj)], ignore_index=True)


def run_table():
    rows = []
    base = rt_ref("off", "70")
    for i, b in base.iterrows():
        ref = b["world"] == D.REF   # short label: "(reference)" does not break and widened the table (format review)
        r = {"world": "level 05" if ref else f'{b["world"]}' + ("" if b["world"] > 1 else " (base)"),
             "changed": "reference" if ref else b["new"] if b["new"] != "-" else "&mdash;",
             "agent": f'{b["agent"]}, seed {b["seed"]}'}
        for c in CASES:
            x = rt_ref(*c).iloc[i]
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


def seed_cell(w, a, seed):
    if seed == 42 or w == 1 or D.seed_status(w, a, seed)[0] == "tested":
        x = D.run_row(w, a, "off", "70", seed)
        return ci_cell(x["inter"], x["inter_lo"], x["inter_hi"]) + \
            f'<br><span class="ci nw">pattern: {"yes" if x["signature"] else "no"}</span>'
    st, ck = D.seed_status(w, a, seed)
    txt = {"testing": "finished, tests running", "queued": "queued for training",
           "training": f"training, {ck / 1e6:.1f} M of 10 M"}[st]
    # status text in a number column: body font, wraps, left-aligned (format review F22/F35)
    return (f'<span style="display:block;white-space:normal;text-align:left;font-family:var(--f-body);'
            f'font-variant-numeric:normal">{txt}</span>')


def seed_table():
    rows = []
    for w in D.WORLDS:
        for a in D.AGENTS:
            r = {"world": f"{w}" + ("" if w > 1 else " (base)"), "changed": D.NEW[w] or "&mdash;", "agent": a,
                 "s42": seed_cell(w, a, 42)}
            for s_ in D.EXTRA_SEEDS:
                r[f"s{s_}"] = seed_cell(w, a, s_) if (w > 1 or s_ == 43) else "&mdash;"
            rows.append(r)
    cols = ["world", "changed", "agent", "s42", "s43", "s44"]
    return FB.table(pd.DataFrame(rows), cols, ["world", "changed", "agent", "seed 42", "seed 43", "seed 44"],
                    num=("s42", "s43", "s44"), raw=("changed", "s42", "s43", "s44"), min_width=740)


def food_cell(g):
    txt = f'<span class="nw">{pp(g["effect"])}</span><br><span class="ci nw">bar {g["bar"]:.1f}' \
          f'{" &dagger;" if not g["same_sign_6_8_10"] else ""}</span>'
    return f"<strong>{txt}</strong>" if g["verdict"] == "clears the bar" else txt


def food_table():
    """Group test (seed 42) with the food item and in the food-free scenes, side by side."""
    ready = all(D.has_nofood(w, a, s) for w in D.WORLDS for a in D.AGENTS for s in ((42, 43) if w == 1 else (42,)))
    rows = []
    for t in ("A", "B", "C", "D", "AB+CD", "AC+BD", "AD+BC"):
        r = {"term": f"{t}: {D.GROUPS[t]}" if t in D.GROUPS else f"pair {t}"}
        for c in CASES:
            r["f_" + "_".join(c)] = food_cell(D.group_effects(rt(*c)).set_index("term").loc[t])
            r["n_" + "_".join(c)] = (food_cell(D.group_effects(D.run_table(*c, grid="grid_nofood")).set_index("term").loc[t])
                                     if ready else "pending")
        rows.append(r)
    cols = ["term"] + [k + "_".join(c) for c in CASES for k in ("f_", "n_")]
    heads = ["setting change"] + [f"{CASE_NAME[c]}, {k}" for c in CASES for k in ("with food", "food-free")]
    return FB.table(pd.DataFrame(rows), cols, heads, num=tuple(cols[1:]), raw=tuple(cols[1:]), min_width=900)


def food_count():
    spec = importlib.util.spec_from_file_location("hf_figures", os.path.join(HERE, "figures.py"))
    FG_ = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(FG_)   # by path: another 'figures' module is already on sys.path
    n = len(FG_.food_runs())
    tot = 18 + sum(D.seed_status(w, a, s)[0] == "tested" for w in D.WORLDS[1:] for a in D.AGENTS for s in D.EXTRA_SEEDS)
    return f"{n} of the {tot} runs tested with the food item also have their food-free test complete"


def seed_count():
    st = [D.seed_status(w, a, s_)[0] for w in D.WORLDS[1:] for a in D.AGENTS for s_ in D.EXTRA_SEEDS]
    n = {k: st.count(k) for k in ("tested", "testing", "training", "queued")}
    parts = [f"{n['tested']} of {len(st)} repeat runs are finished and tested"]
    parts += [f"{n[k]} {txt}" for k, txt in (("testing", "finished and being tested"), ("training", "training"),
                                             ("queued", "queued")) if n[k]]
    return "; ".join(parts)


CURVES_AXES = ("Horizontal: starting injury of the test, 0 (unhurt) to 90 in steps of 10. Vertical: bush dwell, the "
               "share of the test's 100 steps spent on the bush (%), 0&ndash;100 in every panel. Left column: healing "
               "switched off in the test scene, so the starting injury lasts the whole test; right column: healing on, as "
               "in training. Grey open circles: no animal; orange squares: a harmless wandering rabbit. Each point is the "
               "mean over the run's newest 20 tested checkpoints; dashed edges and shading: 95&nbsp;% interval. One row per agent "
               "and seed: seed 42, then each repeat seed (43, 44) once its run is finished and tested (section 06). "
               "Solid lines with shading: the test scenes with one food item (as everywhere on this page); dotted lines "
               "in the same colours, without shading: the same run in the food-free copy of the scenes, "
               "drawn once that test is complete.")
EXTRA_AXES = ("Horizontal: starting injury of the test, 0 to 90. Vertical: the rabbit's extra bush dwell &mdash; bush "
              "dwell with the wandering rabbit minus bush dwell with no animal, in percentage points (pp), mean over the "
              "newest 20 tested checkpoints, with a 95&nbsp;% interval (dashed edges, shading). Blue diamonds: healing off; "
              "green open triangles: healing on. The dotted line in each colour marks that curve's value for an unhurt "
              "agent; a curve above its dotted line means injury makes the rabbit matter more. Every world's figure "
              "uses the same vertical range.")
TRAIN_AXES = ("Horizontal: training, in million steps (0&ndash;10); the shaded part is the newest 20 tested checkpoints, "
              "the window every summary on this page uses. Vertical: the injury contrast in percentage points &mdash; the "
              "rabbit's extra bush dwell at the injury named above the column minus the same when unhurt. Above zero: "
              "injury makes the rabbit matter more. Left column: injury 70 (the design's headline injury); right: injury 10. "
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
               "and the hunting predator &mdash; first unhurt (injury 0), then at injury {INJ}. Rows: one per run, "
               "the plain level-05 reference (seeds 42&ndash;44) first, then world 1 (both seeds), then worlds 2&ndash;8 "
               "(seed 42), ordinary above modulated. Colour and number: bush dwell, the "
               "share of the test's 100 steps spent on the bush (%), mean over the newest 20 tested checkpoints, healing "
               "off in the test scene. No intervals are shown.")


SEEDS_AXES = ("Horizontal: the injury contrast at injury 70, in percentage points of bush dwell &mdash; the rabbit's "
              "extra bush dwell when injured minus the same when unhurt, mean over the run's newest 20 tested "
              "checkpoints; the line through each mark is its 95&nbsp;% interval. Vertical: the eight training worlds, "
              "world 1 (no change) on top, then worlds 2&ndash;8 with the setting groups they change. Within a world, one "
              "mark per seed: black circle seed 42 (the screen), purple plus sign seed 43, ochre cross "
              "seed 44; world 1 shows its two existing seeds. Columns: ordinary and modulated agent. Rows: healing off in "
              "the test scene (top, the headline) and healing on (bottom). A seed appears once its run has finished "
              "training and been tested. Purple and ochre are outside the house series colours on purpose: blue and green "
              "already mean healing off and on on this page.")
SEEDTRAIN_AXES = ("Horizontal: training, in million steps (0&ndash;10). Vertical: the injury contrast at injury 70 "
                  "with healing off, in percentage points, as a 5-checkpoint moving average. One panel per world (rows) "
                  "and agent (columns). Solid black: seed 42; purple dashed: seed 43; ochre dotted: seed 44. All panels "
                  "share one vertical range, which differs from Figure 4's because these lines are averaged.")


FOOD_AXES = ("Horizontal: a run's injury contrast at injury 70 in the scenes with the food item (as in sections "
             "02&ndash;06); vertical: the same run's injury contrast in the food-free copy of the scenes. Both in "
             "percentage points of bush dwell, mean over the newest 20 tested checkpoints, with the 95&nbsp;% interval "
             "as thin lines. One mark per run: circle ordinary agent, open square modulated agent; colour by seed "
             "(black 42, purple 43, ochre 44). Left: healing off in the test scene; right: healing on. The dashed "
             "diagonal is &ldquo;same value with and without food&rdquo;; marks above it hide more near the rabbit when "
             "there is no food to leave for. Runs more than 15 points off the diagonal carry their world number.")


def world_tabs():
    tl, panels = [], []
    # the plain level-05 reference tab comes first, left of W1, and is the one shown on opening (user, 2026-10-15)
    ws = ([D.REF] if any(D.ref_seeds(a) for a in D.AGENTS) else []) + list(D.WORLDS)
    for w in ws:
        first = w == ws[0]
        sel = "true" if first else "false"
        lab = ("W1" if w == 1 else "Level 05 &middot; reference" if w == D.REF
               else f"W{w} &middot; {'+'.join(D.NEW[w])}")
        tl.append(f'<button class="tab" role="tab" id="tab-w{w}" aria-controls="panel-w{w}" aria-selected="{sel}"'
                  + ("" if first else ' tabindex="-1"') + f">{lab}</button>")
        name = ("world 1, the lookalike world (no change)" if w == 1 else
                "plain level 05, the reference: the same two agents trained 10 million steps on level 05 itself, "
                "without the lookalike world's three changes (same smell for predator and rabbit, pounce at 3 cells, "
                "half-size food), seeds 42, 43 and 44, tested in the same world-1 scenes" if w == D.REF else
                f"world {w}, changed: " + "; ".join(f"{g} {D.GROUP_PLAIN[g]}" for g in D.NEW[w]))
        where = "level 05" if w == D.REF else f"world {w}"
        body = [f'<p class="wname"><strong>{name[0].upper() + name[1:]}.</strong></p>']
        for k, (kind, axes, shows, alt) in enumerate((
                ("curves", CURVES_AXES, "Whether hiding rises with injury, and whether the rabbit line separates from "
                 "the no-animal line more at some injuries than when unhurt.",
                 "Panels of bush dwell against starting injury, healing off and on, no animal and rabbit"),
                ("extra", EXTRA_AXES, "At which injuries, if any, the rabbit adds more hiding than it adds to an unhurt "
                 "agent.", "Panels of the rabbit's extra bush dwell against starting injury, healing off and on"),
                ("train", TRAIN_AXES, "Whether the injury contrast is steady across training or rises and falls.",
                 "Panels of the injury contrast across training, injury 70 and 10, healing off and on")), start=2):
            body.append(FB.figure(f"hf_{kind}__w{w}", alt + f", {where}.", axes, shows,
                                  f"{FIG} --figure {kind} --world {w}", title=f"Figure {k} &mdash; {where}"))
        panels.append(f'<div class="tabpanel" role="tabpanel" id="panel-w{w}" aria-labelledby="tab-w{w}" tabindex="0"'
                      + ("" if first else " hidden") + ">" + "\n".join(body) + "</div>")
    return ('<div class="tabs" data-tabs><p class="cue" hidden>more worlds &mdash; scroll the tabs sideways &rarr;</p>'
            '<div class="tablist" role="tablist" aria-label="Training world">'
            + "".join(tl) + "</div>" + "\n".join(panels) + "</div>")


ANIMAL_DEFAULT = "20"   # injury 20 keeps hiding off the ceiling (Visualization session, 2026-10-15)


def animal_tabs():
    """Figure 5, one heat map per injury level 10-90 behind tabs, as Figure 2's world tabs (user, 2026-10-15)."""
    tl, panels = [], []
    for i in FG_ANIMAL_INJ:
        on = i == ANIMAL_DEFAULT
        tl.append(f'<button class="tab" role="tab" id="tab-i{i}" aria-controls="panel-i{i}" aria-selected="{str(on).lower()}"'
                  + ("" if on else ' tabindex="-1"') + f">Injury {i}</button>")
        fig = FB.figure(
            f"hf_animals__i{i}", f"Heat map of bush dwell per run and test scene, unhurt and at injury {i}, healing off.",
            ANIMAL_AXES.replace("{INJ}", i),
            f"How much each run hides with each animal, unhurt and at injury {i}; how much room is left for the rabbit to add.",
            f"{FIG} --figure animals", title=f"Figure 5 &mdash; hiding with each animal, injury {i}")
        panels.append(f'<div class="tabpanel" role="tabpanel" id="panel-i{i}" aria-labelledby="tab-i{i}" tabindex="0"'
                      + ("" if on else " hidden") + ">" + fig + "</div>")
    return ('<div class="tabs" data-tabs><p class="cue" hidden>more injury levels &mdash; scroll the tabs sideways &rarr;</p>'
            '<div class="tablist" role="tablist" aria-label="Starting injury">'
            + "".join(tl) + "</div>" + "\n".join(panels) + "</div>")


FG_ANIMAL_INJ = [f"{i}" for i in range(10, 100, 10)]


def main():
    page = open(os.path.join(PAGE_DIR, "page_template.html")).read()
    tok = {"{{TABLE:group}}": group_table(), "{{TABLE:runs}}": run_table(), "{{WORLD_TABS}}": world_tabs()}
    tok["{{FIG:group}}"] = FB.figure(
        "hf_group", "Three panels of setting-change effects against the bar.", GROUP_AXES,
        "Which setting changes move the injury contrast by more than seed-to-seed noise would, in world 1's scenes.",
        f"{FIG} --figure group", title="Figure 1 &mdash; the setting changes against the bar")
    tok["{{FIG:animals}}"] = animal_tabs()
    tok["{{TABLE:seeds}}"] = seed_table()
    tok["{{SEED_COUNT}}"] = seed_count()
    tok["{{FIG:seeds}}"] = FB.figure(
        "hf_seeds", "Dot plot of the injury contrast per world and agent, one mark per seed.", SEEDS_AXES,
        "Whether a world's injury contrast in seed 42 is repeated by seeds 43 and 44, or moves by as much as world 1's "
        "two seeds differ.", f"{FIG} --figure seeds", title="Figure 6 &mdash; the injury contrast, seed by seed")
    tok["{{FIG:seedtrain}}"] = FB.figure(
        "hf_seedtrain", "Panels of the injury contrast across training, seeds overlaid.", SEEDTRAIN_AXES,
        "Whether the seeds agree over the whole of training or only at its end.",
        f"{FIG} --figure seedtrain", title="Figure 7 &mdash; the seeds across training")
    tok["{{BUILT}}"] = datetime.date.today().isoformat()
    house = open(BB.HOUSE).read()
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    vm = re.search(r'(<div class="lb fit" id="lb".*?\n</div>)', house, re.S)
    vs = re.search(r"(\(function \(\) \{\s*// full-size figure viewer.*?\}\)\(\);)", house, re.S)
    sc = re.search(r"(function updateCues\(\).*?)</script>", house, re.S)
    tok["{{HOUSE_STYLE}}"] = m.group(1)
    tabjs = sc.group(1)
    # a selected tab half outside its sideways-scrolling strip stays cut off: focus() does not scroll it
    # (format review 2026-10-15, at 834 px with two overflowing strips)
    assert tabjs.count("if (focus) t.focus();") == 1
    tabjs = tabjs.replace("if (focus) t.focus();",
                          "if (focus) t.focus();\n    t.scrollIntoView({block: 'nearest', inline: 'nearest'});")
    tok["{{LIGHTBOX}}"] = vm.group(1) + "\n<script>\n" + vs.group(1) + "\n" + tabjs + "</script>"
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
