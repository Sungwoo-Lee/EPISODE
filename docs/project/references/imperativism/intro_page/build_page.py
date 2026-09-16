#!/usr/bin/env python3
"""build_page.py - assemble the imperativism introduction page from its parts.

WHAT IT DOES. Reads `page_template.html`, pulls the House Style Sheet's `<style>` block and its
full-size figure viewer out of `house_style_sheet.template.html` (so the page cannot drift from the
house look), inlines the Pretendard subsets, embeds each figure PNG written by a `figNN_*.py` script
in this folder, substitutes each figure's data statement, resolves `{{CITE:key}}` tokens to numbered
citations and renders the reference list. The built page is never edited by hand.

Pattern copied from scripts/analysis/tutorials/loop_graph_engineering/build_page.py.

FAILS LOUDLY, rather than writing a partial page, on:
  * a figure with no generating script, or no PNG / SVG / PDF / data statement on disk;
  * a <figure> that draws its own chart (inline <svg> or <canvas>)            - guide 2.7
  * a figure caption with no <b>Axes.</b> sentence                             - guide 11a
  * a figure with no {{DATA:}} statement                                       - guide 11b
  * a figure whose "How it is drawn" block is missing or outside 150-250 words - guide 11c
  * a citation to a key not in REFS, or a REFS entry the page never cites      - guide 12c
  * a page-specific CSS class that reuses a house class name                   - register F54
  * a figure on disk the page never shows, or any token left unsubstituted.

Usage:  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/project/references/imperativism/intro_page/build_page.py
"""
from __future__ import annotations

import base64
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
os.chdir(ROOT)

TEMPLATE = f"{HERE}/page_template.html"
OUT = f"{HERE}/imperativism_intro.html"
FIGS = f"{HERE}/figures"
HOUSE = "docs/develop/active/meta/house_style_sheet.template.html"
FONTS = "assets/fonts/pretendard/subset"

READ = "Reviewed in full for this page"
NOT_READ = "Not read: named here only as it is described by the papers above"
# key -> (who, title, venue, url or None, provenance)  - guide 12d: say what is first-hand
REFS = {
    "klein2007": ("Klein, C.", "An Imperative Theory of Pain",
                  "The Journal of Philosophy 104(10): 517–532, 2007",
                  "https://doi.org/10.5840/jphil2007104104",
                  f"{READ}, from the author's own copy (manuscript pages differ from the journal's)."),
    "carruthers2018": ("Carruthers, P.", "Valence and Value",
                       "Philosophy and Phenomenological Research 97(3): 658–680, 2018",
                       "https://doi.org/10.1111/phpr.12395",
                       f"{READ}, from the published version."),
    "bh2019": ("Barlassina, L. and Hayward, M. K.",
               "More of me! Less of me!: Reflexive Imperativism about Affective Phenomenal Character",
               "Mind 128(512): 1013–1044, 2019", "https://doi.org/10.1093/mind/fzz035",
               f"{READ}, from the typeset advance-access copy with journal page numbers."),
    "barlassina2020": ("Barlassina, L.",
                       "Beyond good and bad: Reflexive imperativism, not evaluativism, explains valence",
                       "Thought: A Journal of Philosophy 9(4): 274–284, 2020",
                       "https://doi.org/10.1002/tht3.471",
                       f"{READ}, from the published version. The paper this page is built around."),
    "carruthers2023": ("Carruthers, P.", "On Valence: Imperative or Representation of Value?",
                       "The British Journal for the Philosophy of Science 74(3): 533–553, 2023",
                       "https://doi.org/10.1086/714985",
                       f"{READ}, from the author's own copy (manuscript pages differ from the journal's)."),
    "bain2013": ("Bain, D.", "What makes pains unpleasant?",
                 "Philosophical Studies 166: 69–89, 2013",
                 "https://doi.org/10.1007/s11098-012-0049-7",
                 "Not read: only its abstract, on the author's website, was seen. The PDF was behind a publisher bot check."),
    "klein2015": ("Klein, C.", "What the Body Commands: The Imperative Theory of Pain",
                  "MIT Press, 2015", "https://doi.org/10.7551/mitpress/10480.001.0001",
                  f"{NOT_READ}. Barlassina & Hayward and Carruthers read this book differently."),
    "loopy2019": ("Barlassina, L. and Hayward, M. K.",
                  "Loopy Regulations: The Motivational Profile of Affective Phenomenology",
                  "Philosophical Topics 47: 233–261, 2019", None,
                  f"{NOT_READ}. Several objections Carruthers 2023 answers are credited to it."),
    "mk2016": ("Martínez, M. and Klein, C.", "Pain signals are predominantly imperative",
               "Biology & Philosophy 31, 2016", "https://doi.org/10.1007/s10539-015-9514-y",
               f"{NOT_READ}. Suggested as the next paper to read."),
}


def fail(msg: str):
    sys.exit(f"build_page: {msg}")


