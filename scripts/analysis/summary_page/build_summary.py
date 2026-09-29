"""Build a SUMMARY-REPORT artifact page (artifact generation guide §13) from its template.

    python scripts/analysis/summary_page/build_summary.py <template.html> <output.html>

A summary page is take-home claim cards, each linked into the detailed report that backs it. This
builder is shared by every summary: it adds nothing to the content, it only assembles and refuses.

  * lifts the house <style>, viewer markup and <script> from the BUILT style sheet (never the
    template, whose font url() still holds a {{FONT:...}} token);
  * <img data-thumb="<detailed page .html>#<stem>"> gets the detailed page's own embedded image for
    data-fig=<stem>, byte for byte -- a thumbnail is the evidence itself, never a redraw (§13c);
  * <a class="ev" data-src="<detailed page .html>#<anchor>" href="<published url>#<anchor>"> must
    name an id that exists in that detailed page, with the same fragment in href (§13c);
  * enforces the §13h checklist items that can be checked mechanically, and writes nothing if any
    fails.
"""
import html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HOUSE = os.path.join(ROOT, "docs/develop/active/meta/house_style_sheet.html")
CHIPS = {"ok": "Supported", "no": "Not supported", "mixed": "Mixed", "open": "Open"}   # guide §13d

tpl_path, out_path = sys.argv[1], sys.argv[2]
page = open(tpl_path).read()
fail = []

house = open(HOUSE).read()
style = re.search(r"<style>.*?</style>", house, re.S)
script = re.search(r"<script>.*?</script>", house, re.S)
viewer = re.search(r'<div class="lb fit" id="lb".*?\n</div>', house, re.S)
if not (style and script and viewer):
    sys.exit("could not lift the house <style>, viewer markup and <script> from the built sheet")
page = page.replace("__HOUSE_STYLE__", style.group(0))
page = page.replace("__HOUSE_SCRIPT__", viewer.group(0) + "\n" + script.group(0))

_cache = {}
def detailed(rel):
    if rel not in _cache:
        p = os.path.join(ROOT, rel)
        _cache[rel] = open(p).read() if os.path.exists(p) else None
    return _cache[rel]

# --- thumbnails: the detailed page's own image, by key --------------------------------------
def thumb(m):
    rel, stem = m.group(1).split("#")
    src = detailed(rel)
    if src is None:
        fail.append(f"thumbnail source {rel} does not exist"); return m.group(0)
    img = re.search(r'<img[^>]*data-fig="%s"[^>]*src="(data:image/[^"]+)"' % re.escape(stem), src) or \
          re.search(r'<img[^>]*src="(data:image/[^"]+)"[^>]*data-fig="%s"' % re.escape(stem), src)
    if not img:
        fail.append(f"{rel}: no embedded image with data-fig=\"{stem}\""); return m.group(0)
    return f'data-fig="{stem}" src="{img.group(1)}"'
page = re.sub(r'data-thumb="([^"]+)"', thumb, page)

# --- evidence links resolve to a real anchor, and href carries the same fragment ------------
evs = re.findall(r'<a class="ev" data-src="([^"]+)" href="([^"]+)"', page)
for dsrc, href in evs:
    rel, anchor = dsrc.split("#")
    src = detailed(rel)
    if src is None:
        fail.append(f"evidence page {rel} does not exist"); continue
    if f'id="{anchor}"' not in src:
        fail.append(f"{rel}: no element with id=\"{anchor}\" -- add the anchor (guide §13c) before citing it")
    if not href.endswith("#" + anchor):
        fail.append(f"link to {rel}#{anchor} has href {href} -- fragments differ")
    if f'data-source="{rel}"' not in page:
        fail.append(f"{rel} is cited but not listed among the source reports")

# --- cards: 3-6, each with a fixed chip, a thumbnail or a stated absence, and evidence --------
cards = re.findall(r'<article class="card[^"]*">(.*?)</article>', page, re.S)
if not 3 <= len(cards) <= 6:
    fail.append(f"{len(cards)} claim cards; a summary carries 3 to 6 (guide §13b)")
for i, c in enumerate(cards, 1):
    chip = re.search(r'<span class="chip (\w+)">([^<]+)</span>', c)
    if not chip or CHIPS.get(chip.group(1)) != chip.group(2).strip():
        fail.append(f"card {i}: verdict chip must be one of {list(CHIPS.values())} with its class (guide §13d)")
    if 'class="ev"' not in c:
        fail.append(f"card {i}: no Detail link into a detailed report")
    if "data-fig=" not in c and "no-thumb" not in c:
        fail.append(f"card {i}: no thumbnail and no stated reason for its absence (guide §13c)")

# --- language: nothing a reader without context cannot read (guide §13e) ---------------------
body = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", page, flags=re.S)
# The provenance footer (class="foot") is exempt: naming the builder and template by path is what
# makes the page reproducible (publish-page "Say where it came from"), and it is not reader prose.
prose = re.sub(r'<p class="foot">.*?</p>', " ", body, flags=re.S)
text = html.unescape(re.sub(r"<[^>]+>", " ", prose))
for pat, what in [(r"\.ya?ml\b|configs/", "config path"),
                  (r"\b(?=[a-z0-9]*\d)(?=[a-z0-9]*[a-z])[a-z0-9]{8}\b", "run-ID-like token"),
                  (r"[Α-Ωα-ω]", "Greek letter"),
                  (r"[₀-₉]", "subscript symbol"),
                  (r"\b[a-z]+_[a-z0-9_]+\b", "code identifier")]:
    for hit in sorted(set(re.findall(pat, text))):
        fail.append(f"visible text contains a {what}: {hit!r} (guide §13e)")

# --- glossary: only terms that appear on the page --------------------------------------------
gl = re.search(r'<dl class="gloss">(.*?)</dl>', page, re.S)
if not gl:
    fail.append("no 'Words used on this page' glossary (<dl class=\"gloss\">)")
else:
    rest = html.unescape(re.sub(r"<[^>]+>", " ", body.replace(gl.group(0), " "))).lower().replace("-", " ")
    for term in re.findall(r"<dt>(.*?)</dt>", gl.group(1)):
        if html.unescape(term).lower().replace("-", " ") not in rest:
            fail.append(f"glossary term {term!r} does not appear on the page")

if not re.search(r"<title>[^<]+</title>", page):
    fail.append("no <title>")
if fail:
    print("BUILD FAILURE -- nothing written:")
    for f in fail:
        print("  " + f)
    sys.exit(1)
open(out_path, "w").write(page)
print(f"wrote {out_path}  ({os.path.getsize(out_path)/1e6:.2f} MB, {len(cards)} cards, "
      f"{len(evs)} evidence links, {page.count('data-fig=')} thumbnails)")
