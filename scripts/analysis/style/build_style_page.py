#!/usr/bin/env python3
"""build_style_page.py - assemble the House Style Sheet page from its parts.

WHY A BUILDER. The page embeds a figure and two fonts. Pasting either by hand makes the page and
the thing it embeds two artifacts that must agree with nothing forcing them to -- and this page in
particular would then be a style document whose own specimen was drawn by hand rather than by the
style module it documents, which is the exact failure it exists to warn about.

So: `spec01_line_chart.py` draws the figure and writes SVG, PDF, PNG and a one-line statement of
the data it used; this script substitutes the SVG and that statement into the template and inlines
the subset fonts; the page is never edited directly.

FAILS LOUDLY, rather than shipping something partial, on:
  * a token naming a figure with no SVG on disk;
  * a figure whose generating script is missing;
  * a font token with no subset file;
  * any token left unsubstituted;
  * a figure on disk that the page never shows;
  * a figure block with no caption;
  * a figure with no data-used statement from its script (artifact guide 11b - never typed by hand).
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
TEMPLATE = f"{META}/house_style_sheet.template.html"
OUT = f"{META}/house_style_sheet.html"
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
        data = f"{FIGS}/{stem}.data.txt"
        if f"{{{{DATA:{stem}}}}}" not in page:
            fail(f"{stem}: the page shows the figure but never states how much data it used")
        if not os.path.exists(data):
            fail(f"{stem}: no data statement at {data} -- run python {script}")
        page = page.replace(f"{{{{DATA:{stem}}}}}", open(data).read().strip())

    for weight in font_tokens:
        f = f"{FONTS}/Pretendard-{weight}.latin.woff"
        if not os.path.exists(f):
            fail(f"font {weight}: no subset at {f}")
        page = page.replace(f"{{{{FONT:{weight}}}}}",
                            base64.b64encode(open(f, "rb").read()).decode())

    # A short inline code chip such as `--accent` would otherwise break after its hyphens at a line
    # end, since hyphen-minus is a native break opportunity. A WORD JOINER after each hyphen keeps
    # the chip whole; long path-like chips are left alone so they can still wrap.
    page = re.sub(r"<code>([^<]{1,32})</code>",
                  lambda m: "<code>" + m.group(1).replace("-", "-\u2060") + "</code>", page)

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
