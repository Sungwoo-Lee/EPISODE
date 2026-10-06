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
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "basic_behaviour"))
import importlib.util  # noqa: E402
# the Basic Behaviour builder shares this file's name, so it is loaded by path (helpers only)
_spec = importlib.util.spec_from_file_location(
    "bb_build_page", os.path.join(ROOT, "scripts", "analysis", "basic_behaviour", "build_page.py"))
BB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BB)
sys.path.insert(0, HERE)
import figures as FX      # noqa: E402
import highlight as HL    # noqa: E402

PAGE_DIR = os.path.join(ROOT, "docs/experiments/active/hypervigilance/f7b_across_runs")
FIG_DIR = os.path.join(PAGE_DIR, "figures")
LEVEL_GROUPS = ["smell", "body", "thirst", "core", "thermal", "injgrid", "core_old", "refuge", "july", "dreamer", "ladder"]
PLAIN = {   # group -> what the agents were trained in, in plain words
    "July curriculum": "The first full ladder: one agent per level 00 to 05 as the levels were defined in early "
                       "July, levels 03 to 05 trained on to 100 million steps. Its level 05 was noise on the senses.",
    "July re-train, corrected smell fall-off": "Levels 01 to 04 retrained in late July after a fix to how fast a "
                                               "smell fades with distance; ordinary and early modulated agents.",
    "Dreamer agents": "A different learning method (Dreamer), which learns a model of the world and plans inside "
                      "it, on July levels 02 to 04 in many sizes and settings.",
    "Bush-refuge training": "Levels 01 to 04 retrained in August with a bush that animals cannot enter, so the bush "
                            "becomes a real refuge.",
    "Rest premium": "Level 04 with the refuge bush, where injury heals faster the longer the agent rests without "
                    "interruption; ten settings of how big that reward for resting is.",
    "Rest premium, no ambush predators": "The same ten rest-premium settings with the hidden ambush predators "
                                         "removed, to test whether moving around was what made resting risky.",
    "July network size": "July runs of curriculum levels 03 and 04, as those levels were defined in July (not the "
                         "table above), each with a "
                         "smaller or larger network inside the agent.",
    "July level-04 variants": "July runs of level 04, each with one or two rules changed: slower movement, a shorter "
                              "predator jump, less damage, slower or faster animals, or combinations.",
    "July GAE return": "July runs of levels 03 and 04 that learn with a different way of estimating how good the "
                       "future will be (called GAE in the literature).",
    "July early modulator": "July runs of levels 03 and 04 with the first version of the modulated agent.",
    "Curriculum wave 1": "The first September run of curriculum levels 02, 03 and 04. Level 02: a predator and a "
                         "harmless rabbit. Level 03: adds random starting hunger and injury and a random number of "
                         "animals. Level 04: adds a predator that can jump at the agent.",
    "Fast bush healing (22 Sep)": "The same levels retrained a day later (levels 02 to 06) with new body rules: injury "
                              "heals 25 times faster while the agent sits on a bush, and the body stores twice as much "
                              "food. Their level 06 is today's level 07 (noise on the senses); the pond level was added later.",
    "Smell study (level 05)": "Level 05 (cold world with campfires) in three versions that differ only in how the "
                              "predator and the rabbit smell: two different smells, one smell differing only in "
                              "strength, or the same mixture of both. Three seeds each.",
    "Body rules (level 05)": "Level 05 with up to four extra body rules switched on: hunger slows healing; healing "
                             "uses up food; staying warm uses up food; less food in the world.",
    "Thirst task": "Level 06 (level 05 plus a pond and thirst), on maps of 10, 15 or 20 squares, with smells "
                   "that carry across the whole map or only 5 or 3 squares.",
}
LEVEL_CAP = {
    "smell": "Smell study, level 05: three smell worlds × two agents × three seeds, tested in scenes built on each smell world. Tested in the study's own scenes (cold air, campfire beside the bush), not the neutral re-test used in Figures B1&ndash;B8.",
    "body": "Body rules, level 05: fifteen worlds × two agents, one seed each. Rules on: H hunger slows healing, C healing costs food, W warmth costs food, F scarcer food. Tested in the study's own scenes (cold air, campfire beside the bush), not the neutral re-test used in Figures B1&ndash;B8.",
    "thirst": "Thirst task: nine worlds (map 10, 15 or 20 squares; smell across the map, or range 5 or 3) × two agents, one seed each. Tested in the study's own scenes (cold air, campfire beside the bush), not the neutral re-test used in Figures B1&ndash;B8.",
    "core": "Fast bush healing (22 Sep), level 04, tested in the core scene set (bush blocks animals, no campfire).",
    "core_old": "Curriculum wave 1, levels 02-04, tested in the core scene set before the 2026-09-23 fix, so animals could walk into the test bush.",
    "refuge": "August bush-refuge and rest-premium runs, tested in scenes whose bush blocks animals, matching their training.",
    "dreamer": "Dreamer agents (a different learning method), tested in the July scene set.",
    "ladder": "The July curriculum runs, one per level; the level-05 (noise) run is tested with noisy senses.",
    "thermal": "Fast bush healing (22 Sep), levels 05 and 06, tested in eight temperature variants of the core scenes (cool or neutral ambient, fire by the bush or away, with or without sensor noise matched to training).",
    "injgrid": "Fast bush healing (22 Sep), tested in the injury-grid scene set (no chasing rabbit). Only injuries 0 and 70 are shown.",
    "july": "July runs (levels 03 and 04: network sizes, level-04 variants, GAE return, an early modulator design), tested in the July scene set in which animals could enter the bush.",
}


