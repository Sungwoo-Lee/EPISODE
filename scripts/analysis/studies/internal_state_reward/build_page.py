"""Assemble the internal-state reward page: house chrome + script-drawn figures.

The builder EMBEDS, it never draws (guide 2.7). It fails rather than shipping a partial page:
a figure with no script, a missing raster/vector/data statement, a caption with no axes
sentence, a figure with no method block, any <svg>/<canvas> inside a <figure>, or any
unsubstituted token is a build error.
"""
import base64, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
# LIFT FROM THE BUILT SHEET, NOT THE TEMPLATE. The template's @font-face src is
# url(data:font/woff;base64,{{FONT:Regular}}); a {{...}} inside a CSS url() is an invalid URL
# that CSS discards SILENTLY, so the page renders in the system fallback and nothing errors
# except two console lines nobody reads. Proposed register entry F60.
HOUSE = os.path.join(ROOT, "docs/develop/active/meta/house_style_sheet.html")
HERE = os.path.join(ROOT, "docs/experiments/active/internal_state_reward")
TPL = os.path.join(HERE, "internal_state_reward.template.html")
OUT = os.path.join(HERE, "internal_state_reward.html")
FIGS = os.path.join(HERE, "figures")
SCRIPTS = os.path.join(ROOT, "scripts/analysis/studies/internal_state_reward")

fail = []


def die():
    if fail:
        for f in fail:
            print("  BUILD FAILURE:", f)
        sys.exit(1)


house = open(HOUSE).read()
style = re.search(r"<style>.*?</style>", house, re.S)
script = re.search(r"<script>.*?</script>", house, re.S)
viewer = re.search(r'<div class="lb fit" id="lb".*?\n</div>', house, re.S)
if not (style and script and viewer):
    fail.append("could not lift the house <style>, viewer markup and <script> from "
                f"{os.path.relpath(HOUSE, ROOT)} - the template's shape changed")
    die()

page = open(TPL).read()
page = page.replace("__HOUSE_STYLE__", style.group(0))
# The viewer SCRIPT is useless without the viewer MARKUP it reaches by id: copying one without
# the other is register F57, where every getElementById returned null and the whole script block
# died at load while four figures still advertised "click to view full size".
page = page.replace("__HOUSE_SCRIPT__", viewer.group(0) + "\n" + script.group(0))

stems = re.findall(r'<img data-fig="([^"]+)"', page)
if not stems:
    fail.append("no <img data-fig=...> in the template")

for stem in stems:
    for ext in ("png", "svg", "pdf"):
        if not os.path.exists(os.path.join(FIGS, f"{stem}.{ext}")):
            fail.append(f"{stem}: no .{ext} - run its script")
    if not os.path.exists(os.path.join(SCRIPTS, f"{stem}.py")):
        fail.append(f"{stem}: no generating script at scripts/.../{stem}.py")
    data = os.path.join(FIGS, f"{stem}.data.txt")
    if not os.path.exists(data):
        fail.append(f"{stem}: no .data.txt - the script must call record_samples()")
        continue
    rows = [l.rstrip("\n").split("|") for l in open(data) if l.strip()]
    cells = "".join(
        f"<tr><td>{w}</td><td>{u}</td><td>{t}</td><td>{p}%</td><td>{n}</td></tr>"
        for w, u, t, p, n in rows)
    # The five-column shape overflows a phone column by ~220px. The house carries .scroll,
    # .cue and table.wide for exactly this, and its updateCues() script is already on the page.
    block = ('<span><b>Data.</b> How much this figure used, emitted by its own script:</span>'
             '<p class="cue" hidden>&larr; the table is wider than the screen &mdash; scroll it sideways</p>'
             '<div class="scroll"><table class="wide">'
             '<thead><tr><th>what</th><th>used</th><th>available</th><th>share</th>'
             f'<th>why</th></tr></thead><tbody>{cells}</tbody></table></div>'
             f'<p class="prov">Drawn by <code>scripts/analysis/studies/internal_state_reward/'
             f'{stem}.py</code> &rarr; <code>figures/{stem}.{{svg,pdf,png,data.txt}}</code></p>')
    page = page.replace(f"__DATA_{stem}__", block)
    page = page.replace(
        f'<img data-fig="{stem}"',
        '<img data-fig="{}" src="data:image/png;base64,{}"'.format(
            stem, base64.b64encode(open(os.path.join(FIGS, f"{stem}.png"), "rb").read()).decode()),
        1)

