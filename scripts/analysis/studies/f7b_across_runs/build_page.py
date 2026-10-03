#!/usr/bin/env python3
"""build_page.py - assemble the "Injury and Rabbit Avoidance Across Runs" page.

Fills docs/experiments/active/hypervigilance/f7b_across_runs/page_template.html with the house style,
the figures (embedded, each with the data statement its script emitted), the tables and the headline
numbers -- every number on the page is computed here from collect.py's tables, none typed by hand.
Reuses the Basic Behaviour builder's helpers (embedding, data tables, width floor) by import.

    $P scripts/analysis/studies/f7b_across_runs/build_page.py --data results/analysis/f7b_across_runs
"""
import argparse
import base64
import datetime
import html
import json
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "basic_behaviour"))
import importlib.util  # noqa: E402
# the Basic Behaviour builder shares this file's name, so it is loaded by path (helpers only)
_spec = importlib.util.spec_from_file_location(
    "bb_build_page", os.path.join(ROOT, "scripts", "analysis", "basic_behaviour", "build_page.py"))
BB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BB)
sys.path.insert(0, HERE)
import figures as FX      # noqa: E402

PAGE_DIR = os.path.join(ROOT, "docs/experiments/active/hypervigilance/f7b_across_runs")
FIG_DIR = os.path.join(PAGE_DIR, "figures")
LEVEL_GROUPS = ["smell", "body", "thirst", "core", "thermal", "injgrid", "july"]
LEVEL_CAP = {
    "smell": "Smell study, level 05: three smell worlds × two agents × three seeds, tested in scenes built on each smell world.",
    "body": "Body rules, level 05: fifteen worlds × two agents, one seed each. Rules on: H hunger slows healing, C healing costs food, W warmth costs food, F scarcer food.",
    "thirst": "Thirst task: nine worlds (map 10, 15 or 20 squares; smell across the map, or range 5 or 3) × two agents, one seed each.",
    "core": "Curriculum waves 1 and 2 and blocking-bush training, tested in the core scene set (bush blocks animals, no campfire).",
    "thermal": "Blocking-bush training, levels 05 and 06, tested in eight temperature variants of the core scenes (cool or neutral ambient, fire by the bush or away, with or without sensor noise matched to training).",
    "injgrid": "Blocking-bush training, tested in the injury-grid scene set (no chasing rabbit). Only injuries 0 and 70 are shown.",
    "july": "July runs (levels 03 and 04: network sizes, level-04 variants, GAE return, an early modulator design), tested in the July scene set in which animals could enter the bush.",
}


def num_text(v):
    """Signed numbers with a true minus sign; -0.0 shown as 0.0."""
    t = str(v)
    if re.fullmatch(r"-0(\.0+)?", t):
        t = t[1:]
    return re.sub(r"(?<![\w.])-(?=\d)", "\u2212", t)


