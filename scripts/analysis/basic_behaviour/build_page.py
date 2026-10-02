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
of the F1-F6 sequence; a caption without <b>Axes.</b>; a block without "How it is computed" or with
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
BLOCKS = {"F1": ("f1_behaviours_survival", False), "F2": ("f2_factor_inventory", True),
          "F3": ("f3_univariate", True), "F4": ("f4_multivariate", True),
          "F5": ("f5_settings", True), "F6": ("f6_crosstabs", True)}
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
    span = (f"{min(pcts):.0f}%" if min(pcts) == max(pcts) else f"{min(pcts):.0f}&ndash;{max(pcts):.0f}%") if pcts else "n/a"
    summary = (f"<b>Data.</b> {len(merged)} subset{'s' if len(merged) != 1 else ''} "
               f"({len(rows)} rows before merging identical ones), using {span} of what was available "
               f"&mdash; open for the counts, emitted by the figure script")
    return (f'<details class="bb-data"><summary>{summary}</summary>'
            '<p class="cue" hidden>&larr; wider than the screen &mdash; scroll it sideways</p>'
            '<div class="scroll"><table class="wide" style="min-width:720px"><thead><tr><th>subset</th><th class="n">used</th>'
            '<th class="n">available</th><th class="n">share</th><th>why</th></tr></thead><tbody>'
            + "".join(out) + "</tbody></table></div></details>")


TOC_TITLE = {"F1": "Behaviours and survival, per run", "F2": "Which features each run's analysis uses",
             "F3": "Each feature on its own, per run", "F4": "The features fitted together, per run",
             "F5": "Which settings move each behaviour (screening)",
             "F6": "By state, rabbit smell and nearby animals"}
LABEL_PX = FG.H.FS_LABEL * 220 / 72          # smallest label on every figure canvas (house.apply: 220 dpi)


def width_floor(png_path):
    """Display width at which the smallest label is 9 px (register F65)."""
    from PIL import Image
    import math
    return math.ceil(Image.open(png_path).width * 9 / LABEL_PX)


def toc_html(toc):
    items = []
    for bid, figs in toc:
        if len(figs) == 1 and figs[0][0] is None:
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


def build(population, out_root, page_dir):
    fig_dir = os.path.join(page_dir, "figures")
    D = FG.load_outputs(population, out_root)
    page = open(TEMPLATE).read()
    house = open(HOUSE).read()
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    vm = re.search(r'(<div class="lb fit" id="lb".*?\n</div>)', house, re.S)
    vs = re.search(r"(\(function \(\) \{\s*// full-size figure viewer.*?\}\)\(\);)", house, re.S)
    sc = re.search(r"(function updateCues\(\).*?)</script>", house, re.S)
    if not (m and vm and vs and sc):
        fail(f"could not find the style block, viewer or cue script in {HOUSE}")
    # every file in the figure folder must belong to the F1-F6 sequence
    on_disk = sorted(os.listdir(fig_dir)) if os.path.isdir(fig_dir) else []
    stems = {}
    for f in on_disk:
        mm = re.fullmatch(r"(f\d_[a-z_]+?)(?:__([a-z_]+))?\.(png|svg|pdf|samples\.json)", f)
        if not mm or mm.group(1) not in {v[0] for v in BLOCKS.values()} or \
                (mm.group(2) and mm.group(2) not in REG.TARGETS):
            fail(f"{fig_dir}/{f} is not part of the F1-F6 sequence")
        stems.setdefault((mm.group(1), mm.group(2)), set()).add(mm.group(3))
    blocks = blocks_of(page)
    if sorted(blocks) != sorted(BLOCKS):
        fail(f"template blocks {sorted(blocks)} != {sorted(BLOCKS)}")
    present, pending, mirror, toc = [], [], [], []
    for bid, (base, per_target) in BLOCKS.items():
        block = blocks[bid]
        targets = [t for t in REG.TARGETS if (base, t) in stems] if per_target else \
            ([None] if (base, None) in stems else [])
        if not targets:
            title = re.search(r"<h2>(.*?)</h2>", block, re.S).group(1)
            title = re.sub(r"\s*&mdash;\s*\{\{TARGET_LABEL\}\}", "", title)
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
                   f"{os.path.relpath(population, ROOT)} --out-root {os.path.relpath(out_root, ROOT)} "
                   f"--fig-dir {os.path.relpath(fig_dir, ROOT)}" + (f" --target {t}" if t else ""))
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
    golden = os.path.join(FG.ROOT, "results/analysis/basic_behaviour/_golden_pass.json")
    gtxt = (f"passed on {json.load(open(golden))['date'][:10]}" if os.path.exists(golden) else "not passed")
    tok = {"{{POPULATION}}": html.escape(D["population"]), "{{N_RUNS}}": str(len(D["cells"])),
           "{{N_EPISODES}}": f"{n_ep:,}", "{{N_PENDING}}": str(len(D["unswept"]) + len(D["not_completed"])),
           "{{RUN_TABLE}}": run_table(D), "{{MANIFEST}}": html.escape(os.path.relpath(population, ROOT)),
           "{{OUT_ROOT}}": html.escape(os.path.relpath(out_root, ROOT)), "{{GOLDEN}}": html.escape(gtxt),
           "{{TOC}}": toc_html(toc),
           "{{STATUS_LINE}}": ("All six figures are present." if not pending else
                               f"Figures not yet produced: {', '.join(pending)}.")}
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--population", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--page-dir", required=True)
    a = ap.parse_args(argv)
    build(os.path.abspath(a.population), os.path.abspath(a.out_root), os.path.abspath(a.page_dir))


if __name__ == "__main__":
    main()
