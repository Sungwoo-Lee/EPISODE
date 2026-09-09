#!/usr/bin/env python3
"""build_style_page.py - assemble the house-style reference page from its parts.

WHY A BUILDER. The page embeds a figure and two fonts. Pasting either by hand makes the page and
the thing it embeds two artifacts that must agree with nothing forcing them to -- and this page in
particular would then be a style document whose own specimen was drawn by hand rather than by the
style module it documents, which is the exact failure it exists to warn about.

So: `spec01_line_chart.py` draws the figure and writes SVG, PDF and PNG; this script substitutes
the SVG into the template and inlines the subset fonts; the page is never edited directly.

FAILS LOUDLY, rather than shipping something partial, on:
  * a token naming a figure with no SVG on disk;
  * a figure whose generating script is missing;
  * a font token with no subset file;
  * any token left unsubstituted;
  * a figure on disk that the page never shows;
  * a figure block with no caption.
"""
from __future__ import annotations
import base64
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
os.chdir(ROOT)

META = "docs/develop/active/meta"
TEMPLATE = f"{META}/transformer_circuits_style.template.html"
OUT = f"{META}/transformer_circuits_style.html"
FIGS = f"{META}/figures"
FONTS = "assets/fonts/pretendard/subset"
SCRIPTS = HERE


def fail(msg: str):
    sys.exit(f"build_style_page: {msg}")


def main():
    page = open(TEMPLATE).read()

    fig_tokens = re.findall(r"\{\{FIG:([A-Za-z0-9_]+)\}\}", page)
    font_tokens = re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page)
    if not fig_tokens:
        fail("the template shows no figures at all")
    if len(fig_tokens) != len(set(fig_tokens)):
        fail(f"a figure is shown twice: {fig_tokens}")

    for stem in fig_tokens:
        svg = f"{FIGS}/{stem}.svg"
        script = f"{SCRIPTS}/{stem}.py"
        if not os.path.exists(svg):
            fail(f"{stem}: no SVG at {svg} -- run python {script}")
        if not os.path.exists(script):
            fail(f"{stem}: shown on the page but no generating script at {script}")
        body = open(svg).read()
        # strip the XML prologue and DOCTYPE; an inline SVG in HTML must start at <svg
        body = body[body.index("<svg"):]
        # matplotlib writes width/height in pt; drop them so the CSS controls the size
        body = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"\sheight="[^"]*"', r"\1", body, count=1)
        page = page.replace(f"{{{{FIG:{stem}}}}}", body)

    for weight in font_tokens:
        f = f"{FONTS}/Pretendard-{weight}.latin.woff"
        if not os.path.exists(f):
            fail(f"font {weight}: no subset at {f}")
        page = page.replace(f"{{{{FONT:{weight}}}}}",
                            base64.b64encode(open(f, "rb").read()).decode())

    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        fail(f"unsubstituted tokens remain: {sorted(set(left))}")

    on_disk = {f[:-4] for f in os.listdir(FIGS) if f.endswith(".svg")}
    unused = on_disk - set(fig_tokens)
    if unused:
        fail(f"figures exist that the page never shows: {sorted(unused)} -- show them or delete them")

    for block in re.findall(r"<figure\b.*?</figure>", page, re.S):
        if "<figcaption" not in block:
            fail("a figure block has no caption")

    open(OUT, "w").write(page)
    print(f"  built {OUT}  ({len(page):,} chars)")
    print(f"  figures: {', '.join(fig_tokens)}   fonts: {', '.join(font_tokens)}")


if __name__ == "__main__":
    main()
