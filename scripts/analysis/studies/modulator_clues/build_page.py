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
HERE = os.path.join(ROOT, "docs/experiments/active/modulator_clues")
TPL = os.path.join(HERE, "modulator_clues.template.html")
OUT = os.path.join(HERE, "modulator_clues.html")
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
    # Every figure names the script that draws it -- the checklist item the folder name alone does
    # not satisfy, since a reader cannot tell which of five scripts made which of five figures.
    block += (f'<p class="prov">Drawn by <code>scripts/<wbr>analysis/<wbr>studies/<wbr>'
              f'modulator_clues/<wbr>{stem}.py</code>\u2060, which also writes '
              f'<code>figures/<wbr>{stem}.data.txt</code>\u2060 \u2014 the table above.</p>')
    page = page.replace(f"__DATA:{stem}__", block)

# --- kind badges: causal / observational / controlled scene, from the tag each script EMITS ------
sys.path.insert(0, SCRIPTS)
import _common as CC                                              # noqa: E402
for stem in sorted({m for m in re.findall(r'data-fig="([^"]+)"', page)}):
    kf = os.path.join(FIGS, f"{stem}.kind.txt")
    if not os.path.exists(kf):
        fail.append(f"{stem}: no {stem}.kind.txt - figure is not tagged causal / observational / scene")
        continue
    k = open(kf).read().strip()
    page = page.replace(f"__KIND:{stem}__", f'<p class="kind kind-{k}">{CC.KIND[k]}</p>')
# --- script-emitted table fragments -----------------------------------------------------------
for m in set(re.findall(r"__TABLE:([a-z0-9_]+)__", page)):
    tf = os.path.join(FIGS, f"{m}.html")
    if not os.path.exists(tf):
        fail.append(f"table fragment {m}.html missing - run its script")
        continue
    page = page.replace(f"__TABLE:{m}__", open(tf).read())

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
seen_app, order = [], []
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
    if 'class="kind kind-' not in flat:
        fail.append(f"{stem}: no kind badge (causal / observational / scene) in its figure")
    if "zoomhint" not in flat:
        fail.append(f"{stem}: no click-to-open hint (guide 2.6)")
    alt = re.search(r'alt="([^"]*)"', blk)
    if not alt or len(alt.group(1)) < 60:
        fail.append(f"{stem}: alt text missing or too short to describe the figure")
    fn = re.search(r"<b>Figure (A?)(\d+)", flat)
    if not fn:
        fail.append(f"{stem}: caption has no 'Figure N' or 'Figure AN' number")
    else:
        (seen_app if fn.group(1) else seen_nums).append(int(fn.group(2)))
        order.append(fn.group(1))

# Figure numbers must ascend in DOCUMENT order. They did not on the first build of this page:
# the variance figure sat before the results figure but was numbered after it, so the prose said
# "Figure 4 shows why" three paragraphs above Figure 3.
# Order is not enough: a chained renumber (9->10, then 10->11) keeps the order right and still
# prints two "Figure 11"s. Every caption's number must equal its position on the page.
# Two series: the main body's Figures 1..N, then the appendix's Figures A1..AM, each numbered by
# position, and every main-body figure before every appendix one.
if seen_nums != list(range(1, len(seen_nums) + 1)):
    fail.append(f"figure numbers are not 1..N in document order: {seen_nums}")
if seen_app != list(range(1, len(seen_app) + 1)):
    fail.append(f"appendix figure numbers are not A1..AM in document order: {seen_app}")
if "A" in order and "" in order[order.index("A"):]:
    fail.append("a main-body figure appears after the appendix began")

for tm in re.finditer(r"<table[^>]*>", page):
    before = page[max(0, tm.start() - 400):tm.start()]
    if 'class="scroll"' not in before:
        fail.append(f"a <table> is not inside a .scroll box: {tm.group(0)[:60]}")
    if "<p class=\"cue\"" not in before:
        fail.append(f"a <table> has no overflow cue before it: {tm.group(0)[:60]}")

# The <title> must name THIS page. This page's header was first cut from a sibling template and
# carried that page's title through a clean build -- it would have published under another name.
_tm = re.search(r"<title>(.*?)</title>", page); _hm = re.search(r"<h1>(.*?)</h1>", page)
if not (_tm and _hm and _tm.group(1).strip() == _hm.group(1).strip()):
    fail.append(f"<title> {(_tm.group(1) if _tm else None)!r} does not match <h1> "
                f"{(_hm.group(1) if _hm else None)!r}")

left = re.findall(r"__[A-Z][A-Z0-9_:]*__|\{\{[^}]+\}\}", page)
if left:
    fail.append(f"unsubstituted tokens remain: {sorted(set(left))[:6]}")
if "data:font" not in page:
    fail.append("no embedded font - the page would render in the system fallback")

die()
# Declare the encoding first. Without it Chrome sniffed this 2.3 MB file as windows-1252 on one load in
# six and drew every em dash as "â€”"; the layout checkers inject a charset, so they could never see it.
page = '<meta charset="utf-8">\n' + page
assert page.startswith('<meta charset="utf-8">')
open(OUT, "w").write(page)
print(f"wrote {os.path.relpath(OUT, ROOT)}  ({len(page)/1e6:.2f} MB, {len(seen_nums)} figures)")
