#!/usr/bin/env python3
"""build_algorithmic_null_page.py - assemble the "What Both Agents Compute" page.

WHAT IT DOES. Reads the page template, takes the House Style Sheet's `<style>` block and its
measured-scroll-cue script from `house_style_sheet.template.html` (so the page cannot drift from the
house look), inlines the Pretendard subsets, resolves `{{CITE:key}}` tokens to numbered citations and
renders the reference list. The built page is never edited by hand.

The page is a plan: it carries no figures yet. Planned figures are described in dashed placeholder
panels, not drawn. When a figure lands it must come from a script and be embedded (guide 2.7), and
this builder must gain the figure checks from `scripts/analysis/tutorials/loop_graph_engineering/
build_page.py` (guide 11a-c) at the same time.

FAILS LOUDLY, rather than writing a partial page, on:
  * any <figure>, <svg> or <canvas> in the template (no figures until a script draws them) - guide 2.7
  * a class defined in the page's own CSS that the house block also defines           - register F54
  * a citation to a key not in REFS, or a REFS entry the page never cites             - guide 12c
  * any token left unsubstituted.
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

DOC = "docs/experiments/active/modulator_clues"
TEMPLATE = f"{DOC}/algorithmic_null.template.html"
OUT = f"{DOC}/algorithmic_null.html"
HOUSE = "docs/develop/active/meta/house_style_sheet.template.html"
FONTS = "assets/fonts/pretendard/subset"

# key -> (who, title, where and when, url, how this page used it)  - guide 12d: say what is first-hand
REFS = {
    "keramati": ("Keramati, M. and Gutkin, B.",
                 "Homeostatic reinforcement learning for integrating reward collection and physiological stability",
                 "eLife 3:e04811, 2014", "https://doi.org/10.7554/eLife.04811",
                 "Cited from prior knowledge for the idea that internal needs define what is rewarding; "
                 "mentioned in the project's TD review, not re-read for this page."),
    "perez": ("Perez, E., Strub, F., de Vries, H., Dumoulin, V. and Courville, A.",
              "FiLM: Visual Reasoning with a General Conditioning Layer",
              "AAAI 2018", "https://arxiv.org/abs/1709.07871",
              "PDF held in the project library; read through the project's per-paper review "
              "(docs/project/references/FiLM/reviews/perez_2018_film.md)."),
    "kornblith": ("Kornblith, S., Norouzi, M., Lee, H. and Hinton, G.",
                  "Similarity of Neural Network Representations Revisited",
                  "ICML 2019", "https://arxiv.org/abs/1905.00414",
                  "No PDF held; used as described in the project's representational-methods review "
                  "(docs/project/references/neural_representation_analysis/film_hypernet_representational_methods.md)."),
    "raghu": ("Raghu, M., Gilmer, J., Yosinski, J. and Sohl-Dickstein, J.",
              "SVCCA: Singular Vector Canonical Correlation Analysis for Deep Learning Dynamics and Interpretability",
              "NeurIPS 2017", "https://arxiv.org/abs/1706.05806",
              "No PDF held; cited from prior knowledge as a rescaling-robust comparison measure. "
              "Mentioned in other project reviews, not reviewed on its own."),
}


def prov(text: str) -> str:
    """Escape a provenance note, emitting any repo path as <code> so the later <wbr> pass lets it
    break at a separator rather than inside a name (format review, 2026-09-29)."""
    return re.sub(r"(docs/[^\s)]+)", r"<code>\1</code>", html.escape(text))


def fail(msg: str):
    sys.exit(f"build_algorithmic_null_page: {msg}")


def css_classes(css: str) -> set[str]:
    """Class names DEFINED in a stylesheet: selectors only, comments and declarations stripped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    selectors = re.findall(r"([^{}]+)\{", css)
    names = set()
    for sel in selectors:
        if sel.strip().startswith("@"):
            continue
        names.update(re.findall(r"\.([A-Za-z][\w-]*)", sel))
    return names


def main():
    page = open(TEMPLATE).read()
    house = open(HOUSE).read()

    if re.search(r"<(figure|svg|canvas)\b", page):
        fail("the template draws or holds a figure; figures come from scripts (guide 2.7) and "
             "this builder has no figure checks yet")

    # ---- the house look and cue script, taken from their one source ---------------------------
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    s = re.search(r"(function updateCues\(\).*?)</script>", house, re.S)
    if not (m and s):
        fail(f"could not find the style block or the cue script in {HOUSE}")
    house_css = m.group(1)

    # register F54: a page class reusing a house class name inherits every declaration it does not
    # override. Require the two definition sets to be disjoint.
    own = re.findall(r"<style>(.*?)</style>", page, re.S)
    clash = css_classes("".join(own)) & css_classes(house_css)
    if clash:
        fail(f"page CSS defines classes the house block already defines (F54): {sorted(clash)}")

    page = page.replace("{{HOUSE_STYLE}}", house_css)
    page = page.replace("{{HOUSE_SCRIPT}}", "<script>\n" + s.group(1) + "</script>")

    # ---- citations, numbered in order of first appearance ------------------------------------
    # A chip must never start a line or strand punctuation (register F50).
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
    for i, key in enumerate(order, 1):
        who, title, where, url, how = REFS[key]
        items.append(
            f'<li id="ref-{key}"><span class="rnum">{i}</span><span class="rbody">'
            f'<span>{html.escape(who)} &mdash; <strong>{html.escape(title)}</strong></span>'
            f'<span class="rmeta">{html.escape(where)} &middot; <a href="{url}">{html.escape(url)}</a></span>'
            f'<span class="rprov">{prov(how)}</span></span></li>')
    page = page.replace("{{REFS}}", '<ol class="refs">\n' + "\n".join(items) + "\n</ol>")

    # ---- fonts -------------------------------------------------------------------------------
    for weight in set(re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page)):
        f = f"{FONTS}/Pretendard-{weight}.latin.woff"
        if not os.path.exists(f):
            fail(f"font {weight}: no subset at {f}")
        page = page.replace(f"{{{{FONT:{weight}}}}}", base64.b64encode(open(f, "rb").read()).decode())

    # a short code chip must not break after its hyphens (register F49); a long path may break
    # after / or _ so a phone does not split it before its last letter.
    page = re.sub(r"<code>([^<]{1,32})</code>",
                  lambda mm: "<code>" + mm.group(1).replace("-", "-⁠") + "</code>", page)
    page = re.sub(r"<code>([^<]{33,})</code>",
                  lambda mm: "<code>" + re.sub(r"([/_])", r"\1<wbr>", mm.group(1)) + "</code>", page)

    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        fail(f"unsubstituted tokens remain: {sorted(set(left))}")

    open(OUT, "w").write(page)
    print(f"  built {OUT}  ({len(page):,} chars; {len(order)} references)")


if __name__ == "__main__":
    main()
