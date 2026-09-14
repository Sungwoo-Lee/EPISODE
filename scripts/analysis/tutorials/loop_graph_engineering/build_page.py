#!/usr/bin/env python3
"""build_page.py - assemble the "Loop and Graph Engineering" tutorial page.

WHAT IT DOES. Reads the page template, pulls the House Style Sheet's `<style>` block and its
full-size figure viewer out of `house_style_sheet.template.html` (so this page cannot drift from the
house look), inlines the Pretendard subsets, embeds each figure PNG written by an `lgNN_*.py`
script, substitutes each figure's data statement, resolves `{{CITE:key}}` tokens to numbered
citations and renders the reference list. The built page is never edited by hand.

FAILS LOUDLY, rather than writing a partial page, on:
  * a figure with no generating script, or no PNG / SVG / PDF / data statement on disk;
  * a <figure> that draws its own chart (inline <svg> or <canvas>)            - guide 2.7
  * a figure caption with no <b>Axes.</b> sentence                             - guide 11a
  * a figure with no {{DATA:}} statement                                       - guide 11b
  * a figure whose "How it is drawn" block is missing or outside 150-250 words - guide 11c
  * a citation to a key not in REFS, or a REFS entry the page never cites      - guide 12c
  * a figure on disk the page never shows, or any token left unsubstituted.
"""
from __future__ import annotations

import base64
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
os.chdir(ROOT)

DOC = "docs/project/tutorials/loop_and_graph_engineering"
TEMPLATE = f"{DOC}/loop_and_graph_engineering.template.html"
OUT = f"{DOC}/loop_and_graph_engineering.html"
FIGS = f"{DOC}/figures"
HOUSE = "docs/develop/active/meta/house_style_sheet.template.html"
FONTS = "assets/fonts/pretendard/subset"

# key -> (who, title, where and when, url, how this page read it)  - guide 12d: say what is first-hand
FETCHED = "Web page read on 2026-09-14 through a summarising fetch, not read in full."
REFS = {
    "feng": ("Feng, Y., Xiang, Z., Yang, C., et al. (35 authors)",
             "Graph Engineering in the Era of LLM Agents: From Individual Intelligence to System Intelligence",
             "arXiv preprint 2608.21156, August 2026 (not peer reviewed)",
             "https://arxiv.org/abs/2608.21156",
             "Abstract page and HTML full text read on 2026-09-14 through a summarising fetch; quotations "
             "are as that fetch returned them, not checked against the PDF."),
    "osmani": ("Osmani, A.", "Loop Engineering", "addyosmani.com, 7 June 2026",
               "https://addyosmani.com/blog/loop-engineering/", FETCHED),
    "macedo": ("Macedo, S.",
               "Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting",
               "arXiv preprint 2607.00038, June 2026 (not peer reviewed)",
               "https://arxiv.org/abs/2607.00038",
               "Abstract page only, read on 2026-09-14 through a summarising fetch; the body was not read."),
    "ibm": ("Belcic, I. and Stryker, C.", "What Is Loop Engineering?", "IBM Think, 17 July 2026",
            "https://www.ibm.com/think/topics/loop-engineering", FETCHED),
    "huntley": ("Huntley, G.", "Ralph Wiggum as a “software engineer”", "ghuntley.com, 14 July 2025",
                "https://ghuntley.com/ralph/", FETCHED),
    "react": ("Yao, S., Zhao, J., Yu, D., et al.",
              "ReAct: Synergizing Reasoning and Acting in Language Models",
              "arXiv 2210.03629, 2022; ICLR 2023",
              "https://arxiv.org/abs/2210.03629",
              "Cited from prior knowledge of the paper; not re-read for this page."),
}


def fail(msg: str):
    sys.exit(f"build_page: {msg}")


def words(fragment: str) -> int:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = re.sub(r"\{\{[^}]+\}\}", " ", text)
    return len(html.unescape(text).split())


