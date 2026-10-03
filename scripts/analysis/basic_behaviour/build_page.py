#!/usr/bin/env python3
"""build_page.py - assemble the Basic Behaviour Analysis page from the figures that exist.

Plan: BASIC_BEHAVIOUR_ANALYSIS_PIPELINE.md (Revision 2), `page_template.html` and `build_page.py`.

    $P scripts/analysis/basic_behaviour/build_page.py --population <json> \
        --out-root <abs results/analysis/basic_behaviour/<pop>> --page-dir <docs/... page folder>

Takes the House Style Sheet's <style>, viewer and cue script from
docs/develop/active/meta/house_style_sheet.template.html at build time (as
studies/modulator_clues/build_algorithmic_null_page.py does), inlines the Pretendard subsets, embeds
each figure PNG from <page-dir>/figures/, renders each figure's data statement from its
<stem>.samples.json, and prints the regenerating command. Blocks F2-F6 are repeated once per target
whose figure exists. A block with nothing on disk becomes a visible "not yet produced" box; the build
then prints `partial: present [...], pending [...]` and exits 0.

FAILS (non-zero, no page written) on: a present figure missing any of PNG / SVG / PDF / samples or its
generating script; a <figure> holding <svg> or <canvas>; a file in the figure folder that is not part
of the F1-F7 sequence; a caption without <b>Axes.</b>; a block without "How it is computed" or with
one outside 150-250 words; a data row whose used count exceeds its available count; any unsubstituted
token. Writes <page-dir>/basic_behaviour.html and the generated mirror <page-dir>/basic_behaviour.md
(each figure's Axes sentence + data table, from the same source, so the two cannot drift).
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _fig as FG                                                       # noqa: E402
import registry as REG                                                  # noqa: E402

ROOT = FG.ROOT
HOUSE = os.path.join(ROOT, "docs/develop/active/meta/house_style_sheet.template.html")
FONTS = os.path.join(ROOT, "assets/fonts/pretendard/subset")
TEMPLATE = os.path.join(HERE, "page_template.html")
# Populations with water (BASIC_BEHAVIOUR_WATER): the <!-- WATER --> sections of the template are kept
# (and stripped for every other population, which then builds exactly as before), and Figure 7 comes
# from this block instead of the template's.
TEMPLATE_F7_WATER = os.path.join(HERE, "page_template_f7_water.html")
F7W_STEMS = ["f7_pond_traces__g10", "f7_pond_traces__g15", "f7_pond_traces__g20", "f7_pond_levels",
             "f7_pond_visits"]
F7W_ARGS = {**{f"f7_pond_traces__g{m}": f"--figure pond_traces --map {m}" for m in ("10", "15", "20")},
            "f7_pond_levels": "--figure pond_levels", "f7_pond_visits": "--figure pond_visits"}
BLOCKS = {"F1": ("f1_behaviours_survival", False), "F2": ("f2_factor_inventory", True),
          "F3": ("f3_univariate", True), "F4": ("f4_multivariate", True),
          "F5": ("f5_settings", True), "F6": ("f6_crosstabs", True),
          "F7": ("f7_probes", None)}
# Figure 7 (probe scenes): fixed stems, all drawn by f7_probes.py from probes.py's outputs. A None
# in BLOCKS marks this "explicit" kind: the template names every stem with data-fig.
F7_STEMS = ["f7_probe_traces__hv2ch", "f7_probe_traces__hv1ch", "f7_probe_traces__hv1chm",
            "f7_probe_levels", "f7_probe_confusion", "f7_probe_threat", "f7_probe_budget",
            "f7_probe_training", "f7_probe_other"]
F7_ARGS = {"f7_probe_traces__hv2ch": "--figure traces --world hv2ch",
           "f7_probe_traces__hv1ch": "--figure traces --world hv1ch",
           "f7_probe_traces__hv1chm": "--figure traces --world hv1chm",
           **{f"f7_probe_{k}": f"--figure {k}" for k in ("levels", "confusion", "threat", "budget",
                                                          "training", "other")}}
HOWTO = "How it is computed"
EXTS = ("png", "svg", "pdf", "samples.json")
UNBREAKABLE_MAX = 40
EMBED_WIDTH = 1600            # px: embedded copy only; full-resolution PNG / SVG / PDF stay on disk
PAGE_MAX_BYTES = 15_500_000   # under the 16 MB artifact limit, with margin


def embed_png(path: str) -> str:
    """Base64 of a lighter copy of the figure for embedding: at most EMBED_WIDTH wide and quantised
    to a 256-colour palette (the house figures use a handful of flat colours, so this is visually
    lossless at page width). The files in the figure folder are not touched."""
    import io
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width > EMBED_WIDTH:
        im = im.resize((EMBED_WIDTH, round(im.height * EMBED_WIDTH / im.width)), Image.LANCZOS)
    # Palette = the house colours, exactly, plus 240 colours chosen by octree for everything else
    # (anti-aliasing, the heat-map ramp). A free palette alone shifted the series green visibly,
    # which would break the colour = world encoding; pinned entries cannot shift.
    house = [FG.H.PAPER, FG.H.INK, FG.H.INK_2, FG.H.TEXT_LIGHT, FG.H.TICK_LINE, FG.H.RULE,
             FG.H.BG_SOFT, *FG.H.SERIES, "#ffffff", "#000000"]
    pinned = [int(h.lstrip("#")[i:i + 2], 16) for h in house for i in (0, 2, 4)]
    rest = im.quantize(colors=256 - len(house), method=Image.Quantize.FASTOCTREE,
                       dither=Image.Dither.NONE).getpalette()[: 3 * (256 - len(house))]
    import numpy as np
    P = np.array(pinned + rest, dtype=np.int32).reshape(-1, 3)
    A = np.asarray(im, dtype=np.int32)
    flat = A.reshape(-1, 3)
    uniq, inv = np.unique(flat, axis=0, return_inverse=True)
    idx = np.empty(len(uniq), dtype=np.uint8)
    for i in range(0, len(uniq), 4096):              # exact nearest palette entry (PIL's is approximate)
        d = ((uniq[i:i + 4096, None, :] - P[None, :, :]) ** 2).sum(2)
        idx[i:i + 4096] = d.argmin(1)
    im = Image.fromarray(idx[inv.ravel()].reshape(A.shape[:2]), mode="P")
    im.putpalette(P.astype(np.uint8).ravel().tolist())
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


class BuildError(SystemExit):
    pass


def fail(msg):
    raise BuildError(f"build_page: {msg}")


def words(fragment):
    t = re.sub(r"<[^>]+>", " ", fragment)
    t = re.sub(r"\{\{[^}]+\}\}", " ", t)
    return len(html.unescape(t).split())


def wrap_cell(text):
    esc = html.escape(str(text), quote=False)
    esc = re.sub(r"([/_.,])(?=\S)", r"\1<wbr>", esc)
    long = [w for w in re.sub(r"<wbr>", " ", esc).split() if len(w) > UNBREAKABLE_MAX]
    if long:
        fail(f"data-statement cell holds an unbreakable run over {UNBREAKABLE_MAX} characters: {long}")
    return esc


RUN_RE = re.compile(r"^(?P<what>.*), (?P<run>[^,]+ smell[^,]*, [^,]+ agent, seed \d+)$")


def merge_rows(rows):
    """Rows that differ only in the run they describe become one row naming how many runs share it
    (register F71). Order of first appearance is kept."""
    groups, order = {}, []
    for r in rows:
        m = RUN_RE.match(r["what"])
        key = (m.group("what") if m else r["what"], r["used"], r["total"], r["note"])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(m.group("run") if m else None)
    out = []
    for key in order:
        runs = [x for x in groups[key] if x]
        what = key[0] if not runs else (f"{key[0]}, {runs[0]}" if len(runs) == 1 else f"{key[0]}, {len(runs)} runs")
        tot = key[2]
        out.append({"what": what, "used": key[1], "total": tot,
                    "pct": (100.0 * key[1] / tot) if tot else 0.0, "note": key[3]})
    return out


def data_table(stem, rows):
    for r in rows:
        if r["used"] > r["total"]:
            fail(f"{stem}: row '{r['what']}' uses {r['used']} of {r['total']}")
        if r["total"] and r["used"] < r["total"] and not str(r.get("note", "")).strip():
            fail(f"{stem}: row '{r['what']}' uses {r['pct']:.1f}% of what is available but gives no "
                 f"reason (guide 11b: every subset says why)")
    merged = merge_rows(rows)
    out = []
    for r in merged:
        out.append(f'<tr><td>{wrap_cell(r["what"])}</td><td class="n">{r["used"]:,}</td>'
                   f'<td class="n">{r["total"]:,}</td><td class="n">{r["pct"]:.1f}%</td>'
                   f'<td>{wrap_cell(r["note"])}</td></tr>')
    pcts = [r["pct"] for r in merged if r["total"]]
    lo_, hi_ = (f"{min(pcts):.0f}", f"{max(pcts):.0f}") if pcts else ("", "")
    span = ("n/a" if not pcts else f"{lo_}%" if lo_ == hi_ else f"{lo_}&ndash;{hi_}%")   # "100%", never "100–100%"
    summary = (f"<b>Data.</b> {len(merged)} subset{'s' if len(merged) != 1 else ''} "
               f"({len(rows)} rows before merging identical ones), using {span} of what was available "
               f"&mdash; open for the counts, emitted by the figure script")
    return (f'<details class="bb-data"><summary>{summary}</summary>'
            '<p class="cue" hidden>&larr; wider than the screen &mdash; scroll it sideways</p>'
            '<div class="scroll"><table class="wide" style="min-width:720px"><thead><tr><th>subset</th><th class="n">used</th>'
            '<th class="n">available</th><th class="n">share</th><th>why</th></tr></thead><tbody>'
            + "".join(out) + "</tbody></table></div></details>")


TOC_TITLE = {"F1": "Behaviours and survival, per run", "F2": "Which factors each run's analysis uses",
             "F3": "Each factor on its own, per run", "F4": "The factors fitted together, per run",
             "F5": "Which settings move each behaviour (screening)",
             "F6": "By state, rabbit smell and nearby animals",
             "F7": "Experiment tests (exploratory)"}
LABEL_PX = FG.H.FS_LABEL * 220 / 72          # smallest label on every figure canvas (house.apply: 220 dpi)


def width_floor(png_path):
    """Display width at which the smallest label is 9 px (register F65)."""
    from PIL import Image
    import math
    return math.ceil(Image.open(png_path).width * 9 / LABEL_PX)


F7_TOC = [("f7a", "over training"), ("f7b", "per scene"), ("f7c", "confusion contrast"),
          ("f7d", "threat discrimination"), ("f7e", "worlds vs noise"), ("f7f", "vs training environment"),
          ("f7g", "other measures")]


def toc_html(toc):
    items = []
    for bid, figs in toc:
        if bid == "F7":
            subs = " &middot; ".join(f'<a href="#{fid}">{fid[1:]} {lab}</a>' for fid, lab in F7_TOC)
            items.append(f'<li>Figure 7 &middot; {TOC_TITLE[bid]}<br><span class="bb-sub">{subs}</span></li>')
        elif len(figs) == 1 and figs[0][0] is None:
            items.append(f'<li><a href="#{figs[0][1]}">Figure {bid[1]}</a> &middot; {TOC_TITLE[bid]}</li>')
        else:
            subs = " &middot; ".join(f'<a href="#{fid}">{bid[1]}{"abcdefgh"[k]} {html.escape(FG.TARGET_NOUN[t])}</a>'
                                     for k, (t, fid) in enumerate(figs))
            items.append(f'<li>Figure {bid[1]} &middot; {TOC_TITLE[bid]}<br><span class="bb-sub">{subs}</span></li>')
    return ('<nav class="col bb-toc" aria-label="Figures on this page"><h2><span class="num">CONTENTS</span></h2>'
            '<ol>' + "".join(items) + '</ol></nav>')


def blocks_of(page):
    return {m.group(1): m.group(0) for m in
            re.finditer(r"<!-- BLOCK (F\d) -->.*?<!-- /BLOCK \1 -->", page, re.S)}


def check_block(bid, block):
    for fig in re.findall(r"<figure\b.*?</figure>", block, re.S):
        if re.search(r"<(svg|canvas)\b", fig):
            fail(f"{bid}: a <figure> draws in the page (<svg> or <canvas>); figures come from scripts")
        cap = re.search(r"<figcaption>.*?</figcaption>", fig, re.S)
        if not cap or "<b>Axes.</b>" not in cap.group(0):
            fail(f"{bid}: caption has no <b>Axes.</b> sentence (guide 11a)")
        how = re.search(r'<div class="howto">(.*?)</div>', fig, re.S)
        if not how:
            fail(f"{bid}: no '{HOWTO}' block (guide 11c)")
        eb = re.search(r'<p class="eyebrow">(.*?)</p>', how.group(1), re.S)
        if not eb or " ".join(html.unescape(eb.group(1)).split()) != HOWTO:
            fail(f"{bid}: the method block's eyebrow must read exactly '{HOWTO}'")
        n = words(how.group(1).replace(eb.group(0), " "))
        if not 150 <= n <= 250:
            fail(f"{bid}: '{HOWTO}' is {n} words; guide 11c wants 150-250")


def axes_sentence(fig_html):
    cap = re.search(r"<figcaption>(.*?)</figcaption>", fig_html, re.S).group(1)
    first = re.search(r"<span>(.*?)</span>", cap, re.S).group(1)
    t = html.unescape(re.sub(r"<[^>]+>", "", first))
    return " ".join(t.split())


def plain_reason(text: str) -> str:
    """Pre-fit reasons name factors by code; show them by their display names."""
    for code in sorted(FG.FACTOR_LABEL, key=len, reverse=True):
        text = re.sub(rf"\b{code}\b", FG.FACTOR_LABEL[code], text)
    return text


def reasons_table(D, target):
    """Every exclusion with its reason; identical (feature, reason) pairs across runs merged."""
    groups = {}
    for c in D["cells"]:
        pj = os.path.join(c["dir"], target, "prefit.json")
        if not os.path.exists(pj):
            continue
        pf = json.load(open(pj))
        for e in pf["excluded"] + pf["demoted"]:
            groups.setdefault((FG.flabel(e["name"]), plain_reason(e["reason"])), []).append(c)
        for u in c["inv"]["unhandled"]:
            groups.setdefault((f"randomised setting {u['path']}", f"no measurement: {u['why_no_handler']}"),
                              []).append(c)
    if not groups:
        return "<p>No feature was excluded and no randomised setting went unmeasured in any run.</p>"
    worlds = lambda cs: ", ".join(sorted({FG.WORLD_SHORT.get(c["world"], c["world"]) for c in cs}))
    body = "".join(f"<tr><td>{wrap_cell(a)}</td><td>{wrap_cell(b)}</td><td>{len(cs)} runs "
                   f"({html.escape(worlds(cs))})</td></tr>" for (a, b), cs in groups.items())
    return ('<details class="bb-data"><summary><b>Exclusions.</b> every feature left out of this '
            'behaviour\'s fits, with the reason and the runs it applies to</summary>'
            '<p class="cue" hidden>&larr; scroll sideways</p>'
            '<div class="scroll"><table class="wide" style="min-width:640px"><thead><tr><th>feature</th><th>reason</th>'
            f'<th>runs</th></tr></thead><tbody>{body}</tbody></table></div></details>')

def run_table(D):
    rows = []
    for c in D["cells"]:
        rows.append(f"<tr><td>{html.escape(FG.wlabel(c['world']))}</td><td>{html.escape(FG.alabel(c['agent']))}"
                    f"</td><td class=\"n\">{c['seed']}</td><td class=\"n\">{c['inv']['n_episodes']:,}</td>"
                    f"<td><code>{wrap_cell(c['run'])}</code></td></tr>")
    for c in D["unswept"] + D["not_completed"]:
        rows.append(f"<tr><td>{html.escape(FG.wlabel(c['world']))}</td><td>{html.escape(FG.alabel(c['agent']))}"
                    f"</td><td class=\"n\">{c['seed']}</td><td class=\"n\">&mdash;</td>"
                    f"<td>not yet available ({html.escape(c['status'] if c in D['not_completed'] else 'not swept')})</td></tr>")
    return ('<p class="cue" hidden>&larr; the table is wider than the screen &mdash; scroll it sideways</p>'
            '<div class="scroll"><table class="wide" style="min-width:760px">'
            '<thead><tr><th>world</th><th>agent</th><th class="n">training seed</th>'
            '<th class="n">evaluation episodes</th><th>run</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def world_table(D):
    """Section 02 (water): map, pond size, sensor radius and the share of episodes per pond corner,
    per run, from each run's inventory (the sweep's replayed pond corners)."""
    K = max(len(c["inv"]["water"]["pond_corners"]) for c in D["cells"] if "water" in c["inv"])
    head = "".join(f'<th class="n">corner {k + 1}</th>' for k in range(K))
    body = []
    for c in D["cells"]:
        w = c["inv"].get("water")
        if w is None:
            continue
        cnt = w["pond_corner_counts"]
        n = sum(cnt)
        body.append(f"<tr><td>{html.escape(FG.run_short(c))}</td><td class=\"n\">{'×'.join(map(str, w['map_size']))}</td>"
                    f"<td class=\"n\">{'×'.join(map(str, w['pond_size']))}</td><td class=\"n\">{w['sensor_radius']}</td>"
                    + "".join(f"<td class=\"n\">{100 * x / n:.1f}%</td>" for x in cnt)
                    + "<td class=\"n\">&mdash;</td>" * (K - len(cnt)) + f"<td class=\"n\">{n:,}</td></tr>")
    corners = sorted({", ".join(f"[{r + 1}, {cc + 1}]" for r, cc in c["inv"]["water"]["pond_corners"])
                      for c in D["cells"] if "water" in c["inv"]})
    return ('<details class="bb-data"><summary><b>World features and where the pond was.</b> map, pond size, '
            'smell reach (sensor radius, squares) and the share of each run\'s episodes per pond corner, '
            'rebuilt from each episode\'s seed</summary><p class="cue" hidden>&larr; scroll sideways</p>'
            '<div class="scroll"><table class="wide" style="min-width:760px"><thead><tr><th>run</th>'
            '<th class="n">map</th><th class="n">pond</th><th class="n">sensor radius</th>' + head +
            '<th class="n">episodes</th></tr></thead><tbody>' + "".join(body) + '</tbody></table></div>'
            f'<p>Pond corners (top-left square, 1-based row, column), per map: {html.escape("; ".join(corners))}. '
            'The corner is tabulated, not fitted: its effect runs through the start distance to the pond.</p>'
            '</details>')


def water_tokens(D, population, out_root):
    """The water sections' tokens, every count and claim from a record the pipeline or the study wrote
    (guide 11: never typed): the calibration record, the sweep inventories, the population manifest and
    the study doc's launch-manifest status cells, probes.py's series and refusal records."""
    import numpy as np
    cal_p = os.path.join(out_root, "probes", "calibration.json")
    if not os.path.exists(cal_p):
        fail(f"water population: no {cal_p} (copy the R2.3 calibration record there)")
    cal = json.load(open(cal_p))
    if "choice" not in cal:
        fail(f"{cal_p}: the calibration has no choice (it failed its checks)")
    S = cal["choice"]["S"]
    Skey = f"{float(S):g}"
    tab = cal["table"]
    worlds = sorted(next(iter(tab.values())))
    rows = "".join(f"<tr><td class=\"n\">{float(k):g}</td>" + "".join(
        f"<td class=\"n\">{100 * v[w]['P_visit']:.1f}%</td><td class=\"n\">{100 * v[w]['P_od']:.1f}%</td>"
        f"<td class=\"n\">{v[w]['n']:,}</td>" for w in worlds) + "</tr>"
        for k, v in sorted(tab.items(), key=lambda kv: float(kv[0])))
    head = "".join(f"<th class=\"n\">{html.escape(FG.wlabel(w))}: reached the pond</th>"
                   f"<th class=\"n\">over-drank</th><th class=\"n\">episodes</th>" for w in worlds)
    rule_ok = cal["choice"]["branch"].startswith("rule")
    rr = cal["rule"]
    branch_words = (
        f"the rule was met" if rule_ok else
        f"no start value had at most {100 * rr['P_visit_max']:g}% of episodes reaching the pond in every test "
        f"world, so the first fallback took the value whose worse world had the lowest share, among values "
        f"with at most {100 * rr['P_od_max']:g}% over-drinking deaths in every world"
        if cal["choice"]["branch"].startswith("FALLBACK 1") else
        f"no start value had at most {100 * rr['P_od_max']:g}% over-drinking deaths in every test world, so "
        f"the second fallback took the value with the lowest over-drinking risk")
    table = ('<p class="cue" hidden>&larr; scroll sideways</p><div class="scroll"><table class="wide" '
             'style="min-width:760px"><thead><tr><th class="n">start hydration</th>' + head +
             f'</tr></thead><tbody>{rows}</tbody></table></div><p>Rule outcome: '
             f'{html.escape(branch_words).replace("at most", "&le;")}. Episodes per cell pool both agents\' '
             'final checkpoints over every scene.</p>')
    at_s = "; ".join(f"{html.escape(FG.wlabel(w))}: {100 * tab[Skey][w]['P_visit']:.1f}% of "
                     f"{tab[Skey][w]['n']:,} episodes reached the pond" for w in worlds)
    calib = ((f"{float(S):g} met the rule." if rule_ok else
              f"<strong>No value met the rule</strong>, so a fallback of the rule chose {float(S):g}.")
             + f" At {float(S):g}: {at_s}. The pond sits at the same distance from the agent in every scene:")
    r = cal["rule"]
    cands = [f"{float(x):g}" for x in r["candidates"]]
    rule_txt = (f"the lowest of {', '.join(cands[:-1])} and {cands[-1]} at which at most "
                f"{100 * r['P_visit_max']:g}&nbsp;% of episodes reach the pond and at most "
                f"{100 * r['P_od_max']:g}&nbsp;% die of over-drinking, in each of the {len(worlds)} test worlds.")
    calib_title = ("Experiment-test scenes: start hydration chosen by the pre-stated rule" if rule_ok else
                   "Experiment-test scenes: start hydration chosen by a fallback of the pre-stated rule")
    wc = [c["inv"]["water_checks"] for c in D["cells"] if c["inv"].get("water_checks")]
    exc = sum(w["step_exceptions"] + w["start_cell_mismatches"] for w in wc)
    checks = (f"{sum(w['steps_checked'] for w in wc):,} steps in {sum(w['episodes_checked'] for w in wc):,} "
              f"episodes of {len(wc)} runs, {exc} exceptions")
    # endpoint: the study doc's own launch-manifest status cells (the population's source)
    M = json.load(open(population))
    src = M.get("source")
    if not isinstance(src, str):
        fail("water population: the population manifest has no study-doc source to read run statuses from")
    sys.path.insert(0, os.path.join(FG.A_DIR, "studies", "hypervigilance"))
    import make_population as MP
    status = sorted({re.sub(r"final checkpoint \d+", "final checkpoint N", r["Status"])
                     for r in MP.parse_launch_manifest(os.path.join(REG.DATA_ROOT, src))})
    cks = sorted(int(c["checkpoint"]) for c in M["cells"] if c.get("checkpoint"))
    endpoint = ("The study's launch manifest records the runs as: " +
                "; ".join(f"&ldquo;{html.escape(x)}&rdquo;" for x in status) +
                f". Every figure reads each run's store at the checkpoint in the population manifest "
                f"({cks[0]:,}&ndash;{cks[-1]:,} training episodes).")
    per = {}
    for c in D["cells"]:
        per.setdefault((c["world"], c["agent"]), []).append(c["seed"])
    nmax = max(len(v) for v in per.values())
    seeds = sorted({s for v in per.values() for s in v})
    if nmax == 1:
        runs_title = "One training run per world and agent"
        runs = (f"Each of the {len(per)} world &times; agent combinations has a single training run "
                f"(seed{'s' if len(seeds) > 1 else ''} {', '.join(map(str, seeds))}).")
        runs_short = "each world and agent has a single training run"
    else:
        runs_title = "Training runs per world and agent"
        runs = (f"World &times; agent combinations have {min(len(v) for v in per.values())}&ndash;{nmax} "
                f"training runs (seeds {', '.join(map(str, seeds))}).")
        runs_short = f"each world and agent has at most {nmax} training runs"
    refusals = []
    for t in REG.TARGETS:
        pj = os.path.join(out_root, "screen", t, "prefit.json")
        if os.path.exists(pj) and "refused" in json.load(open(pj)):
            refusals.append(json.load(open(pj))["refused"])
    prov = os.path.join(out_root, "probes", "provenance.json")
    budget = json.load(open(prov)).get("budget_refused") if os.path.exists(prov) else None
    ref = []
    if refusals:
        ref.append(f"Figure 5, because {html.escape(refusals[0])}")
    if budget:
        ref.append(f"Figure 7's seed-to-seed budget, because {html.escape(budget)}")
    ref_txt = ("; ".join(ref) + ".") if ref else "(their refusal records are not written yet)."
    ser = os.path.join(out_root, "probes", "series.csv.gz")
    ep_txt = "the recorded number of"
    if os.path.exists(ser):
        import pandas as pd
        Sx = pd.read_csv(ser)
        n = Sx[Sx.measure == "n_episodes"]["value"]
        if len(n):
            ep_txt = f"{int(n.min())}" if n.min() == n.max() else f"{int(n.min())}&ndash;{int(n.max())}"
    return {"{{W_WORLD_TABLE}}": world_table(D), "{{W_CHECKS}}": checks, "{{W_ENDPOINT}}": endpoint, "{{W_REFUSALS}}": ref_txt,
            "{{W_CALIB_S}}": f"{float(S):g}", "{{W_CALIB_TABLE}}": table, "{{W_CALIB_RESULT}}": calib, "{{W_CALIB_RULE}}": rule_txt,
            "{{W_CALIB_TITLE}}": calib_title, "{{W_RUNS_TITLE}}": runs_title, "{{W_RUNS}}": runs,
            "{{W_RUNS_SHORT}}": runs_short, "{{W_EP_PER_CKPT}}": ep_txt,
            "{{W_F7_BUDGET}}": (f"The seed-to-seed comparison is refused: {html.escape(budget)}." if budget else "")}


def build(population, out_root, page_dir):
    fig_dir = os.path.join(page_dir, "figures")
    D = FG.load_outputs(population, out_root)
    page = open(TEMPLATE).read()
    water = FG.has_water(D["cells"])
    # the hydration heat maps' axes sentence of Figure 6 (water only; empty, so unchanged, otherwise),
    # substituted before the blocks are read so the generated mirror carries it too
    page = page.replace("{{W_F6_HYD}}", (
        " Hydration heat maps, one per world and agent below the injury maps, with their own grey scale "
        "and colour bar: horizontal, nutrition one step earlier; vertical, hydration one step earlier (four "
        "bands: under 50, 50&ndash;100, 100&ndash;150, 150 and over); shade and number, the share of chosen "
        "steps in percent, except for time on the pond, where they show the share of steps off the pond one "
        "step earlier that arrive on it." if water else ""))
    if water:
        page = page.replace("<!-- WATER -->\n", "").replace("<!-- /WATER -->\n", "")
        f7w = re.search(r"<!-- BLOCK F7 -->.*?<!-- /BLOCK F7 -->", open(TEMPLATE_F7_WATER).read(), re.S).group(0)
        page = re.sub(r"<!-- BLOCK F7 -->.*?<!-- /BLOCK F7 -->", lambda _: f7w, page, flags=re.S)
    else:
        page = re.sub(r"<!-- WATER -->\n.*?<!-- /WATER -->\n", "", page, flags=re.S)
    house = open(HOUSE).read()
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    vm = re.search(r'(<div class="lb fit" id="lb".*?\n</div>)', house, re.S)
    vs = re.search(r"(\(function \(\) \{\s*// full-size figure viewer.*?\}\)\(\);)", house, re.S)
    sc = re.search(r"(function updateCues\(\).*?)</script>", house, re.S)
    if not (m and vm and vs and sc):
        fail(f"could not find the style block, viewer or cue script in {HOUSE}")
    # every file in the figure folder must belong to the F1-F7 sequence
    on_disk = sorted(os.listdir(fig_dir)) if os.path.isdir(fig_dir) else []
    stems = {}
    for f in on_disk:
        m7 = re.fullmatch(r"(f7_(?:probe|pond)_[a-z_]+?(?:__(?:hv[0-9a-z]+|g\d+))?)\.(png|svg|pdf|samples\.json)", f)
        if m7 and m7.group(1) in (F7W_STEMS if water else F7_STEMS):
            stems.setdefault(("f7_probes", m7.group(1)), set()).add(m7.group(2))
            continue
        mm = re.fullmatch(r"(f\d_[a-z_]+?)(?:__([a-z_]+))?\.(png|svg|pdf|samples\.json)", f)
        if not mm or mm.group(1) not in {v[0] for v in BLOCKS.values()} or \
                (mm.group(2) and mm.group(2) not in REG.TARGETS):
            fail(f"{fig_dir}/{f} is not part of the F1-F7 sequence")
        stems.setdefault((mm.group(1), mm.group(2)), set()).add(mm.group(3))
    blocks = blocks_of(page)
    if sorted(blocks) != sorted(BLOCKS):
        fail(f"template blocks {sorted(blocks)} != {sorted(BLOCKS)}")
    present, pending, mirror, toc = [], [], [], []
    for bid, (base, per_target) in BLOCKS.items():
        block = blocks[bid]
        if per_target is None:
            page, ok = build_f7(page, block, stems, fig_dir, out_root, mirror, toc, water)
            (present if ok else pending).append(bid)
            continue
        targets = [t for t in REG.TARGETS if (base, t) in stems] if per_target else \
            ([None] if (base, None) in stems else [])
        if not targets:
            title = re.search(r"<h2>(.*?)</h2>", block, re.S).group(1)
            title = re.sub(r"\s*&mdash;\s*\{\{TARGET_LABEL\}\}", "", title)
            refused = {}
            for t in REG.TARGETS if (water and bid == "F5") else []:
                pj = os.path.join(out_root, "screen", t, "prefit.json")
                if os.path.exists(pj) and "refused" in json.load(open(pj)):
                    refused[t] = json.load(open(pj))["refused"]
            if refused:                     # D10: refused by design, with the reason, not "pending"
                page = page.replace(block, f'<section class="col"><h2>{title}</h2><div class="bb-pending">'
                                    f'<b>Figure {bid[1]} &mdash; not drawn, by design.</b> The cross-run '
                                    f'screening needs at least two training runs per world and agent; it '
                                    f'refused for {len(refused)} behaviours ('
                                    f'{html.escape(", ".join(FG.TARGET_NOUN[t] for t in refused))}): '
                                    f'{html.escape(next(iter(refused.values())))}</div></section>')
                present.append(bid)
                continue
            page = page.replace(block, f'<section class="col"><h2>{title}</h2><div class="bb-pending">'
                                f'<b>Figure {bid[1]} &mdash; not yet produced.</b> Run '
                                f'<code>scripts/analysis/basic_behaviour/{base}.py</code>, then rebuild.'
                                f'</div></section>')
            pending.append(bid)
            continue
        parts = []
        check_block(bid, block)
        pm = re.search(r"<!-- PER -->(.*?)<!-- /PER -->", block, re.S)
        if per_target and not pm:
            fail(f"{bid}: a per-behaviour block needs <!-- PER --> ... <!-- /PER -->")
        unit = pm.group(1) if pm else block
        toc.append((bid, [(t, f"f{bid[1]}-{t}" if t else f"f{bid[1]}") for t in targets]))
        for li, t in enumerate(targets):
            stem = f"{base}__{t}" if t else base
            missing = [e for e in EXTS if e not in stems[(base, t)]]
            if missing:
                fail(f"{stem}: missing {missing} in {fig_dir}")
            if not os.path.exists(os.path.join(HERE, f"{base}.py")):
                fail(f"{stem}: no generating script {base}.py")
            b = (unit.replace("{{T}}", t or "").replace("{{L}}", "abcdefgh"[li] if t else "")
                 .replace("{{FIGID}}", f"f{bid[1]}-{t}" if t else f"f{bid[1]}")
                 .replace("{{TARGET_TITLE}}", FG.TARGET_TITLE[t] if t else "")
                 .replace("{{TARGET_NOUN}}", FG.TARGET_NOUN[t] if t else ""))
            rows = json.load(open(os.path.join(fig_dir, f"{stem}.samples.json")))
            b = b.replace(f"{{{{DATA:{stem}}}}}", data_table(stem, rows))
            cmd = (f"python scripts/analysis/basic_behaviour/{base}.py --population "
                   f"{os.path.relpath(population, REG.DATA_ROOT)} --out-root {os.path.relpath(out_root, REG.DATA_ROOT)} "
                   f"--fig-dir {os.path.relpath(fig_dir, REG.DATA_ROOT)}" + (f" --target {t}" if t else ""))
            b = b.replace(f"{{{{CMD:{stem}}}}}", html.escape(cmd))
            if t is not None and f"{{{{REASONS:{t}}}}}" in b:
                b = b.replace(f"{{{{REASONS:{t}}}}}", reasons_table(D, t))
            png = embed_png(os.path.join(fig_dir, f"{stem}.png"))
            floor = width_floor(os.path.join(fig_dir, f"{stem}.png"))
            im_tag = re.search(rf'<img data-fig="{stem}"[^>]*>', b).group(0)
            new_tag = im_tag.replace(f'<img data-fig="{stem}"', f'<img data-fig="{stem}" style="min-width:{floor}px" '
                                     f'src="data:image/png;base64,{png}"', 1)
            # register F65: a width floor so labels stay >= 9 px on a phone, inside a scroll box whose
            # cue is shown only while it really overflows (the house cue script)
            b = b.replace(im_tag, '<p class="cue" hidden>&larr; the figure is wider than the screen &mdash; '
                          'scroll it sideways, or tap it to open it full size</p><div class="scroll">'
                          + new_tag + "</div>", 1)
            fig_html = re.search(r"<figure\b.*?</figure>", b, re.S).group(0)
            mirror.append((stem, axes_sentence(fig_html), rows))
            parts.append(b)
            present.append(stem)
        page = page.replace(block, block.replace(pm.group(0), "\n".join(parts)) if pm else "\n".join(parts))
    n_ep = sum(c["inv"]["n_episodes"] for c in D["cells"])
    golden = os.path.join(REG.BB_ROOT, "_golden_pass.json")
    gtxt = (f"passed on {json.load(open(golden))['date'][:10]}" if os.path.exists(golden) else "not passed")
    tok = {"{{POPULATION}}": html.escape(D["population"]), "{{N_RUNS}}": str(len(D["cells"])),
           "{{N_EPISODES}}": f"{n_ep:,}", "{{N_PENDING}}": str(len(D["unswept"]) + len(D["not_completed"])),
           "{{RUN_TABLE}}": run_table(D), "{{MANIFEST}}": html.escape(os.path.relpath(population, REG.DATA_ROOT)),
           "{{OUT_ROOT}}": html.escape(os.path.relpath(out_root, REG.DATA_ROOT)), "{{GOLDEN}}": html.escape(gtxt),
           "{{TOC}}": toc_html(toc),
           "{{STATUS_LINE}}": ("All seven figures are present." if not pending else
                               f"Figures not yet produced: {', '.join(pending)}.")}
    if water:
        tok.update(water_tokens(D, population, out_root))
    for k, v in tok.items():
        page = page.replace(k, v)
    page = page.replace("{{HOUSE_STYLE}}", m.group(1))
    page = page.replace("{{HOUSE_VIEWER}}", vm.group(1))
    page = page.replace("{{HOUSE_SCRIPT}}", "<script>\n" + vs.group(1) + "\n" + sc.group(1) + "</script>")
    for w in set(re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page)):
        f = os.path.join(FONTS, f"Pretendard-{w}.latin.woff")
        if not os.path.exists(f):
            fail(f"font {w}: no subset at {f}")
        page = page.replace(f"{{{{FONT:{w}}}}}", base64.b64encode(open(f, "rb").read()).decode())
    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        fail(f"unsubstituted tokens remain: {sorted(set(left))}")
    if len(page.encode()) > PAGE_MAX_BYTES:
        fail(f"page would be {len(page.encode()):,} bytes, over {PAGE_MAX_BYTES:,} (artifact limit 16 MB)")
    os.makedirs(page_dir, exist_ok=True)
    open(os.path.join(page_dir, "basic_behaviour.html"), "w").write(page)
    md = [f"# Basic Behaviour Analysis — {D['population']} (generated; do not edit)", "",
          f"Generated by `scripts/analysis/basic_behaviour/build_page.py` from the same template and "
          f"data as `basic_behaviour.html`.", ""]
    for stem, ax, rows in mirror:
        md += [f"## {stem}", "", ax.replace("Axes.", "**Axes.**", 1), "",
               "| subset | used | available | share | why |", "|---|---:|---:|---:|---|"]
        md += [f"| {r['what']} | {r['used']:,} | {r['total']:,} | {r['pct']:.1f}% | {r['note']} |" for r in rows]
        md.append("")
    if pending:
        md += ["## Not yet produced", "", ", ".join(pending), ""]
    open(os.path.join(page_dir, "basic_behaviour.md"), "w").write("\n".join(md))
    print(f"{'partial' if pending else 'complete'}: present {present}, pending {pending}; "
          f"page {len(page.encode()):,} bytes")
    return present, pending


def build_f7(page, block, stems, fig_dir, out_root, mirror, toc, water=False):
    """Figure 7: every stem in F7_STEMS (F7W_STEMS for water) must be complete, or the block becomes a
    pending box."""
    STEMS, ARGS = (F7W_STEMS, F7W_ARGS) if water else (F7_STEMS, F7_ARGS)
    have = [st for st in STEMS if ("f7_probes", st) in stems]
    if not have:
        title = re.search(r"<h2>(.*?)</h2>", block, re.S).group(1)
        return page.replace(block, f'<section class="col"><h2>{title}</h2><div class="bb-pending">'
                            '<b>Figure 7 &mdash; not yet produced.</b> Run <code>scripts/analysis/basic_behaviour/'
                            'probes.py</code> then <code>f7_probes.py</code>, then rebuild.</div></section>'), False
    for st in STEMS:
        missing = [e for e in EXTS if e not in stems.get(("f7_probes", st), set())]
        if missing:
            fail(f"{st}: missing {missing} in {fig_dir} (Figure 7 is built whole or not at all)")
    if not os.path.exists(os.path.join(HERE, "f7_probes.py")):
        fail("Figure 7: no generating script f7_probes.py")
    prov = os.path.join(out_root, "probes", "provenance.json")
    if not os.path.exists(prov):
        fail(f"Figure 7: no {prov} (written by probes.py)")
    P = json.load(open(prov))
    if P.get("partial") or P.get("csv_root_override"):
        print("build_page: WARNING - Figure 7 is built from a PARTIAL / development probe summary")
    check_block("F7", block)
    b = block
    for st in STEMS:
        rows = json.load(open(os.path.join(fig_dir, f"{st}.samples.json")))
        tbl = data_table(st, rows)
        if "__" in st:                       # three trace charts share one caption: name the world
            w = {"hv2ch": "two-channel (control)", "hv1ch": "single-channel",
                 "hv1chm": "matched-strength", "g10": "10&times;10 map", "g15": "15&times;15 map",
                 "g20": "20&times;20 map"}[st.split("__")[1]]
            tbl = tbl.replace("<b>Data.</b>", f"<b>Data, {w} chart.</b>", 1)
        b = b.replace(f"{{{{DATA:{st}}}}}", tbl)
        cmd = (P["command"] + " && python scripts/analysis/basic_behaviour/f7_probes.py --out-root "
               f"{os.path.relpath(out_root, REG.DATA_ROOT)} --fig-dir {os.path.relpath(fig_dir, REG.DATA_ROOT)} {ARGS[st]}")
        b = b.replace(f"{{{{CMD:{st}}}}}", html.escape(cmd))
        png = os.path.join(fig_dir, f"{st}.png")
        im_tag = re.search(rf'<img data-fig="{st}"[^>]*>', b)
        if not im_tag:
            fail(f"Figure 7: the template has no <img data-fig=\"{st}\">")
        im_tag = im_tag.group(0)
        new_tag = im_tag.replace(f'<img data-fig="{st}"', f'<img data-fig="{st}" style="min-width:{width_floor(png)}px" '
                                 f'src="data:image/png;base64,{embed_png(png)}"', 1)
        b = b.replace(im_tag, '<p class="cue" hidden>&larr; the figure is wider than the screen &mdash; '
                      'scroll it sideways, or tap it to open it full size</p><div class="scroll">'
                      + new_tag + "</div>", 1)
        figs = re.findall(r"<figure\b.*?</figure>", b, re.S)
        fig_html = next(f for f in figs if f'data-fig="{st}"' in f)
        mirror.append((st, axes_sentence(fig_html), rows))
    toc.append(("F7", [(None, "f7a")]))
    return page.replace(block, b), True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--population", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--page-dir", required=True)
    a = ap.parse_args(argv)
    build(os.path.abspath(a.population), os.path.abspath(a.out_root), os.path.abspath(a.page_dir))


if __name__ == "__main__":
    main()
