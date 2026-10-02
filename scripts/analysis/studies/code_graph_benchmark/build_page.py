#!/usr/bin/env python3
"""build_page.py - assemble the Code-Graph Benchmark page from its template, figures and data.

The page's style and figure viewer are taken from the House Style Sheet template at build time, so
this page cannot drift from it. Every number on the page is a {{N:key}} token computed here from the
per-run records, through the same _common functions the figures use (register F15).

FAILS LOUDLY on: a figure with no generating script, no PNG/SVG/PDF, or no data statement; a figure
drawn in the page (<svg>/<canvas> inside <figure>); a caption with no <b>Axes.</b> sentence (guide
11a); a figure with no "How it is computed" block, or one outside 150-250 words (11c); a number
token with no value; any token left unsubstituted.
"""
from __future__ import annotations

import base64
import json
import os
import re
import statistics
import sys

import _common as K

HOUSE_T = os.path.join(K.ROOT, "docs", "develop", "active", "meta", "house_style_sheet.template.html")
TEMPLATE = os.path.join(K.DOC, "code_graph_benchmark.template.html")
OUT = os.path.join(K.DOC, "code_graph_benchmark.html")
FONTS = os.path.join(K.ROOT, "assets", "fonts", "pretendard", "subset")


def fail(msg):
    sys.exit(f"build_page: {msg}")


def numbers(runs) -> dict:
    n = {"n_runs": len(runs)}
    by = {a: [d for k, d in runs.items() if k.split("-")[1] == a] for a in K.ARMS}
    for a in K.ARMS:
        r = by[a]
        n[f"correct_{a}"] = sum(d["correct"] for d in r)
        n[f"broke_{a}"] = sum(d["p2p_broken"] > 0 for d in r)
        n[f"med_wall_{a}"] = f"{statistics.median(d['wall_s'] for d in r) / 60:.1f} min"
        n[f"med_tok_{a}"] = f"{statistics.median(d['total_in'] for d in r) / 1e6:.2f} M"
    n["broke_total"] = sum(d["p2p_broken"] for d in runs.values())
    g, f = by["G"], by["F"]
    n["g_connected"] = sum(bool(d["graft_mcp_connected"]) for d in g)
    n["g_context"] = sum(d["graft_session_context_bytes"] > 0 for d in g)
    n["g_used"] = sum(d["graft_tool_calls"] + d["graft_cli_calls"] + d["graft_dir_reads"] > 0 for d in g)
    n["f_report"] = sum(d["graph_report_reads"] > 0 for d in f)
    n["f_cmd"] = sum(d["graphify_cli_calls"] > 0 for d in f)
    grading = json.load(open(os.path.join(K.DATA, "harness", "grading.json")))
    p2p = [len(grading[t]["P2P"]) for t in K.TASKS]
    n["p2p_min"], n["p2p_max"] = min(p2p), max(p2p)
    ma = statistics.median(d["wall_s"] for d in by["A"])
    mg = statistics.median(d["wall_s"] for d in g)
    n["pool_med_pct"] = f"{100 * (1 - mg / ma):.0f}"
    n["pool_mean_pct"] = f"{100 * (1 - statistics.mean(d['wall_s'] for d in g) / statistics.mean(d['wall_s'] for d in by['A'])):.0f}"
    p, lo, hi, ratios = K.paired_ratios(runs, "wall_s", "G")
    n["paired_wall_G_pct"] = f"{100 * (1 - p):.0f}"
    n["ci_wall_G"] = f"{lo:.2f}&ndash;{hi:.2f}&times;"
    n["g_faster"] = sum(r < 1 for r in ratios)
    n["n_oldprompt"] = sum("smoke" not in e["reason"] for e in K.excluded())
    log = open(os.path.join(K.DATA, "harness", "graft_build_chain.log")).read()
    first = re.search(r"deep build rc=0 (\d+)s", log)
    if not first:
        fail("cannot read the first Graft build time from graft_build_chain.log")
    n["graft_build_min"] = f"{int(first.group(1)) / 60:.0f}"
    return n


def main():
    runs = K.load_runs()
    page = open(TEMPLATE).read()
    house_t = open(HOUSE_T).read()
    style = re.search(r"<style>(.*?)</style>", house_t, re.S).group(1)
    viewer = re.search(r'(<div class="lb fit" id="lb".*</script>)', house_t, re.S).group(1)
    page = page.replace("{{HOUSE_STYLE}}", style).replace("{{HOUSE_VIEWER}}", viewer)

    for block in re.findall(r"<figure\b.*?</figure>", page, re.S):
        if re.search(r"<(svg|canvas)\b", block):
            fail("a <figure> draws its chart in the page (guide 2.7)")
        if "<b>Axes.</b>" not in block:
            fail("a figure caption has no <b>Axes.</b> sentence (guide 11a)")
        how = re.search(r'How it is computed</p>(.*?)</div>', block, re.S)
        if not how:
            fail("a figure has no 'How it is computed' block (guide 11c)")
        words = len(re.sub(r"<[^>]+>|&[a-z]+;|\{\{[^}]+\}\}", " ", how.group(1)).split())
        if not 150 <= words <= 250:
            fail(f"a 'How it is computed' block is {words} words, outside 150-250 (guide 11c)")

    stems = re.findall(r'<img data-fig="([A-Za-z0-9_]+)"', page)
    for stem in stems:
        if not os.path.exists(os.path.join(K.HERE, f"{stem}.py")):
            fail(f"{stem}: no generating script")
        for ext in ("png", "svg", "pdf", "data.txt"):
            if not os.path.exists(os.path.join(K.OUT, f"{stem}.{ext}")):
                fail(f"{stem}: no {ext} -- run python {stem}.py")
        b64 = base64.b64encode(open(os.path.join(K.OUT, f"{stem}.png"), "rb").read()).decode()
        page = page.replace(f'<img data-fig="{stem}"', f'<img data-fig="{stem}" src="data:image/png;base64,{b64}"', 1)
        page = page.replace(f"{{{{DATA:{stem}}}}}", open(os.path.join(K.OUT, f"{stem}.data.txt")).read().strip())

    nums = numbers(runs)
    for key in set(re.findall(r"\{\{N:([a-z_A-Z0-9]+)\}\}", page)):
        if key not in nums:
            fail(f"number token {key} has no computed value")
        page = page.replace(f"{{{{N:{key}}}}}", str(nums[key]))
    for weight in re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page):
        page = page.replace(f"{{{{FONT:{weight}}}}}",
                            base64.b64encode(open(os.path.join(FONTS, f"Pretendard-{weight}.latin.woff"), "rb").read()).decode())
    page = re.sub(r"<code>([^<]{1,32})</code>",
                  lambda m: "<code>" + m.group(1).replace("-", "-⁠") + "</code>", page)
    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        fail(f"unsubstituted tokens: {sorted(set(left))}")
    open(OUT, "w").write(page)
    print(f"  built {OUT} ({len(page):,} chars)")
    for k in sorted(nums):
        print(f"    {k} = {nums[k]}")


if __name__ == "__main__":
    main()