def num_text(v):
    """Signed numbers with a true minus sign; -0.0 shown as 0.0."""
    t = str(v)
    if re.fullmatch(r"-0(\.0+)?", t):
        t = t[1:]
    return re.sub(r"(?<![\w.])-(?=\d)", "\u2212", t)


LEVEL_FILES = "configs/environment/experiment/basic/0[0-7]-*.yaml"


def level_table():
    """On/off table of the training curriculum, read from the level configs themselves (extends resolved)."""
    import glob as G
    sys.path.insert(0, ROOT)
    from src.environment.config_loader import load_env_config
    feats = [
        ("map size (squares)", lambda c, e, b, P, Rb: f"{e['height']}&times;{e['width']}"),
        ("hidden ambush predators (fixed squares that bite)",
         lambda c, e, b, P, Rb: any(r.get("type") == "hiding_predator" for r in e.get("resources", []))),
        ("hunting predator that chases the agent", lambda c, e, b, P, Rb: bool(P)),
        ("&hellip; moving at full speed (not every third step)",
         lambda c, e, b, P, Rb: bool(P) and all(np.max(np.atleast_1d(p.get("move_interval", 1))) == 1 for p in P)),
        ("&hellip; able to jump at the agent from 2&ndash;3 squares",
         lambda c, e, b, P, Rb: any(np.max(np.atleast_1d(p.get("attack_range", 0))) > 1 for p in P)),
        ("harmless rabbit", lambda c, e, b, P, Rb: bool(Rb)),
        ("bush to hide in", lambda c, e, b, P, Rb: any(o.get("name") == "bush" for o in e.get("obstacles", []) or [])),
        ("random starting hunger and injury", lambda c, e, b, P, Rb: bool(b.get("random_start_injury"))),
        ("random number of animals each episode",
         lambda c, e, b, P, Rb: any(x.get("count_high") is not None for x in P + Rb)),
        ("cold, with campfires to stay warm", lambda c, e, b, P, Rb: bool(c["thermal"]["enabled"])),
        ("pond and thirst", lambda c, e, b, P, Rb: bool(c["water"]["enabled"])),
        ("noise on the senses", lambda c, e, b, P, Rb: bool(c["perceptual_noise"]["enabled"])),
        ("injury heals 25&times; faster on a bush",
         lambda c, e, b, P, Rb: float(b.get("recovery_in_bush_multiplier", 1)) >= 25),
    ]
    files = sorted(G.glob(os.path.join(ROOT, LEVEL_FILES)))
    if len(files) != 8:
        raise SystemExit(f"expected 8 curriculum levels, found {len(files)}")
    cols = []
    for f in files:
        c = load_env_config(f).to_dict()
        e, b = c["environment"], c["body"]
        ents = e.get("entities", []) or []
        P = [x for x in ents if x.get("class") == "predator"]
        Rb = [x for x in ents if x.get("class") == "neutral"]
        cols.append([fn(c, e, b, P, Rb) for _, fn in feats])
    head = "".join(f'<th class="n">{os.path.basename(f)[:2]}</th>' for f in files)
    rows = []
    for i, (name, _) in enumerate(feats):
        cells = "".join(
            f'<td class="n">{v}</td>' if isinstance(v, str) else
            (f'<td class="n"><b>on</b></td>' if v else '<td class="n" style="color:var(--ink-3)">&ndash;</td>')
            for v in (col[i] for col in cols))
        rows.append(f"<tr><td>{name}</td>{cells}</tr>")
    return ('<p class="cue" hidden>&larr; wider than the screen &mdash; scroll it sideways</p><div class="scroll">'
            '<table class="wide" style="min-width:720px"><thead><tr><th>level</th>' + head + "</tr></thead><tbody>"
            + "".join(rows) + "</tbody></table></div>")


AVOID = os.path.join(ROOT, "results/eval/avoidance")


def late_diff(leaf, plus, minus):
    """Newest-20-checkpoint mean of (bush dwell in condition `plus` minus `minus`), formed per checkpoint, in pp."""
    import probes as PR
    def ser(c):
        d = pd.read_csv(os.path.join(AVOID, leaf, f"avoid_{c}.csv"))
        col = "bush_hiding" if "bush_hiding" in d.columns else "bush_dwell"
        return d[["step", col]].rename(columns={col: c})
    m = ser(plus).merge(ser(minus), on="step").sort_values("step")
    v = PR.summarise(((m[plus] - m[minus]) * 100.0).to_numpy())
    return v["mean"]