# Per-figure checks, sliced element by element so a greedy pattern cannot reach into the next
# <figure> and check it twice while leaving one unchecked (the trap recorded in guide 11).
for m in re.finditer(r"<figure>.*?</figure>", page, re.S):
    f = m.group(0)
    stem = (re.search(r'data-fig="([^"]+)"', f) or [None, "?"])[1]
    if "<b>Axes.</b>" not in f:
        fail.append(f"{stem}: caption has no <b>Axes.</b> sentence (guide 11a)")
    if "<b>Data.</b>" not in f:
        fail.append(f"{stem}: no used/available block (guide 11b)")
    if "How it is computed" not in f:
        fail.append(f"{stem}: no 'How it is computed' block (guide 11c)")
    else:
        body = re.sub(r"<[^>]+>", " ", f.split("How it is computed", 1)[1])
        n = len(body.split())
        if not (150 <= n <= 320):
            fail.append(f"{stem}: method block is {n} words, wanted 150-320 (guide 11c)")
    if re.search(r"<svg|<canvas", f):
        fail.append(f"{stem}: a <figure> contains vector art drawn in the page (guide 2.7)")
    if 'class="zoomhint"' not in f:
        fail.append(f"{stem}: no click-to-open hint (guide 2.6)")
    if "does <em>not</em> show" not in f:
        fail.append(f"{stem}: method block never says what the figure does NOT show (guide 11c)")

# A cue emitted without its text passes every "present iff overflow" check while telling the
# reader nothing at all -- the table is still cut off and the line that should say so is blank.
for cue in re.findall(r'<p class="cue"[^>]*>(.*?)</p>', page, re.S):
    if not re.sub(r"<[^>]+>|&[a-z]+;|\s", "", cue):
        fail.append("an empty <p class=\"cue\">: emit the house text, not a blank shell")
# A cue measures its NEXT SIBLING, so that sibling must be the element that actually scrolls.
# A <pre> has its own overflow-x from the house sheet, so wrapping one in .scroll gives the cue
# a box that can never overflow while the <pre> inside it is visibly cut.
for m in re.finditer(r'<p class="cue"[^>]*>.*?</p>\s*(<[a-z]+)([^>]*)>', page, re.S):
    tag, attrs = m.group(1), m.group(2)
    if tag == "<div" and "scroll" in attrs:
        seg = page[m.end():m.end() + 400]
        if seg.lstrip().startswith("<pre"):
            fail.append("a cue's next sibling is a .scroll wrapping a <pre>: the <pre> scrolls, "
                        "the wrapper does not, so the cue is bound to the wrong box")
    elif tag not in ("<div", "<pre"):
        fail.append(f"a cue's next sibling is {tag}>, which is not a scroll container")

# .wrap's 52px gap only reaches the sections if they are its DIRECT children; a <main> between
# them is display:block and swallows it, leaving every section touching.
if re.search(r'<div class="wrap">\s*<main', page):
    fail.append("a <main> sits between .wrap and the sections, so .wrap's section gap lands on it")
for tok in re.findall(r"__[A-Z0-9_]+__", page):
    fail.append(f"unsubstituted token {tok}")
# Both token dialects, because the house sheet uses {{...}} and this page uses __...__, and the
# first build shipped every font as a {{FONT:...}} placeholder while every __TOKEN__ check passed.
for tok in sorted(set(re.findall(r"\{\{[A-Za-z0-9_:]+\}\}", page))):
    fail.append(f"unsubstituted house token {tok} - lift from the BUILT sheet, not the template")
if "data:font" not in page:
    fail.append("no embedded font in the page: the house head did not carry its @font-face data")
for i, sec in enumerate(re.findall(r"<section[^>]*>", page), 1):
    if 'class="col"' not in sec:
        fail.append(f"section {i} ({sec}) lacks class=\"col\": the house resets element margins "
                    f"and expresses ALL vertical rhythm through .col/.wrap flex gap, so a bare "
                    f"<section> collapses every paragraph and heading gap to 0px")
die()

open(OUT, "w").write(page)
print(f"  wrote {os.path.relpath(OUT, ROOT)}  ({len(page)/1e6:.2f} MB, {len(stems)} figures)")
