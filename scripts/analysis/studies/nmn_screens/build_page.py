#!/usr/bin/env python3
"""build_page.py - assemble the 'Modulator Capacity and Input Screen' results page.

Fills docs/experiments/active/hypervigilance/nmn_screens/page_template.html with the house style, the figures
of figures.py (embedded, each with the data statement its script emitted), the stage-2 decision table and the
summary counts -- computed here from the readout tables, none typed by hand. Reuses the cross-run page's builder
helpers (figure, table, num_text, house style) by path, as the replication page does.

    $P scripts/analysis/studies/nmn_screens/build_page.py
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
import figures as SF  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "f7b_build_page", os.path.join(ROOT, "scripts", "analysis", "studies", "f7b_across_runs", "build_page.py"))
FB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FB)
BB = FB.BB
RO = SF.RO

PAGE_DIR = os.path.join(ROOT, "docs/experiments/active/hypervigilance/nmn_screens")
FB.FIG_DIR = os.path.join(PAGE_DIR, "figures")
FIG = "scripts/analysis/studies/nmn_screens/figures.py"
STUDY_NAME = {"cap": "capacity screen", "inp": "input screen"}
SCENE_NAME = {"neutral": "no-temperature", "own": "training-like"}   # display names of the two scene sets


def pp(v):
    if pd.isna(v):
        return "&ndash;"
    t = f"{v:+.1f}"
    return "0.0" if t in ("+0.0", "-0.0") else FB.num_text(t)


def tables():
    return {s: pd.read_csv(os.path.join(FB.FIG_DIR, f"screen_{s}_table.csv")) for s in RO.STUDY}


def main():
    page = open(os.path.join(PAGE_DIR, "page_template.html")).read()
    tok = {}
    T = tables()
    ref = T["cap"][T["cap"].kind == "reference"]
    rmax = {m: ref[f"neutral_{m}"].max() for m in ("inj", "injw", "pred")}
    rmin = {m: ref[f"neutral_{m}"].min() for m in ("inj", "injw", "pred")}
    # ---- decision table (both screens; references first, once)
    D = pd.concat([ref.assign(screen="reference")] + [T[s][T[s].kind == "cell"].assign(screen=STUDY_NAME[s])
                                                      for s in RO.STUDY], ignore_index=True)
    D["row"] = D.row.str.replace(", seed 42", "", regex=False)
    for c in ("neutral_inj", "neutral_injw", "neutral_pred", "own_inj", "own_injw"):
        D[c] = D[c].map(pp)
    D["ckpts"] = D.neutral_ckpts.astype(int).astype(str) + " of 41"
    for c in ("rule_strict", "rule_option_A"):
        D[c] = D[c].map(lambda v: "n/a" if pd.isna(v) else ("pass" if str(v) == "True" else "no"))
    tok["{{TABLE:decision}}"] = FB.table(
        D, ["screen", "row", "neutral_inj", "neutral_injw", "neutral_pred", "own_inj", "own_injw", "ckpts",
            "rule_strict", "rule_option_A"],
        ["screen", "agent / setting", "injury, no animal", "injury, rabbit", "predator", "training-like: injury, no animal",
         "training-like: injury, rabbit", "check&shy;points", "strict", "option A"],
        num=("neutral_inj", "neutral_injw", "neutral_pred", "own_inj", "own_injw", "ckpts"), min_width=1080)
    # ---- summary (counts against the six references, neutral scenes)
    lines = []
    for s in RO.STUDY:
        C = T[s][T[s].kind == "cell"]
        name = lambda r: r.row.replace(", seed 42", "")
        up_w = [name(r) for _, r in C.iterrows() if r.neutral_injw > rmax["injw"]]
        up_n = [name(r) for _, r in C.iterrows() if r.neutral_inj > rmax["inj"]]
        lo_p = [name(r) for _, r in C.iterrows() if r.neutral_pred < rmin["pred"]]
        pa = int((C.rule_option_A.astype(str) == "True").sum())
        lines.append(
            f"<li><strong>{STUDY_NAME[s].capitalize()} ({len(C)} settings).</strong> Injury effect with the wandering "
            f"rabbit above every reference (more than {pp(rmax['injw'])} pp): {len(up_w)} "
            f"({'; '.join(up_w) if up_w else 'none'}). With no animal above every reference ({pp(rmax['inj'])} pp): "
            f"{len(up_n)} ({'; '.join(up_n) if up_n else 'none'}). Predator effect below every reference "
            f"({pp(rmin['pred'])} pp): {len(lo_p)} ({'; '.join(lo_p) if lo_p else 'none'}). Option A passes {pa}; the "
            f"strict rule passes {int((C.rule_strict.astype(str) == 'True').sum())}.</li>")
    tok["{{SUMMARY}}"] = ("<div class=\"callout\"><p>No-temperature scenes, seed 42, against the six level-05 references "
                          "(ordinary and current modulated agents, seeds 42&ndash;44):</p><ul>" + "".join(lines) +
                          "</ul>{{SUMMARY_NOTE}}</div>")
    # ---- figures
    eff_axes = ("Vertical: one row per agent; above the line the six level-05 references (grey: ordinary agents, open "
                "circles; current modulated agents, filled squares), below it the new settings (blue diamonds), seed 42. "
                "Horizontal, left: injury 70 minus injury 0 with no animal; middle: the same with the wandering rabbit "
                "(the two share one scale); right: hunting predator minus no animal, unhurt. All in percentage points "
                "of bush dwell, mean over the checkpoints from 2 to 10 M training steps, with a 95 % interval.")
    for k, (s, st) in enumerate([(s, st) for s in RO.STUDY for st in RO.SETS]):
        tok[f"{{{{FIG:{s}_{st}}}}}"] = FB.figure(
            f"screen_{s}__{st}", f"Rows of dot-and-interval marks, {STUDY_NAME[s]}, {SCENE_NAME[st]} scenes: three effects per agent.",
            eff_axes + f" {SCENE_NAME[st].capitalize()} scenes.",
            "Whether any setting's injury effects sit outside the spread of the six references, and whether its "
            "predator effect changes.", f"{FIG} --figure effects --study {s}",
            title=f"Figure S{k + 1} &mdash; {STUDY_NAME[s]}, {SCENE_NAME[st]} scenes")
    dose_axes = ("Horizontal: starting injury of the test, 0 (unhurt) to 90 in steps of 10. Vertical: bush dwell, the "
                 "share of the scene's 100 steps spent on the bush (%), mean over the checkpoints from 2 to 10 M training "
                 "steps, 0&ndash;100 in every panel. Rows: the current modulated agent, then one row per setting; "
                 "columns: no animal, wandering rabbit, chasing rabbit, hunting predator (injury-grid no-temperature scenes). "
                 "Open grey circles: the level-05 ordinary agent, seed 42; filled black squares: the row's modulated "
                 "agent, seed 42; dashed edges and shading: 95 % interval.")
    for k, (stem, extra, args) in enumerate([("cap_h32", "modulator memory 32", "--study cap --size 32"),
                                             ("cap_h64", "modulator memory 64", "--study cap --size 64"),
                                             ("cap_h128", "modulator memory 128", "--study cap --size 128"),
                                             ("inp", "input screen", "--study inp")]):
        tok[f"{{{{FIG:dose_{stem}}}}}"] = FB.figure(
            f"screen_dose__{stem}", f"Panels of bush dwell against starting injury, {extra}.", dose_axes,
            "Whether a setting's no-animal and rabbit lines start low and rise more steeply with injury than the "
            "ordinary agent's (more injury-driven hiding), or sit higher everywhere (more hiding regardless of injury).",
            f"{FIG} --figure dose {args}", title=f"Figure S{5 + k} &mdash; {extra}")
    train_axes = ("Horizontal: training, in million steps (0&ndash;10). Vertical: bush dwell (%, 0&ndash;100), the same "
                  "scale in every panel. Rows: four scenes; columns: the level-05 ordinary agent, seed 42 (left) and the "
                  "setting, seed 42 (right). Ten lines per panel, one per starting injury of the test: grey = 0 (unhurt), "
                  "light to dark blue = 10 to 90; each line averages 5 neighbouring checkpoints. Grey here means unhurt, "
                  "not the ordinary agent as in Figures S1&ndash;S8. Text above each panel: bush dwell at injury 0, 50 and "
                  "90, mean over 2&ndash;10 M steps. The shaded first 2 M steps are not used in those means.")
    parts, n = [], 9
    for s in RO.STUDY:
        folder, cells, nm = RO.STUDY[s]
        parts.append(f'<details class="more"><summary>{STUDY_NAME[s].capitalize()} ({len(cells)} settings)</summary>')
        for c in cells:
            parts.append(f'<h4 class="fh"><span class="n">Figure S{n}</span>{nm(c)}</h4>')
            parts.append(FB.figure(
                f"screen_train__{s}_{c}", f"Eight panels: bush dwell across training, ten injury lines, {nm(c)}.",
                train_axes, "The setting across training: whether its ten injury lines stay stacked in order (a steady "
                "injury effect) or tangle, against the ordinary agent.", f"{FIG} --figure train --study {s} --cell {c}",
                title=f"Figure S{n} &mdash; {nm(c)}, across training"))
            n += 1
        parts.append("</details>")
    tok["{{TRAIN}}"] = "\n".join(parts)
    tok["{{BUILT}}"] = datetime.date.today().isoformat()
    note = os.path.join(PAGE_DIR, "summary_note.html")
    # ---- house style (as the cross-run and replication pages)
    house = open(BB.HOUSE).read()
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    vm = re.search(r'(<div class="lb fit" id="lb".*?\n</div>)', house, re.S)
    vs = re.search(r"(\(function \(\) \{\s*// full-size figure viewer.*?\}\)\(\);)", house, re.S)
    sc = re.search(r"(function updateCues\(\).*?)</script>", house, re.S)
    tok["{{HOUSE_STYLE}}"] = m.group(1)
    tok["{{LIGHTBOX}}"] = vm.group(1) + "\n<script>\n" + vs.group(1) + "\n" + sc.group(1) + "</script>"
    for k, v in tok.items():
        page = page.replace(k, v)
    page = page.replace("{{SUMMARY_NOTE}}", open(note).read() if os.path.exists(note) else "")
    for w in set(re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page)):
        page = page.replace(f"{{{{FONT:{w}}}}}", base64.b64encode(
            open(os.path.join(BB.FONTS, f"Pretendard-{w}.latin.woff"), "rb").read()).decode())
    page = re.sub(r'<p class="prov">.*?</p>', lambda mm: mm.group(0).replace("--", "&#8209;&#8209;"), page, flags=re.S)
    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        raise SystemExit(f"unsubstituted tokens: {sorted(set(left))}")
    if len(page.encode()) > BB.PAGE_MAX_BYTES:
        raise SystemExit(f"page {len(page.encode()):,} bytes is over the limit")
    out = os.path.join(PAGE_DIR, "nmn_screens.html")
    open(out, "w").write(page)
    print(f"wrote {out}: {len(page.encode()):,} bytes")


if __name__ == "__main__":
    main()
