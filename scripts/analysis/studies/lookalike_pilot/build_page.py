#!/usr/bin/env python3
"""build_page.py - assemble the 'Lookalike Animals Pilot Results' page.

Fills docs/experiments/active/hypervigilance/lookalike_pilot/page_template.html with the house style, the
figures of figures.py (embedded, each with the data statement its script emitted) and the contrast table,
computed here from the test CSVs (none typed by hand). The summary prose lives in summary_note.html beside
the template. Reuses the cross-run page's builder helpers (figure, table, num_text, house style) by path.

    $P scripts/analysis/studies/lookalike_pilot/build_page.py
"""
import base64
import datetime
import importlib.util
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
import figures as LF  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "f7b_build_page", os.path.join(ROOT, "scripts", "analysis", "studies", "f7b_across_runs", "build_page.py"))
FB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FB)
BB = FB.BB

PAGE_DIR = os.path.join(ROOT, "docs/experiments/active/hypervigilance/lookalike_pilot")
FB.FIG_DIR = os.path.join(PAGE_DIR, "figures")
FIG = "scripts/analysis/studies/lookalike_pilot/figures.py"
GROUPS = ("lookalike", "replication", "fixedstart")


def contrast(lf, inj):
    """(rabbit - none at inj) - (rabbit - none at injury 0), per checkpoint on the 2-10 M grid."""
    return (LF.extra_series(lf, inj) - LF.extra_series(lf, "00")).dropna()


def pp(v):
    t = f"{v:+.1f}"
    return "0.0" if t in ("+0.0", "-0.0") else FB.num_text(t)


def cell(v):
    m, lo, hi = LF.prof(v)
    star = lo > 0 or hi < 0
    txt = f"<span class=\"nw\">{pp(m)}</span><br><span class=\"ci nw\">[{pp(lo)}, {pp(hi)}]</span>"
    return f"<strong>{txt}</strong>" if star else txt


def contrast_table():
    rows = []
    for g in GROUPS:
        for a, s in LF.runs(g):
            r = {"group": LF.GROUP_NAME[g].replace(" agents", ""), "agent": f"{a}, seed {s}"}
            for heal in ("on", "off"):
                lf = LF.leaf(g, heal, a, s)
                for inj in ("10", "70"):
                    r[f"{heal}_{inj}"] = cell(contrast(lf, inj))
            rows.append(r)
    D = pd.DataFrame(rows)
    return FB.table(D, ["group", "agent", "on_10", "on_70", "off_10", "off_70"],
                    ["agents", "agent, seed", "healing on: injury 10", "healing on: injury 70",
                     "healing off: injury 10", "healing off: injury 70"],
                    num=("on_10", "on_70", "off_10", "off_70"), raw=("on_10", "on_70", "off_10", "off_70"), min_width=760)


def logit(pct):
    q = np.clip(np.asarray(pct, float) / 100.0, 0.005, 0.995)
    return np.log(q / (1 - q))


def rabbit_logodds(lf, inj):
    """Rabbit effect on the log-odds scale, per checkpoint: logit(bush dwell with rabbit) - logit(no animal).
    Bush dwell is a per-checkpoint mean over 30 episodes, clipped to 0.5-99.5 % before the transform."""
    r, n = LF.ser(lf, "rabbitwander", inj), LF.ser(lf, "none", inj)
    return pd.Series(logit(r) - logit(n), index=r.index).dropna()


def cell_plain(v, fmt="{:+.2f}"):
    m, lo, hi = LF.prof(v)
    t = lambda x: FB.num_text(fmt.format(x))
    txt = f"<span class=\"nw\">{t(m)}</span><br><span class=\"ci nw\">[{t(lo)}, {t(hi)}]</span>"
    return f"<strong>{txt}</strong>" if (lo > 0 or hi < 0) else txt


def logodds_table():
    """Healing off. The rabbit-alone gap at injury 0 (pp) and the rabbit's effect in log-odds at injury 0 and 10."""
    rows = []
    for g in GROUPS:
        for a, s in LF.runs(g):
            lf = LF.leaf(g, "off", a, s)
            r = {"group": LF.GROUP_NAME[g].replace(" agents", ""), "agent": f"{a}, seed {s}",
                 "alone": cell(LF.extra_series(lf, "00").dropna()),
                 "lo0": cell_plain(rabbit_logodds(lf, "00")), "lo10": cell_plain(rabbit_logodds(lf, "10")),
                 "dlo": cell_plain((rabbit_logodds(lf, "10") - rabbit_logodds(lf, "00")).dropna())}
            rows.append(r)
    D = pd.DataFrame(rows)
    return FB.table(D, ["group", "agent", "alone", "lo0", "lo10", "dlo"],
                    ["agents", "agent, seed", "rabbit alone, unhurt (pp)", "rabbit effect, log-odds: injury 0",
                     "rabbit effect, log-odds: injury 10", "change, injury 10 minus 0"],
                    num=("alone", "lo0", "lo10", "dlo"), raw=("alone", "lo0", "lo10", "dlo"), min_width=760)


