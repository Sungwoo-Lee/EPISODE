#!/usr/bin/env python3
"""build_page.py - assemble the fast-bush-healing replication results page.

Fills docs/experiments/active/hypervigilance/fast_heal_replication/page_template.html with the house style,
the figures of figures.py (embedded, each with the data statement its script emitted), the tables and every
number in the prose -- computed here from the experiment-test CSVs, none typed by hand. Reuses the cross-run
page's builder helpers (figure, table, num_text) by import.

    $P scripts/analysis/studies/fast_heal_replication/build_page.py
"""
import base64
import datetime
import html
import importlib.util
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
import figures as RF  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "f7b_build_page", os.path.join(ROOT, "scripts", "analysis", "studies", "f7b_across_runs", "build_page.py"))
FB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FB)
BB = FB.BB

PAGE_DIR = os.path.join(ROOT, "docs/experiments/active/hypervigilance/fast_heal_replication")
FB.FIG_DIR = os.path.join(PAGE_DIR, "figures")      # FB.figure() / img_tag() read the figures from here
HL = RF.HL
FIG = "scripts/analysis/studies/fast_heal_replication/figures.py"


def pp(v):
    t = f"{v:+.0f}"
    return "0" if t in ("+0", "-0") else FB.num_text(t)


def main():
    page = open(os.path.join(PAGE_DIR, "page_template.html")).read()
    tok = {}
    R = RF.summary_rows()
    # ---- summary table and counts (main scene set per level)
    rows, cnt = [], {}
    for lab, E, ref in R:
        lv = next(l for l in RF.LEVELS if RF.LEVEL_NAME[l] in lab)
        for a in ("ordinary", "modulated"):
            e = E[a]
            rows.append({"run": lab if a == "ordinary" else "", "agent": a,
                         "inj": pp(e["inj"][0]), "injw": pp(e["injw"][0]), "pred": pp(e["pred"][0]),
                         "scenes": RF.SET_NAME[RF.MAIN_SET[lv]] if a == "ordinary" else ""})
        if not ref:
            c = cnt.setdefault(lv, {"inj": 0, "injw": 0, "pred": 0, "n": 0})
            c["n"] += 1
            for m in ("inj", "injw", "pred"):
                c[m] += int(E["modulated"][m][0] > E["ordinary"][m][0])
    tok["{{TABLE:summary}}"] = FB.table(pd.DataFrame(rows), ["run", "agent", "scenes", "inj", "injw", "pred"],
                                        ["run", "agent", "test scenes", "injury, no animal (pp)", "injury, rabbit (pp)",
                                         "predator (pp)"], num=("inj", "injw", "pred"), min_width=800)
    for lv, c in cnt.items():
        for m in ("inj", "injw", "pred"):
            tok[f"{{{{N_{lv}_{m}}}}}"] = f"{c[m]} of {c['n']}"
    # ---- own vs neutral (levels 05, 06), matched seeds, injury effect with the wandering rabbit
    sc_rows = []
    for lv in ("l05", "l05fix", "l06"):
        for st in ("own", "neutral"):
            up, n, d = 0, 0, []
            for s in RF.SEEDS:
                o = RF.effect(RF.leaf(lv, st, "ordinary", s), ("rabbitwander", "70"), ("rabbitwander", "00"))
                m = RF.effect(RF.leaf(lv, st, "modulated", s), ("rabbitwander", "70"), ("rabbitwander", "00"))
                if o is None or m is None:
                    continue
                n += 1
                up += int(m[0] > o[0])
                d.append(m[0] - o[0])
            set_name = RF.SET_NAME[st] + (" (fixed start)" if lv == "l05fix" and st == "own" else "")
            sc_rows.append({"level": RF.LEVEL_NAME[lv] if st == "own" else "", "set": set_name, "n": n,
                            "up": f"{up} of {n}", "d": pp(pd.Series(d).median()) if d else "&ndash;"})
            tok[f"{{{{SC_{lv}_{st}}}}}"] = f"{up} of {n}"
    tok["{{TABLE:scenes}}"] = FB.table(pd.DataFrame(sc_rows), ["level", "set", "n", "up", "d"],
                                       ["level", "test scenes", "seeds", "modulated larger, rabbit",
                                        "median diff. (pp)"], num=("n", "up", "d"), min_width=560)
    # ---- dose numbers per level (no animal, injury 0 -> 90, mean over seeds)
    for lv in RF.LEVELS:
        for a, A in (("ordinary", "O"), ("modulated", "M")):
            for inj in ("00", "90"):
                vals = [HL.K.on_grid(HL.series(HL.grid_leaf(f"rep_{lv}_s{s}", a, "none"), "none", inj),
                                     HL.LO_M, HL.HI_M, HL.SPACING_M).mean() for s in RF.SEEDS]
                tok[f"{{{{D_{lv}_{A}{inj}}}}}"] = " / ".join(f"{v:.0f}" for v in vals)
    # ---- figures
    sum_axes = ("Vertical: one row per trained pair (level and seed), the two rows labelled \"22 Sep original\" "
                "are the original pairs, drawn with pale marks; in each row the upper mark is the ordinary agent (open grey circle), the lower the modulated "
                "agent (filled black square). Horizontal, left: injury 70 minus injury 0 with no animal; middle: the "
                "same with the wandering rabbit (the two share one scale); right: hunting predator minus no animal, "
                "unhurt. All in percentage points of bush dwell, mean over the checkpoints from 2 to 10 M training "
                "steps, with a 95 % interval. Level 04 is read in its core scenes, levels 05 and 06 in no-temperature scenes.")
    tok["{{FIG:summary}}"] = FB.figure(
        "rep_summary", "Rows of paired dot-and-interval marks, one row per level and seed, three panels.", sum_axes,
        "Whether the modulated agent's larger injury effect, seen in the 22-Sep pairs, repeats across seeds; the "
        "counts are in the text above.", f"{FIG} --figure summary", title="Figure R1 &mdash; every pair, three effects")
    dose_axes = ("Horizontal: starting injury of the test, 0 (unhurt) to 90 in steps of 10. Vertical: bush dwell, the "
                 "share of the scene's 100 steps spent on the bush (%), mean over the checkpoints from 2 to 10 M "
                 "training steps, 0&ndash;100 in every panel. Rows: seeds 42, 43, 44; columns: no animal, wandering "
                 "rabbit, chasing rabbit, hunting predator. Open grey circles: ordinary agent; filled black squares: "
                 "modulated agent; dashed edges and shading: 95 % interval.")
    train_axes = ("Horizontal: training, in million steps (0&ndash;10). Vertical: bush dwell (%, 0&ndash;100), the same "
                  "scale in every panel. Rows: four scenes; columns: the ordinary and the modulated agent. Ten lines "
                  "per panel, one per starting injury of the test: grey = 0 (unhurt), light to dark blue = 10 to 90; "
                  "each line averages 5 neighbouring checkpoints. Grey here means unhurt, not the ordinary agent as in Figures R1&ndash;R4 and R8. Text above each panel: bush dwell at injury 0, 50 "
                  "and 90, mean over 2&ndash;10 M steps. The shaded first 2 M steps are not used in those means.")
    FIGNO = {"l04": (2, 5), "l05": (3, 6), "l06": (4, 7), "l05fix": (8, 9)}   # (dose, training) figure numbers
    for lv in RF.LEVELS:
        scene = "core scenes" if lv == "l04" else "no-temperature scenes"
        tok[f"{{{{FIG:dose_{lv}}}}}"] = FB.figure(
            f"rep_dose__{lv}", f"Twelve panels, three seeds by four scenes, {RF.LEVEL_NAME[lv]}: bush dwell against "
            "starting injury, ordinary and modulated.", dose_axes + f" {RF.LEVEL_NAME[lv].capitalize()}, {scene}.",
            "Read each row on its own: does the modulated agent's calm-scene line start low and rise steadily with "
            "injury while the ordinary agent's sits higher and flatter, as in the 22-Sep pair?",
            f"{FIG} --figure dose --level {lv}", title=f"Figure R{FIGNO[lv][0]} &mdash; {RF.LEVEL_NAME[lv]}, bush dwell against starting injury")
        for s in RF.SEEDS:
            tok[f"{{{{FIG:train_{lv}_{s}}}}}"] = FB.figure(
                f"rep_train__{lv}_s{s}", f"Eight panels, {RF.LEVEL_NAME[lv]}, seed {s}: bush dwell across training, "
                "ten lines per panel for starting injuries 0 to 90.", train_axes + f" {scene.capitalize()}.",
                "The same run across training: whether the ten injury lines stay stacked in order (a steady injury "
                "effect) or tangle and swing together.", f"{FIG} --figure train --level {lv} --seed {s}",
                title=f"Figure R{FIGNO[lv][1]}{'abc'[RF.SEEDS.index(s)]} &mdash; {RF.LEVEL_NAME[lv]}, seed {s}, across training")
    # ---- the answer, from the counts above (main scene set per level)
    MAIN = ("l04", "l05", "l06")            # the replication proper; the fixed-start arm is reported in section 06
    up = sum(cnt[l]["injw"] for l in MAIN)
    n = sum(cnt[l]["n"] for l in MAIN)
    ref04 = next(E for lab, E, ref in R if ref and "level 04" in lab)
    s42 = next(E for lab, E, ref in R if not ref and "level 04" in lab and lab.endswith("seed 42"))
    tok["{{ANSWER}}"] = (
        "<div class=\"callout\"><p><strong>Only partly.</strong> Across the nine new pairs, the modulated agent's "
        f"injury effect with the wandering rabbit is the larger one in {up} of {n} (level 04: {cnt['l04']['injw']} of 3; "
        f"level 05: {cnt['l05']['injw']} of 3; level 06: {cnt['l06']['injw']} of 3). Where the 22-Sep pattern does repeat "
        "&mdash; the modulated agent's calm-scene hiding starting low and rising steadily with injury while an ordinary "
        "agent sits higher and flatter &mdash; it is clearest at level 04 (Figure R2). At levels 05 and 06 the two agent "
        "types mostly look alike.</p>"
        f"<p><strong>The same seed does not give the same agent.</strong> Level 04, seed 42, repeats the 22-Sep training "
        f"with the same settings and seed, yet its ordinary agent's injury effect with no animal is {pp(s42['ordinary']['inj'][0])} "
        f"points against {pp(ref04['ordinary']['inj'][0])} on 22 September. Training is not reproducible run for run, so a "
        "pattern seen in one run needs several seeds before it is believed.</p>"
        f"<p><strong>Starting every episode at the same body temperature does not change this.</strong> Six more level-05 "
        f"agents trained that way, as on 22 September: the modulated agent's injury effect with the wandering rabbit is the "
        f"larger one in {cnt['l05fix']['injw']} of {cnt['l05fix']['n']} pairs (<a href=\"#fix\">section 06</a>).</p></div>")
    fx, r5 = cnt["l05fix"], cnt["l05"]
    tok["{{FIX_TEXT}}"] = (
        f"<p>In the no-temperature scenes the modulated agent's injury effect with the wandering rabbit is the larger one in "
        f"{fx['injw']} of {fx['n']} fixed-start pairs (random start: {r5['injw']} of {r5['n']}); with no animal in "
        f"{fx['inj']} of {fx['n']} (random start: {r5['inj']} of {r5['n']}); the predator effect in {fx['pred']} of "
        f"{fx['n']} (random start: {r5['pred']} of {r5['n']}). Training-like scenes (fixed start): {tok['{{SC_l05fix_own}}']} "
        f"for the rabbit injury effect.</p>")
    tok["{{BUILT}}"] = datetime.date.today().isoformat()
    # ---- house style (as the cross-run page)
    house = open(BB.HOUSE).read()
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
    page = re.sub(r'<p class="prov">.*?</p>', lambda m: m.group(0).replace("--", "&#8209;&#8209;"), page, flags=re.S)
    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        raise SystemExit(f"unsubstituted tokens: {sorted(set(left))}")
    if len(page.encode()) > BB.PAGE_MAX_BYTES:
        raise SystemExit(f"page {len(page.encode()):,} bytes is over the limit")
    out = os.path.join(PAGE_DIR, "fast_heal_replication.html")
    open(out, "w").write(page)
    print(f"wrote {out}: {len(page.encode()):,} bytes")


if __name__ == "__main__":
    main()