def words(fragment: str) -> int:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = re.sub(r"\{\{[^}]+\}\}", " ", text)
    return len(html.unescape(text).split())


def classes(css: str) -> set[str]:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"url\([^)]*\)", "", css)
    return set(re.findall(r"\.([A-Za-z][A-Za-z0-9_-]*)", css))


def main():
    page = open(TEMPLATE).read()
    house = open(HOUSE).read()

    # ---- the house look, taken from its one source -------------------------------------------
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    v = re.search(r'(<div class="lb fit" id="lb".*?</script>)', house, re.S)
    if not (m and v):
        fail(f"could not find the style block or the figure viewer in {HOUSE}")
    own = re.search(r"\{\{HOUSE_STYLE\}\}\s*<style>(.*?)</style>", page, re.S)
    if not own:
        fail("template has no page-specific <style> block after {{HOUSE_STYLE}}")
    # register F54: a page class reusing a house name silently inherits the house declarations.
    # Descendant uses of a house class (".callout ul") are fine; a page RULE whose selector
    # STARTS with a house class is the hazard, so check the leading class of each selector.
    page_css = re.sub(r"/\*.*?\*/", "", own.group(1), flags=re.S)
    leading = set()
    for sel in re.findall(r"([^{}]+)\{", page_css):
        for part in sel.split(","):
            mm = re.match(r"\s*(?:[a-z0-9]+)?\.([A-Za-z][A-Za-z0-9_-]*)", part)
            if mm and not re.match(r"\s*:root", part):
                leading.add(mm.group(1))
    clash = leading & classes(m.group(1))
    allowed = {"callout"}      # `.callout ul` descendant rules only; checked by eye
    if clash - allowed:
        fail(f"page CSS starts a rule with a house class name (register F54): {sorted(clash - allowed)}")
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
        n = words(how.group(1)) - 4          # minus the four-word eyebrow "How it is drawn"
        if not 150 <= n <= 250:
            fail(f"{stem}: 'How it is drawn' is {n} words; guide 11c wants 150-250")
        if not os.path.exists(f"{HERE}/{stem}.py"):
            fail(f"{stem}: no generating script at {HERE}/{stem}.py")
        for ext in ("png", "svg", "pdf", "data.txt"):
            if not os.path.exists(f"{FIGS}/{stem}.{ext}"):
                fail(f"{stem}: no {ext} in {FIGS} -- run python {HERE}/{stem}.py")
        print(f"  {stem}: how-it-is-drawn {n} words")
    if not stems:
        fail("the template shows no figures")
    if len(stems) != len(set(stems)):
        fail(f"a figure is shown twice: {stems}")
    for stem in stems:
        b64 = base64.b64encode(open(f"{FIGS}/{stem}.png", "rb").read()).decode()
        page = page.replace(f'<img data-fig="{stem}"',
                            f'<img data-fig="{stem}" src="data:image/png;base64,{b64}"', 1)
        page = page.replace(f"{{{{DATA:{stem}}}}}", open(f"{FIGS}/{stem}.data.txt").read().strip())
    unused = {f[:-4] for f in os.listdir(FIGS) if f.endswith(".png")} - set(stems)
    if unused:
        fail(f"figures on disk that the page never shows: {sorted(unused)}")

    # ---- citations, numbered in order of first appearance ----------------------------------------
    # A chip must never start a line or strand the sentence's punctuation (register F50): move a
    # following . , ; : in front of the chip(s), delete the space before each chip, and put a
    # WORD JOINER in front of it.
    page = re.sub(r"((?:\s*\{\{CITE:[a-z0-9_]+\}\})+)([.,;:])", r"\2\1", page)
    page = re.sub(r"\s*(\{\{CITE:)", "⁠\\1", page)
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
    n_read = 0
    for i, key in enumerate(order, 1):
        who, title, where, url, how = REFS[key]
        n_read += how.startswith(READ)
        link = f' &middot; <a href="{url}">{html.escape(url)}</a>' if url else ""
        tag = ('<span class="rtag read">reviewed</span>' if how.startswith(READ)
               else '<span class="rtag unread">not read</span>')
        items.append(
            f'<li id="ref-{key}"><span class="rnum">{i}</span><span class="rbody">'
            f'<span>{html.escape(who)} &mdash; <strong>{html.escape(title)}</strong>&nbsp;{tag}</span>'
            f'<span class="rmeta">{html.escape(where)}{link}</span>'
            f'<span class="rprov">{html.escape(how)}</span></span></li>')
    page = page.replace("{{REFS}}", '<ol class="refs">\n' + "\n".join(items) + "\n</ol>")
    page = page.replace("{{N_REFS}}", str(len(order))).replace("{{N_READ}}", str(n_read)) \
               .replace("{{N_UNREAD}}", str(len(order) - n_read))

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
    print(f"  built {os.path.relpath(OUT, ROOT)}  ({len(page):,} chars; {len(stems)} figure, "
          f"{len(order)} references, {n_read} reviewed)")


if __name__ == "__main__":
    main()
