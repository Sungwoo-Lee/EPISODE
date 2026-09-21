#!/usr/bin/env python3
"""build_olf_page.py - assemble the neuromodulator comparison page from template + real figures.

The page's prose lives in `olf_comparison.template.html`; every figure is a file written by a
script under this directory. This builder only embeds. It draws nothing, and it computes nothing:
if a number appears on the page it was either typed into the prose deliberately or substituted from
a figure's own `.data.txt`, never derived here.

WHY A BUILDER AT ALL, when the two sibling pages in this folder are hand-authored HTML. Because
both of them have drifted: `g04_how_it_ends.png` on the published "Does the Modulator Listen
Inward?" does not match what its own script produces, and nothing caught that for a week. A page
assembled by a script fails loudly instead - a figure shown with no script, a script with no PNG, a
figure with no data statement, or a leftover token are each a hard error here.

  python scripts/analysis/studies/nmn_site_grid/build_olf_page.py
"""
from __future__ import annotations
import base64, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))     # scripts/<a>/<b>/<c>.py
os.chdir(ROOT)

DOC      = "docs/experiments/active/nmn_input_site_grid"
TEMPLATE = f"{DOC}/olf_comparison.template.html"
OUT      = f"{DOC}/olf_comparison.html"
FIGS     = f"{DOC}/figures_olf"
SCRIPTS  = HERE
FONTS    = "assets/fonts/pretendard/subset"

# Which script owns which figure. Explicit rather than derived from the filename: a figure whose
# script is renamed should break the build, not silently look for a file that is not there.
SCRIPT_FOR = {
    "n01_injury_dose_response_by_range": "olf_vs_base_dose_response",
    "n02_window_and_variable":           "olf_window_and_variable",
    "n03_hypervigilance":                "olf_hypervigilance",
    "n04_contextual_fraction":           "olf_contextual_fraction",
}


def fail(msg: str):
    sys.exit(f"build_olf_page: {msg}")


def main():
    if not os.path.exists(TEMPLATE):
        fail(f"missing template: {TEMPLATE}")
    page = open(TEMPLATE, encoding="utf-8").read()

    stems = re.findall(r'<img data-fig="([a-z0-9_]+)"', page)
    if not stems:
        fail("the template shows no figures at all")
    if len(stems) != len(set(stems)):
        fail(f"a figure is shown twice: {stems}")

    for stem in stems:
        if stem not in SCRIPT_FOR:
            fail(f"{stem}: shown on the page but not in SCRIPT_FOR, so no script owns it")
        script = f"{SCRIPTS}/{SCRIPT_FOR[stem]}.py"
        if not os.path.exists(script):
            fail(f"{stem}: shown on the page but no generating script at {script}")
        for ext in ("png", "svg", "pdf"):
            if not os.path.exists(f"{FIGS}/{stem}.{ext}"):
                fail(f"{stem}: no {ext} at {FIGS}/{stem}.{ext} -- run python {script}")
        b64 = base64.b64encode(open(f"{FIGS}/{stem}.png", "rb").read()).decode()
        page = page.replace(f'<img data-fig="{stem}"',
                            f'<img data-fig="{stem}" src="data:image/png;base64,{b64}"', 1)
        if f"{{{{DATA:{stem}}}}}" not in page:
            fail(f"{stem}: the page shows the figure but never states how much data it used")
        data = f"{FIGS}/{stem}.data.txt"
        if not os.path.exists(data):
            fail(f"{stem}: no data statement at {data} -- run python {script}")
        page = page.replace(f"{{{{DATA:{stem}}}}}", open(data, encoding="utf-8").read().strip())

    for weight in re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page):
        f = f"{FONTS}/Pretendard-{weight}.latin.woff"
        if not os.path.exists(f):
            fail(f"font {weight}: no subset at {f}")
        page = page.replace(f"{{{{FONT:{weight}}}}}",
                            base64.b64encode(open(f, "rb").read()).decode())

    # Keep a short code chip whole: hyphen-minus is a native line-break opportunity, so `t1none`
    # is safe but `--accent` would break after its hyphens at a line end.
    page = re.sub(r"<code>([^<]{1,32})</code>",
                  lambda m: "<code>" + m.group(1).replace("-", "-⁠") + "</code>", page)

    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        fail(f"unsubstituted tokens remain: {sorted(set(left))}")
    if re.search(r"<figure\b[^>]*>(?:(?!</figure>).)*<(?:svg|canvas)\b", page, re.S):
        fail("a <figure> contains an <svg> or <canvas>: figures come from scripts (guide 2.7)")
    for stem in stems:
        blk = re.search(rf'<img data-fig="{stem}".*?</figure>', page, re.S)
        if not blk or "How it is computed" not in blk.group(0):
            fail(f"{stem}: no 'How it is computed' block")
        if "<b>Axes" not in blk.group(0):
            fail(f"{stem}: its caption does not state its axes")

    open(OUT, "w", encoding="utf-8").write(page)
    mb = len(page.encode()) / 1e6
    print(f"written: {OUT}  ({mb:.2f} MB)")
    print(f"figures embedded: {len(stems)}/{len(stems)}   "
          f"every figure names a script, states its axes and declares its data")
    if mb > 16:
        fail(f"{mb:.1f} MB exceeds the 16 MB artifact limit")


if __name__ == "__main__":
    main()