def bush_tables():
    """Three comparisons for 'Did the blocking bush matter?'."""
    meas = [("animal dep., predator", "pred_inj00", "none_inj00"),
            ("animal dep., chasing rabbit", "rabbit_inj00", "none_inj00"),
            ("state dep.", "none_inj70", "none_inj00")]
    rows = []
    for agent, lab in (("lvl04_control", "ordinary"), ("lvl04_modulated", "modulated")):
        r = {"agent": lab}
        for name, a, b in meas:
            v0 = late_diff(f"metrics_history_rppo_basicq2_wave2/{agent}", a, b)
            v1 = late_diff(f"metrics_history_rppo_basicq2_wave2_blocking_bush/{agent}", a, b)
            r[name] = f"{v0:+.1f} \u2192 {v1:+.1f}"
        rows.append(r)
    t1 = table(pd.DataFrame(rows), ["agent"] + [m[0] for m in meas],
               ["level-04 agent (22 Sep)"] + [m[0] + ": test bush lets animals in \u2192 blocks them" for m in meas],
               nowrap=tuple(m[0] for m in meas), min_width=820)
    rows = []
    for lvl, a, b in (("01", "dp1/rppo/b01_mc", "bushrefuge/rppo/b01_slowpred_5x5"),
                      ("02", "dp1/rppo/b02_mc", "bushrefuge/rppo/b02_predrabbit_10x10"),
                      ("03", "dp1/rppo/b03_mc", "bushrefuge/rppo/b03_randinit_10x10"),
                      ("04", "dp1/rppo/b04_mc", "bushrefuge/rppo/b04_jump_10x10")):
        r = {"level": lvl}
        for name, x, y in meas:
            r[name] = f"{late_diff(a, x, y):+.1f} \u2192 {late_diff(b, x, y):+.1f}"
        rows.append(r)
    t2 = table(pd.DataFrame(rows), ["level"] + [m[0] for m in meas],
               ["level (ordinary agent)"] + [m[0] + ": July re-train \u2192 August bush refuge" for m in meas],
               nowrap=tuple(m[0] for m in meas), min_width=820)
    rows = []
    for lvl in ("02", "03", "04"):
        for agent, lab in (("control", "ordinary"), ("modulated", "modulated")):
            r = {"run": f"level {lvl} \u00b7 {lab}"}
            for name, x, y in (meas[0], meas[2]):
                v0 = late_diff(f"metrics_history_rppo_basicq2_wave1/lvl{lvl}_{agent}", x, y)
                v1 = late_diff(f"metrics_history_rppo_injurygrid_core/lvl{lvl}_{agent}", x, y)
                r[name] = f"{v0:+.1f} \u2192 {v1:+.1f}"
            rows.append(r)
    t3 = table(pd.DataFrame(rows), ["run", meas[0][0], meas[2][0]],
               ["run", meas[0][0] + ": wave 1 (21 Sep) \u2192 fast bush healing (22 Sep)",
                meas[2][0] + ": wave 1 \u2192 fast bush healing"], nowrap=(meas[0][0], meas[2][0]), min_width=760)
    return t1, t2, t3