def main():
    page = open(TEMPLATE).read()
    house = open(HOUSE).read()

    # ---- the house look, taken from its one source -------------------------------------------
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    v = re.search(r'(<div class="lb fit" id="lb".*?</script>)', house, re.S)
    if not (m and v):
        fail(f"could not find the style block or the figure viewer in {HOUSE}")
    page = page.replace("{{HOUSE_STYLE}}", m.group(1)).replace("{{HOUSE_VIEWER}}", v.group(1))

    # ---- figures: one block at a time, never a pattern spanning two (register F16) ------------
    blocks = re.findall(r"<figure\b.*?</figure>", page, re.S)
    stems = []
    for block in blocks:
        s = re.search(r'<img data-fig="([A-Za-z0-9_]+)"', block)
        if not s:
            fail("a <figure> holds no <img data-fig>")
        stem = s.group(1)
        stems.append(stem)
        if re.search(r"<(svg|canvas)\b", block):
            fail(f"{stem}: the figure is drawn in the page -- write it from a script (guide 2.7)")
        cap = re.search(r"<figcaption>.*?</figcaption>", block, re.S)
        if not cap or "<b>Axes.</b>" not in cap.group(0):
            fail(f"{stem}: caption has no <b>Axes.</b> sentence (guide 11a)")
        if f"{{{{DATA:{stem}}}}}" not in block:
            fail(f"{stem}: no data-used statement token (guide 11b)")
        how = re.search(r'<div class="howto">(.*?)</div>', block, re.S)
        if not how:
            fail(f"{stem}: no 'How it is drawn' block (guide 11c)")
        n = words(how.group(1)) - 3          # minus the three-word eyebrow
        if not 150 <= n <= 250:
            fail(f"{stem}: 'How it is drawn' is {n} words; guide 11c wants 150-250")
        if not os.path.exists(f"{HERE}/{stem}.py"):
            fail(f"{stem}: no generating script at {HERE}/{stem}.py")
        for ext in ("png", "svg", "pdf", "data.txt"):
            if not os.path.exists(f"{FIGS}/{stem}.{ext}"):
                fail(f"{stem}: no {ext} at {FIGS} -- run python {HERE}/{stem}.py")
        print(f"  {stem}: how-it-is-drawn {n} words")
    if len(stems) != len(set(stems)):
        fail(f"a figure is shown twice: {stems}")
    for stem in stems:
        b64 = base64.b64encode(open(f"{FIGS}/{stem}.png", "rb").read()).decode()
        page = page.replace(f'<img data-fig="{stem}"', f'<img data-fig="{stem}" src="data:image/png;base64,{b64}"', 1)
        page = page.replace(f"{{{{DATA:{stem}}}}}", open(f"{FIGS}/{stem}.data.txt").read().strip())
    unused = {f[:-4] for f in os.listdir(FIGS) if f.endswith(".png")} - set(stems)
    if unused:
        fail(f"figures on disk that the page never shows: {sorted(unused)}")

    # ---- citations, numbered in order of first appearance ----------------------------------------
    # A chip must never start a line or strand the sentence's punctuation (register F50): move a
    # following . , ; : in front of the chip(s), then delete the breakable space before each chip -
    # the chip's own left margin supplies the gap.
    page = re.sub(r"((?:\s*\{\{CITE:[a-z0-9_]+\}\})+)([.,;:])", r"\2\1", page)
    page = re.sub(r"\s*(\{\{CITE:)", "⁠\\1", page)   # WORD JOINER: no break before the chip either
    order = []
    for key in re.findall(r"\{\{CITE:([a-z0-9_]+)\}\}", page):
        if key not in REFS:
            fail(f"citation to unknown source '{key}'")
        if key not in order:
            order.append(key)
    uncited = set(REFS) - set(order)
    if uncited:
        fail(f"reference list carries sources the page never cites: {sorted(uncited)}")
    for i, key in enumerate(order, 1):
        page = page.replace(f"{{{{CITE:{key}}}}}", f'<a class="cite" href="#ref-{key}">{i}</a>')
    items = []
    for i, key in enumerate(order, 1):
        who, title, where, url, how = REFS[key]
        items.append(
            f'<li id="ref-{key}"><span class="rnum">{i}</span><span class="rbody">'
            f'<span>{html.escape(who)} &mdash; <strong>{html.escape(title)}</strong></span>'
            f'<span class="rmeta">{html.escape(where)} &middot; <a href="{url}">{html.escape(url)}</a></span>'
            f'<span class="rprov">{html.escape(how)}</span></span></li>')
    page = page.replace("{{REFS}}", '<ol class="refs">\n' + "\n".join(items) + "\n</ol>")

    # ---- fonts -------------------------------------------------------------------------------
    for weight in set(re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page)):
        f = f"{FONTS}/Pretendard-{weight}.latin.woff"
        if not os.path.exists(f):
            fail(f"font {weight}: no subset at {f}")
        page = page.replace(f"{{{{FONT:{weight}}}}}", base64.b64encode(open(f, "rb").read()).decode())

    # a short code chip must not break after its hyphens at a line end (register F49)
    page = re.sub(r"<code>([^<]{1,32})</code>",
                  lambda mm: "<code>" + mm.group(1).replace("-", "-⁠") + "</code>", page)
    # a long path chip may break after / or _, so a phone does not split it before its last letter
    page = re.sub(r"<code>([^<]{33,})</code>",
                  lambda mm: "<code>" + re.sub(r"([/_])", r"\1<wbr>", mm.group(1)) + "</code>", page)

    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        fail(f"unsubstituted tokens remain: {sorted(set(left))}")

    open(OUT, "w").write(page)
    print(f"  built {OUT}  ({len(page):,} chars; {len(stems)} figures, {len(order)} references)")


if __name__ == "__main__":
    main()