def main():
    page = open(os.path.join(PAGE_DIR, "page_template.html")).read()
    tok = {"{{TABLE:contrast}}": contrast_table(), "{{TABLE:logodds}}": logodds_table()}
    curves_axes = ("Horizontal: starting injury of the test, 0 (unhurt) to 90 in steps of 10. Vertical: bush dwell, the "
                   "share of the test's 100 steps spent on the bush (%), 0&ndash;100 in every panel. Left column: the "
                   "test world with bush healing as in training; right column: the same scenes with healing switched off, "
                   "so the starting injury lasts the whole test. Grey open circles: no animal; orange squares: a harmless "
                   "wandering rabbit. Each point is the mean over the checkpoints from 2 to 10 M training steps; dashed "
                   "edges and shading: 95 % interval. One row per agent. The extra-hiding and training figures below share one "
                   "vertical range across the three agent groups.")
    extra_axes = ("Horizontal: starting injury of the test, 0 to 90. Vertical: the rabbit's extra bush dwell &mdash; bush "
                  "dwell with the wandering rabbit minus bush dwell with no animal, in percentage points (pp), mean over "
                  "the checkpoints from 2 to 10 M training steps, with a 95 % interval (dashed edges, shading). Green open "
                  "triangles: healing on; blue diamonds: healing off. The dotted line in each colour marks that curve's value "
                  "for an unhurt agent; a curve rising above its dotted line means injury makes the rabbit matter more.")
    train_axes = ("Horizontal: training, in million steps (0&ndash;10); the shaded first 2 M steps are left out of every "
                  "average on this page. Vertical: the injury-10 contrast in percentage points &mdash; the rabbit's extra "
                  "bush dwell at starting injury 10 minus the same at injury 0. Above zero: injury makes the rabbit matter "
                  "more. Green: healing on; blue: healing off. Thin lines: single checkpoints; thick lines: the average of 5 "
                  "neighbouring checkpoints.")
    n = 1
    for kind, axes, shows, alt in (
            ("curves", curves_axes, "Whether hiding rises with injury, how far it rises with and without healing, and "
             "whether the rabbit line separates from the no-animal line more at some injuries than when unhurt.",
             "Panels of bush dwell against starting injury, healing on and off, no animal and rabbit"),
            ("extra", extra_axes, "At which injuries, if any, the rabbit adds more hiding than it adds to an unhurt agent.",
             "Panels of the rabbit's extra bush dwell against starting injury, healing on and off"),
            ("train", train_axes, "Whether the injury-10 contrast is steady across training or rises and falls.",
             "Panels of the injury-10 contrast across training, healing on and off")):
        for g in GROUPS:
            tok[f"{{{{FIG:{kind}_{g}}}}}"] = FB.figure(
                f"lk_{kind}__{g}", alt + f", {LF.GROUP_NAME[g]}.", axes, shows,
                f"{FIG} --figure {kind} --group {g}", title=f"Figure {n} &mdash; {LF.GROUP_NAME[g]}")
            n += 1
    tok["{{BUILT}}"] = datetime.date.today().isoformat()
    house = open(BB.HOUSE).read()
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    vm = re.search(r'(<div class="lb fit" id="lb".*?\n</div>)', house, re.S)
    vs = re.search(r"(\(function \(\) \{\s*// full-size figure viewer.*?\}\)\(\);)", house, re.S)
    sc = re.search(r"(function updateCues\(\).*?)</script>", house, re.S)
    tok["{{HOUSE_STYLE}}"] = m.group(1)
    tok["{{LIGHTBOX}}"] = vm.group(1) + "\n<script>\n" + vs.group(1) + "\n" + sc.group(1) + "</script>"
    note = os.path.join(PAGE_DIR, "summary_note.html")
    tok["{{SUMMARY}}"] = open(note).read()
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
    out = os.path.join(PAGE_DIR, "lookalike_pilot.html")
    open(out, "w").write(page)
    print(f"wrote {out}: {len(page.encode()):,} bytes")


if __name__ == "__main__":
    main()