def table(df, cols, heads, num=(), nowrap=(), min_width=720):
    out = ['<p class="cue" hidden>&larr; wider than the screen &mdash; scroll it sideways</p>'
           f'<div class="scroll"><table class="wide" style="min-width:{min_width}px"><thead><tr>']
    cls = lambda c: ' class="n"' if c in num else ""
    out += [f"<th{cls(c)}>{h}</th>" for c, h in zip(cols, heads)]
    out.append("</tr></thead><tbody>")
    for _, r in df.iterrows():
        cell = lambda c: (f'<td class="n nw">{html.escape(num_text(r[c]))}</td>' if c in nowrap and c not in ("id", "run", "when") else
                          f'<td class="nw">{html.escape(num_text(r[c]))}</td>' if c in nowrap else
                          f"<td{cls(c)}>{BB.wrap_cell(num_text(r[c]) if c in num else r[c])}</td>")
        out.append("<tr>" + "".join(cell(c) for c in cols) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def fmt(x):
    t = f"{x:+.1f}"
    return "0.0" if t in ("+0.0", "-0.0") else t.replace("-", "&minus;")


CUE = ('<p class="cue" hidden>&larr; the figure is wider than the screen &mdash; scroll it sideways, '
       'or tap it to open it full size</p>')


def img_tag(stem):
    """The embedded figure with its width floor AND the scroll wrapper + cue that make the floor safe
    on a phone (register F79: emit the two together)."""
    png = os.path.join(FIG_DIR, f"{stem}.png")
    return (f'{CUE}<div class="scroll"><img data-fig="{stem}" style="min-width:{BB.width_floor(png)}px" '
            f'src="data:image/png;base64,{BB.embed_png(png)}"')


def figure(stem, alt, axes, shows, prov, title=""):
    rows = json.load(open(os.path.join(FIG_DIR, f"{stem}.samples.json")))
    png = os.path.join(FIG_DIR, f"{stem}.png")
    return (f'<figure>{img_tag(stem)} alt="{html.escape(alt)}"></div>'
            '<p class="zoomhint">Click the figure to view it full size</p><figcaption>'
            + (f'<span><b>{title}.</b></span>' if title else "") +
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
        "{{NONE_NEW}}": f"{eff('none', R[R.bush_heal == '25x'].id)['mean'].median():.0f}",
        "{{NONE_SLOW}}": fmt(eff("none", R[R.bush_heal == "1x"].id)["mean"].median()),
        "{{N_FAST}}": str(R[R.bush_heal == "25x"].run_dir.nunique()),
        "{{ANIM_SLOW_MED}}": f"{eff('rabbit-vs-none@00', R[(R.bush_heal == '1x') & (R.agent != 'Dreamer')].id, interp=False)['mean'].median():.0f}",
        "{{ANIM_SLOW_MAX}}": f"{eff('rabbit-vs-none@00', R[(R.bush_heal == '1x') & (R.agent != 'Dreamer')].id, interp=False)['mean'].max():.0f}",
        "{{N_DREAMER}}": str(int((R.agent == 'Dreamer').sum())),
        "{{ANIM_FAST_MED}}": f"{eff('rabbit-vs-none@00', R[R.bush_heal == '25x'].id, interp=False)['mean'].median():.0f}",
        "{{ANIM_FAST_MAX}}": f"{eff('rabbit-vs-none@00', R[R.bush_heal == '25x'].id, interp=False)['mean'].max():.0f}",
        "{{WAND_OLD}}": f"{eff('rabbitwander-vs-none@00', R[(R.bush_heal == '1x') & (R.agent != 'Dreamer')].id, interp=False)['mean'].median():.1f}",
        "{{WAND_NEW}}": f"{eff('rabbitwander-vs-none@00', R[R.bush_heal == '25x'].id, interp=False)['mean'].median():.1f}",
        "{{N00_OLD}}": f"{lvl[lvl.id.isin(R[(R.bush_heal == '1x') & (R.agent != 'Dreamer')].id) & (lvl.scene == 'none') & (lvl.injury == '00')]['mean'].median():.1f}",
        "{{N00_NEW}}": f"{lvl[lvl.id.isin(R[R.bush_heal == '25x'].id) & (lvl.scene == 'none') & (lvl.injury == '00')]['mean'].median():.1f}",
        "{{ANIM_WANDER_MED}}": f"{eff('rabbitwander-vs-none@00', R.id, interp=False)['mean'].median():.0f}",
        "{{ANIM_WANDER_P90}}": f"{eff('rabbitwander-vs-none@00', R.id, interp=False)['mean'].quantile(0.9):.0f}",
        "{{N_WANDER_ALL}}": str(len(eff('rabbitwander-vs-none@00', R.id, interp=False))),
        "{{N_SETS}}": ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"][R.scene_set.nunique()],
        "{{N_SLOW}}": str(R[R.bush_heal == "1x"].run_dir.nunique()),
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
    tok["{{TABLE:levels}}"] = level_table()
    tok["{{TABLE:bush_test}}"], tok["{{TABLE:bush_train}}"], tok["{{TABLE:bush_heal}}"] = bush_tables()
    pl = []
    R["start"] = R.run_dir.map(FX.start_date)
    for f in sorted(R.family.unique(), key=lambda f: R[R.family == f].start.min()):
        g = R[R.family == f]
        d0, d1 = g.start.min(), g.start.max()
        when = d0.strftime("%-d %b %Y") if d0 == d1 else (
            f"{d0.strftime('%-d')}\u2013{d1.strftime('%-d %b %Y')}" if d0.month == d1.month else
            f"{d0.strftime('%-d %b')} \u2013 {d1.strftime('%-d %b %Y')}")
        pl.append({"group": f, "when": when, "trained": PLAIN[f], "runs": g.run_dir.nunique(),
                   "agents": "both" if g.agent.nunique() == 2 else g.agent.iloc[0],
                   "heal": ", ".join(sorted(g.bush_heal.unique())).replace("25x", "25 times faster")
                                                                   .replace("1x", "same as elsewhere")})
    tok["{{TABLE:datasets}}"] = table(pd.DataFrame(pl), ["group", "when", "trained", "runs", "agents", "heal"],
                                      ["group", "training started", "what the agents learned in", "runs",
                                       "agent type", "healing on a bush"], num=("runs",), nowrap=("when",),
                                      min_width=860)
    tok["{{FIG:map}}"] = figure(
        "f7b_map", "Three scatter panels (hunting predator, chasing rabbit, wandering rabbit) of every run: horizontal, how much the animal raises bush dwell; vertical, how much injury "
        "raises bush dwell with no animal. Runs trained before 22 September lie along the zero line, spread from 0 "
        "to 75 points across; recent runs sit about 10 points higher with 15 to 45 points across. The top right is "
        "empty.",
        "Horizontal: animal dependence, bush dwell with the animal minus bush dwell with no animal, both with the "
        "agent unhurt, in percentage points (left: hunting predator; middle: chasing rabbit; right: wandering rabbit). Vertical: "
        "state dependence, bush dwell with no animal at injury 70 minus at injury 0, in percentage points. Each "
        "value is the average over the newest 20 checkpoints, formed checkpoint by checkpoint. All three panels share one "
        "horizontal scale. Colour = scene set; shape = agent type (circle ordinary, triangle modulated, square "
        "Dreamer). Group means are in the table under the figure.",
        "Two separate kinds of behaviour: older runs react to animals but not to their own injury; recent runs "
        "react to injury even with no animal, and react to animals only moderately. No run does both strongly.",
        "scripts/analysis/studies/f7b_across_runs/figures.py --figure map", title="Figure M &mdash; animal dependence against state dependence")
    mg = []
    for f in FX.FAMILY_ORDER:
        for k in FX.SET_ORDER:
            ids = R[(R.family == f) & (R.scene_set == k)].id
            if not len(ids):
                continue
            row = {"group": f, "set": FX.SET_TAG[k], "n": len(ids),
                   "heal": ", ".join(sorted(R[R.id.isin(ids)].bush_heal.unique()))}
            for q, c in (("pred-vs-none@00", "ap"), ("rabbit-vs-none@00", "ar"), ("rabbitwander-vs-none@00", "aw"),
                         ("none", "st")):
                e = eff(q, ids, interp=False)
                row[c] = f"{e['mean'].mean():+.1f}" if len(e) else "n/a"
            mg.append(row)
    tok["{{TABLE:map_groups}}"] = table(pd.DataFrame(mg), ["group", "set", "n", "heal", "ap", "ar", "aw", "st"],
                                        ["group (oldest first)", "scene set", "rows", "healing on a bush",
                                         "animal dep., predator", "animal dep., chasing rabbit",
                                         "animal dep., wandering rabbit", "state dep."],
                                        num=("n", "ap", "ar", "aw", "st"), min_width=900)
    tok["{{FIG:factors}}"] = figure(
        "f7b_factors", "Two panels, one row per factor. Left: healing 25 times faster on a bush raises injured bush "
        "dwell with a wandering rabbit by about 16 points in every pair; every other factor stays within a few points. "
        "Right: the same factor lowers the wandering rabbit's extra threat value by about 5 points; the largest rises "
        "come from a jumping predator (level 04) and are small and mixed.",
        "Horizontal: the change, in percentage points of bush dwell, when the factor is switched on, within matched "
        "pairs of runs (or of tests of the same run) that differ in that factor and as little else as the existing "
        "runs allow. Left (A): bush dwell with a wandering rabbit at injury 70 minus at injury 0. Right (B): bush "
        "dwell with a wandering rabbit minus with no animal, both at injury 70. Vertical: factor (no unit), with the "
        "number of pairs in brackets, sorted by the size of the effect in A. Both panels share one horizontal scale. One dot per pair; hollow = the agent "
        "died early in a scene the value uses; black bar = mean over pairs.",
        "Only one factor moves A much: fast healing on a bush. It also lowers B, because the injured agent then "
        "hides with no animal too. Nothing in the existing runs raises B by more than a few points on average.",
        "scripts/analysis/studies/f7b_across_runs/figures.py --figure factors (data: factors.py)",
        title="Figure F &mdash; which factor moves the two targets")
    Fc = pd.read_csv(os.path.join(a.data, "factors.csv"))
    Fc["rng1"] = [f"{x:+.1f} to {y:+.1f}" for x, y in zip(Fc.dT1_lo, Fc.dT1_hi)]
    Fc["rng2"] = [f"{x:+.1f} to {y:+.1f}" for x, y in zip(Fc.dT2_lo, Fc.dT2_hi)]
    for c in ("dT1", "dT2", "dS"):
        Fc[c] = Fc[c].map(lambda v: f"{v:+.1f}")
    Fc["key"] = [(-round(abs(float(v)), 1), f) for v, f in zip(Fc.dT1, Fc.factor)]   # same key as Figure F
    Fc = Fc.sort_values("key")
    Fc["pairs"] = [f"{p}" + (f" ({h} hollow)" if h else "") for p, h in zip(Fc.pairs, Fc.hollow)]
    tok["{{TABLE:factors}}"] = table(Fc, ["factor", "pairs", "dT1", "rng1", "dT2", "rng2", "dS"],
                                     ["factor switched on", "pairs", "A: mean", "A: range",
                                      "B: mean", "B: range", "state dep.: mean"],
                                     num=("dT1", "dT2", "dS"), nowrap=("pairs", "rng1", "rng2"), min_width=820)
    tok["{{FIG:timeline}}"] = figure(
        "f7b_timeline", "Timeline of when each group of runs was trained: seven July groups (including the Dreamer runs), three "
        "August groups, then curriculum wave 1 on 21 September, fast-bush-healing training on 22 September, the body "
        "rules and the first smell-study pair on 27 September, the rest of the smell study on 1 October and the "
        "thirst task on 2 October; dashed lines mark four changes to the worlds or tests.",
        "Horizontal: the date each training run started in 2026, read from the run's folder name (one axis from "
        "early July to early October). "
        "Vertical: group of runs (no unit), oldest at the top. One marker per run, several on one day spread "
        "vertically; dark = trained with injury healing 25&times; faster on a bush, grey = trained without it; "
        "circle = ordinary agent, triangle = modulated agent. Numbered dashed lines are changes to the worlds or "
        "the tests, explained in the legend. Square = Dreamer agent.",
        "Every run trained without fast bush healing is older than 22 September, and every run trained after it "
        "has it, so on this page bush-healing speed and training date cannot be separated.",
        "scripts/analysis/studies/f7b_across_runs/figures.py --figure timeline", title="Figure 0 &mdash; when each group was trained")
    ss = pd.DataFrame([{"set": FX.SET_TAG[k], "what": FX.SET_SHORT[k].split(" (")[1].rstrip(")") if "(" in FX.SET_SHORT[k] else "",
                        "rows": int((R.scene_set == k).sum())} for k in FX.SET_ORDER])
    ss["what"] = [{"july": "July 2026 runs; animals could walk into the bush; no temperature system",
                   "july_noise": "the July scenes with noise on the senses, for the agent trained with noise",
                   "refuge": "August scenes whose bush blocks animals, for the bush-refuge and rest-premium runs",
                   "core_old": "the core scenes as they were before the 2026-09-23 fix: the test bush let animals in",
                   "core": "bush hides the agent and blocks animals; no campfire",
                   "thermal": "core scenes in a level-05/06 body, with one of eight fire and ambient-temperature variants",
                   "injgrid": "only three scenes (no animal, hunting predator, wandering rabbit) at ten injury levels",
                   "world": "scenes rebuilt on the agent's own training world, with a campfire beside the bush"}[k]
                  for k in FX.SET_ORDER]
    ss["used"] = [", ".join(f for f in FX.FAMILY_ORDER if ((R.family == f) & (R.scene_set == k)).any()) for k in FX.SET_ORDER]
    tok["{{TABLE:scene_sets}}"] = table(ss, ["set", "what", "used", "rows"], ["scene set", "what differs", "groups tested in it", "rows"],
                                        num=("rows",), min_width=760)
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
    fams = R.groupby(["family", "scene_set", "bush_heal"]).agg(rows=("id", "size"), runs=("run_dir", "nunique"),
                                                   ckpts=("n_ckpt", "median")).reset_index()
    fams["set"] = fams.scene_set.map(FX.SET_TAG)
    fams["ckpts"] = fams.ckpts.map(lambda v: f"{v:.0f}")
    tok["{{TABLE:families}}"] = table(fams, ["family", "set", "bush_heal", "rows", "runs", "ckpts"],
                                      ["group", "scene set", "healing on a bush", "rows", "distinct runs",
                                       "checkpoints tested (median)"],
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
    tok["{{TABLE:runs}}"] = table(R2, ["family", "set", "setting", "agent", "bush_heal", "run", "n_ckpt"],
                                  ["group", "scene set", "setting", "agent", "healing on a bush", "training run",
                                   "checkpoints"], num=("n_ckpt",),
                                  nowrap=("run",), min_width=1300)


    # ---- most effective conditions (highlight.py; checkpoint_stats.py over 2-10 M steps)
    T, n_rank = HL.ranking(a.data)
    CND = HL.conditions(T, 10)
    rows_ = []
    for k, (cond, ro, rm) in enumerate(CND, 1):
        for agent, r in (("ordinary", ro), ("modulated", rm)):
            rows_.append({"rank": k if agent == "ordinary" else "", "cond": HL.label(r, agent=False) if agent == "ordinary" else "",
                          "agent": agent, "inj": num_text(f"{r.inj:+.0f}"), "inj_pos": f"{100 * r.inj_pos:.0f}%",
                          "injw": num_text(f"{r.injw:+.0f}"), "pred": num_text(f"{r.pred:+.0f}"),
                          "wand": num_text(f"{r.wand:+.0f}"), "jump": f"{r.jump:.0f}"})
    tok["{{TABLE:hl_top}}"] = table(pd.DataFrame(rows_), ["rank", "cond", "agent", "inj", "inj_pos", "injw", "pred", "wand", "jump"],
                                    ["#", "condition", "agent", "injury, no animal", "% ckpts up", "injury, rabbit",
                                     "predator", "rabbit", "jump"],
                                    num=("rank", "inj", "inj_pos", "injw", "pred", "wand", "jump"), min_width=820)
    tok["{{TABLE:hl_top}}"] += ("<p>Columns, all in percentage points of bush dwell over 2&ndash;10 M training "
        "steps: <b>injury, no animal</b> = injured (70) minus unhurt (0) with no animal; <b>% ckpts up</b> = share of "
        "checkpoints where that difference is above zero; <b>injury, rabbit</b> = the same with the wandering rabbit; "
        "<b>predator</b> / <b>rabbit</b> = hunting predator / wandering rabbit minus no animal, unhurt; <b>jump</b> = "
        "average change of the unhurt no-animal value between neighbouring checkpoints.</p>")
    tok["{{HL1_COND}}"] = html.escape(HL.label(CND[0][1], agent=False))
    tok["{{HL2_COND}}"] = html.escape(HL.label(CND[1][1], agent=False))
    # ---- test-scene check (2026-10-06): later studies, own scenes vs neutral re-test, matched pairs
    Rr = R[R.family.isin(["Smell study (level 05)", "Body rules (level 05)", "Thirst task"])].copy()
    Rr = Rr[(Rr.scene_set == "world") | Rr.setting.str.endswith("neutral clean")]
    Rr["set"] = np.where(Rr.scene_set == "world", "own", "neutral")
    Rr["cond"] = Rr.setting.str.replace("; scene variant neutral clean", "", regex=False)
    Sa = pd.read_csv(os.path.join(a.data, "ckpt_summary.csv"))
    Sa = Sa[Sa.window == "all"]
    for q, c in (("injury none", "inj"), ("injury rabbitwander", "injw")):
        Rr[c] = Rr.id.map(Sa[Sa.quantity == q].set_index("id")["mean"])
    Pv = Rr.pivot_table(index=["family", "cond", "seed", "set"], columns="agent", values=["inj", "injw"]).dropna()
    rows_sc = []
    for (fam, st), x in Pv.groupby(level=[0, 3]):
        dw = x["injw"]["modulated"] - x["injw"]["ordinary"]
        di = x["inj"]["modulated"] - x["inj"]["ordinary"]
        rows_sc.append({"family": fam.replace(" (level 05)", ", level 05").replace("Thirst task", "Thirst task, level 06"),
                        "set": st, "pairs": len(x),
                        "inj": f"{int((di > 0).sum())} of {len(x)}", "di": num_text(f"{di.median():+.1f}"),
                        "injw": f"{int((dw > 0).sum())} of {len(x)}", "dw": num_text(f"{dw.median():+.1f}"),
                        "_up": int((dw > 0).sum()), "_n": len(x), "_neut": st == "neutral",
                        "_l05": "level 05" in fam})
    SC = pd.DataFrame(rows_sc).sort_values(["family", "set"], ascending=[True, True])
    SC["family"] = [f if i == 0 or f != prev else "" for i, (f, prev) in
                    enumerate(zip(SC.family, [None] + list(SC.family[:-1])))]   # study named once per pair of rows
    tok["{{TABLE:scene_check}}"] = table(SC, ["family", "set", "pairs", "inj", "di", "injw", "dw"],
                                         ["study", "scenes", "pairs", "modulated larger, no animal",
                                          "median diff., no animal (pp)", "modulated larger, rabbit",
                                          "median diff., rabbit (pp)"],
                                         num=("pairs", "inj", "di", "injw", "dw"), min_width=640) + (
        "<p><b>Scenes:</b> <b>neutral</b> = air at 0&nbsp;°C, no campfire, body temperature starting at 0; "
        "<b>own</b> = the study's own scenes, cold air with a campfire beside the bush and a random starting body "
        "temperature. A pair is the ordinary and the modulated agent trained in the same world with the same seed; "
        "<b>modulated larger</b> counts the pairs where the modulated agent's injury effect (injury 70 minus 0) is the "
        "larger one, with no animal or with the wandering rabbit; the difference is modulated minus ordinary, in "
        "percentage points (pp) of bush dwell, mean over 2&ndash;10 M training steps.</p>")
    l05 = SC[SC._l05]
    tok["{{CORR_NEUT_UP}}"] = str(int(l05[l05._neut]._up.sum()))
    tok["{{CORR_NEUT_N}}"] = str(int(l05[l05._neut]._n.sum()))
    tok["{{CORR_OWN_UP}}"] = str(int(l05[~l05._neut]._up.sum()))
    tok["{{CORR_OWN_N}}"] = str(int(l05[~l05._neut]._n.sum()))
    tok["{{CORR_NRUNS}}"] = str(int(Rr[Rr.scene_set == "thermal"].run_dir.nunique()))
    tok["{{HL_N}}"] = str(T.cond.nunique())
    tok["{{HL_NR}}"] = str(T[T.paired].cond.nunique())
    for k, (cond, ro, rm) in (("1", CND[0]), ("2", CND[1])):
        for ag, r in (("M", rm), ("O", ro)):
            tok[f"{{{{HL{k}{ag}_INJ}}}}"] = num_text(f"{r.inj:+.0f}")
            tok[f"{{{{HL{k}{ag}_POS}}}}"] = f"{100 * r.inj_pos:.0f}"
            tok[f"{{{{HL{k}{ag}_INJW}}}}"] = num_text(f"{r.injw:+.0f}")
            tok[f"{{{{HL{k}{ag}_PRED}}}}"] = num_text(f"{r.pred:+.0f}")
            tok[f"{{{{HL{k}{ag}_WAND}}}}"] = num_text(f"{r.wand:+.0f}")
            tok[f"{{{{HL{k}{ag}_JUMP}}}}"] = f"{r.jump:.0f}"
    def grid_mean(leaf, sc, inj):
        return HL.K.on_grid(HL.series(leaf, sc, inj), HL.LO_M, HL.HI_M, HL.SPACING_M).mean()
    o2, m2 = HL.DOSE
    tok["{{D2_O0}}"], tok["{{D2_O90}}"] = f"{grid_mean(o2, 'none', '00'):.0f}", f"{grid_mean(o2, 'none', '90'):.0f}"
    tok["{{D2_M0}}"], tok["{{D2_M90}}"] = f"{grid_mean(m2, 'none', '00'):.0f}", f"{grid_mean(m2, 'none', '90'):.0f}"
    tok["{{D2_OP}}"] = num_text(f"{grid_mean(o2, 'pred', '00') - grid_mean(o2, 'none', '00'):+.0f}")
    # ---- B2 at ten starting injuries (injury-grid sweeps; highlight.py --figure injtrain / injdose)
    for key in ("lvl05", "lvl04"):
        for ag, A in (("ordinary", "O"), ("modulated", "M")):
            for sc, S_ in (("none", "N"), ("rabbitwander", "W"), ("rabbit", "C"), ("pred", "P")):
                leaf = HL.grid_leaf(key, ag, sc)
                for inj in ("00", "90"):
                    tok[f"{{{{IG_{key}_{A}{S_}{inj}}}}}"] = f"{grid_mean(leaf, sc, inj):.0f}"
    ig_axes = ("Horizontal: training, in million steps (0&ndash;10). Vertical: bush dwell, the share of the scene's "
               "100 steps spent on the bush (%, 0&ndash;100), the same scale in every panel. Rows: four scenes (no "
               "animal, wandering rabbit, chasing rabbit, hunting predator); columns: the ordinary and the modulated "
               "agent. Ten lines per panel, one per starting injury of the test: grey = 0 (unhurt, as in B2 and B3), "
               "light to dark blue = 10 to 90 in steps of 10 (injury 70 has B2's blue); each line averages 5 "
               "neighbouring checkpoints. Text above each panel: bush dwell at injury 0, 50 "
               "and 90, mean over 2&ndash;10 M steps. The shaded first 2 M steps are not used in those means.")
    dose_axes = ("Horizontal: starting injury of the test, 0 (unhurt) to 90 in steps of 10 (0&ndash;100 scale). "
                 "Vertical: bush dwell, the share of the scene's 100 steps spent on the bush (%), mean over the "
                 "checkpoints from 2 to 10 M training steps, the same scale in all four panels; shading is the 95 % "
                 "interval (shading, with dashed edges in the line's tone). Open grey circles: ordinary agent; filled "
                 "black squares: modulated agent. Same layout and scale as Figure B4.")
    for key, lab_t, lab_d, ttl in (("lvl05", "B5", "B6", "level 05 pair"), ("lvl04", "B7", "B8", "level 04 pair")):
        tok[f"{{{{FIG:ig_train_{key}}}}}"] = figure(
            f"f7b_hl_injtrain__{key}", f"Eight panels, four scenes by two agents: bush dwell across training, ten lines per "
            f"panel for starting injuries 0 to 90, {ttl}.", ig_axes,
            {"lvl05": "In the modulated agent's calm scenes (no animal, wandering rabbit) the ten lines are stacked in "
                      "injury order, evenly spaced, from early in training to the end: more injury, more time in the "
                      "bush, by a steady step. The ordinary agent's lines are also in injury order for much of training, "
                      "but packed closer (a smaller injury effect) and they come apart late: after about 8.5 M steps its "
                      "less injured lines rise above the more injured ones with the wandering rabbit. With the chasing "
                      "rabbit and the predator the lines of both agents lie on top of each other: the animal, not the "
                      "injury, sets how much they hide.",
             "lvl04": "The same comparison at level 04: the modulated agent's calm-scene lines stack in injury order; the "
                      "ordinary agent's swing together from checkpoint to checkpoint, all injuries alike."}[key],
            f"scripts/analysis/studies/f7b_across_runs/highlight.py --figure injtrain --key {key}",
            title=f"Figure {lab_t} &mdash; {ttl} across training, at ten starting injuries")
        tok[f"{{{{FIG:ig_dose_{key}}}}}"] = figure(
            f"f7b_hl_injdose__{key}", f"Four panels, one per scene: bush dwell against starting injury, ordinary and "
            f"modulated agent, {ttl}.", dose_axes,
            {"lvl05": "The same data as the figure above, reduced to one number per injury: a straight rise with injury in "
                      "the modulated agent's calm scenes, a flatter line for the ordinary agent, and little change with "
                      "injury in the animal scenes.",
             "lvl04": "The modulated agent's calm-scene lines rise straight with injury from a low start. The ordinary "
                      "agent sits far higher at every injury, with wide intervals, and does not rise steadily: it dips in "
                      "the middle injuries with no animal. In the animal scenes injury changes little for either agent."}[key],
            f"scripts/analysis/studies/f7b_across_runs/highlight.py --figure injdose --key {key}",
            title=f"Figure {lab_d} &mdash; {ttl}, bush dwell against starting injury")

    hp = "scripts/analysis/studies/f7b_across_runs/highlight.py"
    pair_axes = ("Horizontal: training, in million steps (0&ndash;10). Vertical: bush dwell, the share of the "
                 "scene's 100 steps spent on the bush (%, 0&ndash;100), the same scale in every panel. Rows: four "
                 "scenes (no animal, wandering rabbit, chasing rabbit, hunting predator); columns: the ordinary and "
                 "the modulated agent. Grey line = unhurt (starting injury 0), blue line = injured (starting injury "
                 "70); thin = each checkpoint, thick = average of 5 neighbouring checkpoints. The shaded first 2 M "
                 "steps are drawn but not used in the printed numbers. Text above each panel's 100 % line: the injury effect and, for the animal scenes, the animal's effect, over 2&ndash;10 M steps.")
    tok["{{FIG:hl_rank}}"] = figure(
        "f7b_hl_rank", f"{len(CND)} training conditions, ranked, each with an ordinary and a modulated agent "
        f"({2 * len(CND)} runs), each run with three dot-and-interval marks: the injury effect with no animal, "
        "the injury effect with a wandering rabbit, and the predator response.",
        "Vertical: the ten top-ranked training conditions (no unit), best at the top; in each row the upper mark "
        "is the ordinary agent (open grey circle) and the lower mark the modulated agent (filled black square) trained in the same condition. Horizontal, left panel: injury 70 minus "
        "injury 0 with no animal; middle panel: the same with a wandering rabbit; right panel: bush dwell with a "
        "hunting predator minus with no animal, both unhurt. All three in percentage points of bush dwell, mean "
        "over the checkpoints from 2 to 10 M training steps, with a 95 % interval. Agents trained with the "
        "temperature system are measured in neutral scenes (0 &deg;C air, no campfire).",
        f"In {sum(int(m.injw > o.injw) for _, o, m in CND)} of the {len(CND)} conditions shown, the modulated agent's "
        "injury effect with the wandering rabbit is the larger one, and in most of them its predator response too. "
        "Where the gap is large, the ordinary agent's injury effect is small or uncertain (wide interval), while "
        "the modulated agent's stays near 10&ndash;18 points.",
        f"{hp} --figure rank", title="Figure B1 &mdash; the ten conditions where both effects are largest, ordinary and modulated side by side")
    for key, lab, ttl in (("lvl05", "B2", "level 05 pair, across training"), ("lvl04", "B3", "level 04 pair, across training")):
        tok[f"{{{{FIG:hl_{key}}}}}"] = figure(
            f"f7b_hl_pair__{key}", f"Eight panels: four scenes by two agents, bush dwell across training, unhurt and injured.",
            pair_axes,
            {"lvl05": "In the modulated agent the injured line sits steadily above the unhurt line with no animal and with "
                      "the wandering rabbit, at nearly every checkpoint, while both lines rise together for the chasing "
                      "rabbit and the predator. In the ordinary agent the two lines overlap and drift upward late in "
                      "training, including for the harmless wandering rabbit.",
             "lvl04": "The same picture at level 04: the modulated agent's calm-scene lines are flat and ordered by injury; "
                      "the ordinary agent's swing between about 0 and 90 % from one checkpoint to the next, in every "
                      "calm scene at once."}[key],
            f"{hp} --figure pair --key {key}", title=f"Figure {lab} &mdash; {ttl}")
    tok["{{FIG:hl_dose}}"] = figure(
        "f7b_hl_dose", "Two panels, ordinary and modulated: bush dwell rising with starting injury, three scenes.",
        "Horizontal: starting injury of the test, 0 (unhurt) to 90 in steps of 10 (0&ndash;100 scale). Vertical: bush "
        "dwell, the share of the scene's 100 steps spent on the bush (%), mean over the checkpoints from 2 to 10 M "
        "training steps, 0&ndash;100 in all three panels (one per scene: no animal, wandering rabbit, hunting "
        "predator). Open grey circles: ordinary agent; filled black squares: modulated agent; dashed edges and "
        "shading: 95 % interval. Same layout and scale as Figures B6 and B8.",
        "Bush dwell climbs steadily with injury in both agents, steeply in the ordinary one. The wandering-rabbit "
        "panel looks like the no-animal panel: neither agent treats the wandering rabbit as a threat at any injury. "
        "The predator raises bush dwell above both.",
        f"{hp} --figure dose", title="Figure B4 &mdash; level 02 pair, bush dwell against starting injury")

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
        f4.append(f'<h4 class="fh"><span class="n">Figure 4{"abcdefghijk"[k]}</span>{html.escape(title)}</h4>')
        f4.append(figure(stem, f"Bush dwell per scene for each run of the group {title}, at injury 0 and 70.",
                         "Horizontal, in each panel: bush dwell over the newest 20 checkpoints, the share of the "
                         "scene's 100 steps spent on the bush (%, 0&ndash;100). Vertical: one row per run (setting "
                         "&middot; agent; no unit). One panel per scene. Light grey marker = start injury 0, dark marker = "
                         "start injury 70; circle = ordinary agent, triangle = modulated agent, square = Dreamer agent; "
                         "* = died early in a "
                         "predator-free scene.",
                         html.escape(LEVEL_CAP[gname]),
                         f"scripts/analysis/studies/f7b_across_runs/figures.py --figure levels --group {gname}",
                         title=f"Figure 4{'abcdefghijk'[k]} &mdash; {html.escape(title)}"))
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