def table(df, cols, heads, num=(), nowrap=(), min_width=720):
    out = ['<p class="cue" hidden>&larr; wider than the screen &mdash; scroll it sideways</p>'
           f'<div class="scroll"><table class="wide" style="min-width:{min_width}px"><thead><tr>']
    cls = lambda c: ' class="n"' if c in num else ""
    out += [f"<th{cls(c)}>{h}</th>" for c, h in zip(cols, heads)]
    out.append("</tr></thead><tbody>")
    for _, r in df.iterrows():
        cell = lambda c: (f'<td class="nw">{html.escape(num_text(r[c]))}</td>' if c in nowrap else
                          f"<td{cls(c)}>{BB.wrap_cell(num_text(r[c]) if c in num else r[c])}</td>")
        out.append("<tr>" + "".join(cell(c) for c in cols) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def fmt(x):
    return f"{x:+.1f}".replace("-", "&minus;")


CUE = ('<p class="cue" hidden>&larr; the figure is wider than the screen &mdash; scroll it sideways, '
       'or tap it to open it full size</p>')


def img_tag(stem):
    """The embedded figure with its width floor AND the scroll wrapper + cue that make the floor safe
    on a phone (register F79: emit the two together)."""
    png = os.path.join(FIG_DIR, f"{stem}.png")
    return (f'{CUE}<div class="scroll"><img data-fig="{stem}" style="min-width:{BB.width_floor(png)}px" '
            f'src="data:image/png;base64,{BB.embed_png(png)}"')


def figure(stem, alt, axes, shows, prov):
    rows = json.load(open(os.path.join(FIG_DIR, f"{stem}.samples.json")))
    png = os.path.join(FIG_DIR, f"{stem}.png")
    return (f'<figure>{img_tag(stem)} alt="{html.escape(alt)}"></div>'
            '<p class="zoomhint">Click the figure to view it full size</p><figcaption>'
            f'<span><b>Axes.</b> {axes}</span><span><b>What it shows.</b> {shows}</span>'
            f'<span>{BB.data_table(stem, rows)}</span></figcaption>'
            f'<p class="prov">Reproduce: <code>{prov}</code></p></figure>')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args(argv)
    R, L, E, X = FX.load(a.data)
    page = open(os.path.join(PAGE_DIR, "page_template.html")).read()

    # ---- numbers
    def eff(q, ids=None, interp=True):
        e = E[E.scene == q]
        if ids is not None:
            e = e[e.id.isin(ids)]
        if interp:
            e = e[~e.id.isin(FX.flagged(L, q))]
        return e
    new_ids = R[R.scene_set.isin(["core", "thermal", "injgrid", "world"])].id
    world = R[R.scene_set == "world"].id
    body = R[R.family == "Body rules (level 05)"]
    hc_on = body[body.setting.str[2] == "1"].id
    hc_off = body[body.setting.str[2] == "0"].id
    w1 = R[(R.family == "Curriculum wave 1") & (R.setting == "level 03")].id
    ch = eff("rabbit-minus-none", interp=True)
    lvl = L.merge(R[["id"]], on="id")
    hc_surv = lvl[lvl.id.isin(hc_on) & (lvl.injury == "70") & (lvl.scene == "rabbit")].survival_mean
    fam_mean = lambda f: eff("rabbit-minus-none", R[R.family == f].id, interp=False)["mean"].mean()
    tok = {
        "{{N_SEL}}": str(len(R)), "{{N_DROP}}": str(len(X)), "{{N_UNIQUE}}": str(R.run_dir.nunique()),
        "{{N_FAMILIES}}": str(R.family.nunique()), "{{N_NEW}}": str(int((R.family == "Body rules (level 05)").sum())),
        "{{NONE_NEW}}": f"{eff('none', new_ids)['mean'].median():.0f}",
        "{{WANDER_MINUS}}": fmt(eff("rabbitwander-minus-none")["mean"].median()),
        "{{N_WANDER}}": str(len(eff("rabbitwander-minus-none"))),
        "{{CHASE_MIN}}": fmt(ch["mean"].min()), "{{CHASE_MAX}}": fmt(ch["mean"].max()),
        "{{W1_L03}}": " and ".join(fmt(v) for v in eff("rabbit-minus-none", w1, interp=False).set_index("id").loc[list(w1)]["mean"]),
        "{{W1_NONE}}": " and ".join(fmt(v) for v in eff("none", w1, interp=False).set_index("id").loc[list(w1)]["mean"]),
        "{{W1_RAW}}": " and ".join(fmt(v) for v in eff("rabbit", w1, interp=False).set_index("id").loc[list(w1)]["mean"]),
        "{{SMELL_MINUS}}": fmt(fam_mean("Smell study (level 05)")),
        "{{THIRST_MINUS}}": fmt(fam_mean("Thirst task")),
        "{{THERMAL_MINUS}}": fmt(eff("rabbit-minus-none", R[R.scene_set == "thermal"].id, interp=False)["mean"].mean()),
        "{{HC_ON}}": fmt(eff("rabbit-minus-none", hc_on, interp=False)["mean"].mean()),
        "{{HC_OFF}}": fmt(eff("rabbit-minus-none", hc_off, interp=False)["mean"].mean()),
        "{{HC_SURV}}": f"{hc_surv.min():.0f}&ndash;{hc_surv.max():.0f}",
        "{{BUILT}}": datetime.date.today().isoformat(),
    }

    # ---- tables
    ss = pd.DataFrame([{"set": FX.SET_TAG[k], "what": FX.SET_SHORT[k].split(" (")[1].rstrip(")") if "(" in FX.SET_SHORT[k] else "",
                        "rows": int((R.scene_set == k).sum())} for k in FX.SET_ORDER])
    ss["what"] = [{"july": "July 2026 runs; animals could walk into the bush; no temperature system",
                   "core": "bush hides the agent and blocks animals; no campfire",
                   "thermal": "core scenes in a level-05/06 body, with one of eight fire and ambient-temperature variants",
                   "injgrid": "only three scenes (no animal, hunting predator, wandering rabbit) at ten injury levels",
                   "world": "scenes rebuilt on the agent's own training world, with a campfire beside the bush"}[k]
                  for k in FX.SET_ORDER]
    tok["{{TABLE:scene_sets}}"] = table(ss, ["set", "what", "rows"], ["scene set", "what differs", "rows"], num=("rows",))
    g = []
    for f in FX.FAMILY_ORDER:
        for s in FX.SET_ORDER:
            ids = R[(R.family == f) & (R.scene_set == s)].id
            if not len(ids):
                continue
            row = {"group": f, "set": FX.SET_TAG[s], "n": len(ids)}
            for q, k in (("none", "none"), ("rabbit", "chase"), ("rabbit-minus-none", "chase_x"),
                         ("rabbitwander", "wand"), ("rabbitwander-minus-none", "wand_x")):
                e = eff(q, ids, interp=False)
                row[k] = f"{e['mean'].mean():+.1f}" if len(e) else "n/a"
            row["hollow"] = int(ids.isin(FX.flagged(L, "rabbit-minus-none") | FX.flagged(L, "rabbitwander-minus-none")).sum())
            g.append(row)
    tok["{{TABLE:groups}}"] = ("<p>Mean over the rows of each group, in percentage points of bush dwell, injury 70 minus "
                               "injury 0. &ldquo;Extra&rdquo; is the scene's injury effect minus the no-animal scene's. "
                               "Hollow values are included in these means; the last column counts them.</p>" +
                               table(pd.DataFrame(g), ["group", "set", "n", "none", "chase", "chase_x", "wand", "wand_x", "hollow"],
                                     ["group", "scene set", "rows", "no animal", "chasing rabbit", "chasing, extra",
                                      "wandering rabbit", "wandering, extra", "hollow rows"],
                                     num=("n", "none", "chase", "chase_x", "wand", "wand_x", "hollow")))
    e = E[E.scene == "rabbit-minus-none"].merge(R, on="id")
    fl = FX.flagged(L, "rabbit-minus-none")
    e["row"] = [FX.row_label(r) for _, r in e.iterrows()]
    e["value"] = e["mean"].map(lambda v: f"{v:+.1f}")
    e["ci"] = [f"{lo:+.1f} to {hi:+.1f}" for lo, hi in zip(e.lo, e.hi)]
    e["note"] = ["died early (hollow)" if i in fl else "" for i in e.id]
    e["set"] = e.scene_set.map(FX.SET_TAG)
    ex = pd.concat([e.nlargest(6, "mean"), e.nsmallest(6, "mean")])
    tok["{{TABLE:extremes}}"] = table(ex, ["family", "set", "row", "value", "ci", "note"],
                                      ["group", "scene set", "run", "extra effect (pp)", "95% interval", "note"],
                                      num=("value",), nowrap=("ci",), min_width=820)
    fams = R.groupby(["family", "scene_set"]).agg(rows=("id", "size"), runs=("run_dir", "nunique"),
                                                   ckpts=("n_ckpt", "median")).reset_index()
    fams["set"] = fams.scene_set.map(FX.SET_TAG)
    fams["ckpts"] = fams.ckpts.map(lambda v: f"{v:.0f}")
    tok["{{TABLE:families}}"] = table(fams, ["family", "set", "rows", "runs", "ckpts"],
                                      ["group", "scene set", "rows", "distinct runs", "checkpoints tested (median)"],
                                      num=("rows", "runs", "ckpts"))
    X2 = X.copy()
    X2["reason"] = X2.reason.str.replace("no experiment-test results on disk",
                                         "no experiment-test results; its pair is the smell study's control seed 42, already included",
                                         regex=False)
    tok["{{TABLE:dropped}}"] = table(X2, ["family", "id", "reason"], ["group", "sweep / run", "reason"], nowrap=("id",),
                                     min_width=860)
    R2 = R.copy()
    R2["set"] = R2.scene_set.map(FX.SET_TAG)
    R2["run"] = R2.run_dir.map(os.path.basename)
    tok["{{TABLE:runs}}"] = table(R2, ["family", "set", "setting", "agent", "run", "n_ckpt"],
                                  ["group", "scene set", "setting", "agent", "training run", "checkpoints"], num=("n_ckpt",),
                                  nowrap=("run",), min_width=1100)

    # ---- figures
    for stem in ("f7b_rank", "f7b_family", "f7b_within"):
        rows = json.load(open(os.path.join(FIG_DIR, f"{stem}.samples.json")))
        png = os.path.join(FIG_DIR, f"{stem}.png")
        tag = re.search(rf'<img data-fig="{stem}"[^>]*>', page).group(0)
        page = page.replace(tag, tag.replace(f'<img data-fig="{stem}"', img_tag(stem)) + "</div>")
        page = page.replace(f"{{{{DATA:{stem}}}}}", BB.data_table(stem, rows)).replace("<b>Data.</b> <details", "<details")
    f4 = []
    for k, gname in enumerate(LEVEL_GROUPS):
        stem = f"f7b_levels__{gname}"
        title = FX.GROUPS[gname][0]
        f4.append(f'<h4 class="fh"><span class="n">Figure 4{"abcdefg"[k]}</span>{html.escape(title)}</h4>')
        f4.append(figure(stem, f"Bush dwell per scene for each run of the group {title}, at injury 0 and 70.",
                         "Horizontal, in each panel: bush dwell over the newest 20 checkpoints, the share of the "
                         "scene's 100 steps spent on the bush (%, 0&ndash;100). Vertical: one row per run (setting "
                         "&middot; agent; no unit). One panel per scene. Hollow grey ring = start injury 0, filled dark marker = "
                         "start injury 70; circle = ordinary agent, triangle = modulated agent; * = died early in a "
                         "predator-free scene.",
                         html.escape(LEVEL_CAP[gname]),
                         f"scripts/analysis/studies/f7b_across_runs/figures.py --figure levels --group {gname}"))
    tok["{{FIG4}}"] = "\n".join(f4)

    # ---- house style
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
    # keep command-line flags whole when a Reproduce chip wraps (register F49)
    page = re.sub(r'<p class="prov">.*?</p>', lambda m: m.group(0).replace("--", "&#8209;&#8209;"), page, flags=re.S)
    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        raise SystemExit(f"unsubstituted tokens: {sorted(set(left))}")
    if len(page.encode()) > BB.PAGE_MAX_BYTES:
        raise SystemExit(f"page {len(page.encode()):,} bytes is over the limit")
    out = os.path.join(PAGE_DIR, "f7b_across_runs.html")
    open(out, "w").write(page)
    print(f"wrote {out}: {len(page.encode()):,} bytes")
    for k in ("{{W1_NONE}}", "{{W1_RAW}}", "{{NONE_NEW}}", "{{WANDER_MINUS}}", "{{CHASE_MIN}}", "{{CHASE_MAX}}", "{{W1_L03}}", "{{SMELL_MINUS}}",
              "{{THIRST_MINUS}}", "{{THERMAL_MINUS}}", "{{HC_ON}}", "{{HC_OFF}}", "{{HC_SURV}}"):
        print(f"  {k} = {tok[k]}")


if __name__ == "__main__":
    main()
