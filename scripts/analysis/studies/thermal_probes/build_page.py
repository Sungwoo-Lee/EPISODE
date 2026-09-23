"""Assemble the thermal-probe page: house chrome + script-drawn figures.

The builder EMBEDS, it never draws (guide 2.7). It fails rather than shipping a partial page: a
figure with no script, a missing raster or data statement, a caption with no axes sentence, a figure
with no method block, a method block that never says what the figure does NOT show, any vector art
drawn inside a <figure>, figure numbers out of document order, or any unsubstituted token.
"""
import base64, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
# LIFT FROM THE BUILT SHEET, NOT THE TEMPLATE. The template's @font-face src is
# url(data:font/woff;base64,{{FONT:Regular}}), and a {{...}} inside a CSS url() is an invalid URL
# that CSS discards SILENTLY -- the page then renders in the system fallback with no error anywhere.
HOUSE = os.path.join(ROOT, "docs/develop/active/meta/house_style_sheet.html")
HERE = os.path.join(ROOT, "docs/experiments/active/behavior_measures")
TPL = os.path.join(HERE, "thermal_probe_hiding.template.html")
OUT = os.path.join(HERE, "thermal_probe_hiding.html")
FIGS = os.path.join(HERE, "figures")
SCRIPTS = os.path.dirname(os.path.abspath(__file__))

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
    fail.append("could not lift the house <style>, viewer markup and <script> from the built sheet")
    die()

page = open(TPL).read()
page = page.replace("__HOUSE_STYLE__", style.group(0))
# The viewer SCRIPT is useless without the viewer MARKUP it reaches by id (register F57).
page = page.replace("__HOUSE_SCRIPT__", viewer.group(0) + "\n" + script.group(0))

# --- data-accounting blocks, read from what each figure script EMITTED (guide 11b) ----------
for stem in sorted({m for m in re.findall(r'data-fig="([^"]+)"', page)}):
    df = os.path.join(FIGS, f"{stem}.data.txt")
    if not os.path.exists(df):
        fail.append(f"{stem}: no {stem}.data.txt - the figure script did not record its samples")
        continue
    rows = [l.rstrip("\n").split("|") for l in open(df) if l.strip()]
    # td.n right-aligns and sets the counts in the mono face (house sheet); the "why" column holds
    # full sentences, so the whole table needs the house scroll box, a declared floor and an
    # overflow cue, or its min-content width pushes the entire page sideways on a phone.
    cells = "".join(
        f'<tr><td>{w}</td><td class="n">{u}</td><td class="n">{t}</td>'
        f'<td class="n">{p}%</td><td>{n}</td></tr>'
        for w, u, t, p, n in rows)
    block = ('<span><b>Data.</b> How much this figure used, emitted by its own script:</span>'
             '<p class="cue" hidden>Scroll the table sideways to see every column.</p>'
             '<div class="scroll"><table class="datatable"><thead><tr><th>subset</th>'
             '<th class="n">used</th><th class="n">available</th><th class="n">share</th>'
             f'<th>why</th></tr></thead><tbody>{cells}</tbody></table></div>')
    page = page.replace(f"__DATA:{stem}__", block)

# --- embed each raster by its key, never by position (guide: match by data-fig) --------------
for stem in sorted({m for m in re.findall(r'data-fig="([^"]+)"', page)}):
    png = os.path.join(FIGS, f"{stem}.png")
    if not os.path.exists(png):
        fail.append(f"{stem}: {stem}.png is missing - run its figure script")
        continue
    if not os.path.exists(os.path.join(SCRIPTS, f"{stem}.py")):
        fail.append(f"{stem}: no generating script {stem}.py (guide 5)")
    if not os.path.exists(os.path.join(FIGS, f"{stem}.svg")):
        fail.append(f"{stem}: no vector companion {stem}.svg")
    b64 = base64.b64encode(open(png, "rb").read()).decode()
    page = re.sub(rf'(<img data-fig="{re.escape(stem)}")',
                  rf'\1 src="data:image/png;base64,{b64}"', page, count=1)

# --- per-figure checks, sliced element by element so a greedy pattern cannot skip one --------
seen_nums = []
for m in re.finditer(r"<figure>.*?</figure>", page, re.S):
    blk = m.group(0)
    # Prose wraps across lines, so every phrase check runs on a whitespace-collapsed copy.
    # Checking the raw block instead reports a missing "does not show" for a caption that says
    # exactly that, with a newline between the two words.
    flat = re.sub(r"\s+", " ", blk)
    sm = re.search(r'data-fig="([^"]+)"', blk)
    stem = sm.group(1) if sm else "<figure with no data-fig>"
    if "src=\"data:image/png;base64," not in blk:
        fail.append(f"{stem}: raster never embedded")
    if "<b>Axes.</b>" not in flat:
        fail.append(f"{stem}: caption has no <b>Axes.</b> sentence (guide 11a)")
    if "<b>Data.</b>" not in flat:
        fail.append(f"{stem}: no data-accounting block (guide 11b)")
    if "<b>How it is computed.</b>" not in flat:
        fail.append(f"{stem}: no method block (guide 11c)")
    elif "does not show" not in flat:
        fail.append(f"{stem}: method block never says what the figure does NOT show (guide 11c)")
    if re.search(r"<(svg|canvas)\b", blk):
        fail.append(f"{stem}: a <figure> contains vector art drawn in the page (guide 2.7)")
    if "zoomhint" not in flat:
        fail.append(f"{stem}: no click-to-open hint (guide 2.6)")
    alt = re.search(r'alt="([^"]*)"', blk)
    if not alt or len(alt.group(1)) < 60:
        fail.append(f"{stem}: alt text missing or too short to describe the figure")
    fn = re.search(r"<b>Figure (\d+)", flat)
    if fn:
        seen_nums.append(int(fn.group(1)))

# Figure numbers must ascend in DOCUMENT order. They did not on the first build of this page:
# the variance figure sat before the results figure but was numbered after it, so the prose said
# "Figure 4 shows why" three paragraphs above Figure 3.
if seen_nums != sorted(seen_nums):
    fail.append(f"figure numbers are out of document order: {seen_nums}")

for tm in re.finditer(r"<table[^>]*>", page):
    before = page[max(0, tm.start() - 400):tm.start()]
    if 'class="scroll"' not in before:
        fail.append(f"a <table> is not inside a .scroll box: {tm.group(0)[:60]}")
    if "<p class=\"cue\"" not in before:
        fail.append(f"a <table> has no overflow cue before it: {tm.group(0)[:60]}")

left = re.findall(r"__[A-Z][A-Z0-9_:]*__|\{\{[^}]+\}\}", page)
if left:
    fail.append(f"unsubstituted tokens remain: {sorted(set(left))[:6]}")
if "data:font" not in page:
    fail.append("no embedded font - the page would render in the system fallback")

die()
open(OUT, "w").write(page)
print(f"wrote {os.path.relpath(OUT, ROOT)}  ({len(page)/1e6:.2f} MB, {len(seen_nums)} figures)")
