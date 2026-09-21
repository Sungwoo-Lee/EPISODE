#!/usr/bin/env python3
"""build_page.py - assemble the computational-functionalism field-review page from its parts.

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
OUT = f"{HERE}/computational_functionalism.html"
FIGS = f"{HERE}/figures"
HOUSE = "docs/develop/active/meta/house_style_sheet.template.html"
FONTS = "assets/fonts/pretendard/subset"

DATA = f"{HERE}/../field_history_data"
MANIFEST = f"{HERE}/../references_manifest.csv"

# Provenance is read from disk, never typed (guide 12d): works.csv says how deeply each work was read,
# the manifest gives the DOI and the file stem. The reference list IS the corpus - every one of its works
# is listed whether or not the page cites it, because the page's counts and diagrams are computed over
# the whole corpus (guide 12c, second invariant). A citation to a key outside the corpus fails the build.
TAG = {"reviewed-full": ("read", "reviewed in full"),
       "reviewed-short": ("short", "short summary from the PDF"),
       "named-only": ("unread", "named only - not read")}


def load_refs():
    import csv
    works = {r["key"]: r for r in csv.DictReader(open(f"{DATA}/works.csv", encoding="utf-8"))}
    man = {r["key"]: r for r in csv.DictReader(open(MANIFEST, encoding="utf-8"))}
    if set(works) != set(man):
        fail(f"works.csv and the manifest disagree: {sorted(set(works) ^ set(man))}")
    refs = {}
    for k, w in works.items():
        m = man[k]
        stem = m["file_stem"]
        who, _, title = stem.partition(" - ")
        if not re.search(r"\d{4}", who):          # an undated stem still prints the plotting year
            who = f"{who} c. {w['year']}"
        title = re.sub(r"\s*\((author copy|publisher preview|preprint|accepted manuscript)\)\s*$", "", title)
        refs[k] = {"label": w["short_label"], "who_year": who, "title": title.replace(" - ", ": "),
                   "doi": m["doi"], "status": w["status"], "community": w["community"], "year": w["year"],
                   "version": re.search(r"\((author copy|publisher preview|preprint|accepted manuscript)\)", stem)}
    return refs


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

    # ---- citations: resolved against the whole corpus; the list is the corpus, in first-citation order
    REFS = load_refs()
    page = re.sub(r"((?:\s*\{\{CITE:[a-z0-9_]+\}\})+)([.,;:])", r"\2\1", page)
    page = re.sub(r"\s*(\{\{CITE:)", "\u2060\\1", page)
    order = []
    for key in re.findall(r"\{\{CITE:([a-z0-9_]+)\}\}", page):
        if key not in REFS:
            fail(f"citation to a source outside the corpus: '{key}'")
        if key not in order:
            order.append(key)
    uncited = sorted((k for k in REFS if k not in order), key=lambda k: (int(REFS[k]["year"]), k))
    full_order = order + uncited
    num = {k: i for i, k in enumerate(full_order, 1)}
    for key in order:
        page = page.replace(f"{{{{CITE:{key}}}}}", f'<a class="cite" href="#ref-{key}">{num[key]}</a>')
    items = []
    for k in full_order:
        r = REFS[k]
        cls, txt = TAG[r["status"]]
        link = f' &middot; <a href="https://doi.org/{r["doi"]}">doi.org/{html.escape(r["doi"])}</a>' if r["doi"] else ""
        ver = f' &middot; PDF held is the {r["version"].group(1)}' if r["version"] and r["status"] != "named-only" else ""
        items.append(
            f'<li id="ref-{k}"><span class="rnum">{num[k]}</span><span class="rbody">'
            f'<span>{html.escape(r["who_year"])} &mdash; <strong>{html.escape(r["title"])}</strong>&nbsp;'
            f'<span class="rtag {cls}">{txt}</span></span>'
            f'<span class="rmeta">{html.escape(r["community"].replace("-", " "))}{link}{ver}</span></span></li>')
    page = page.replace("{{REFS}}", '<ol class="refs">\n' + "\n".join(items) + "\n</ol>")
    counts = {s: sum(1 for r in REFS.values() if r["status"] == s) for s in TAG}
    page = (page.replace("{{N_REFS}}", str(len(REFS))).replace("{{N_CITED}}", str(len(order)))
                .replace("{{N_FULL}}", str(counts["reviewed-full"])).replace("{{N_SHORT}}", str(counts["reviewed-short"]))
                .replace("{{N_NAMED}}", str(counts["named-only"]))
                .replace("{{N_READ}}", str(counts["reviewed-full"] + counts["reviewed-short"])))

    # ---- works the reviews point to that are not in the collection (not_held.csv), rendered, never typed
    import csv as _csv
    W = {r["key"]: r for r in _csv.DictReader(open(f"{DATA}/works.csv", encoding="utf-8"))}
    rows = list(_csv.DictReader(open(f"{DATA}/not_held.csv", encoding="utf-8")))
    trs = []
    for r in rows:
        cited = [W[k.strip()]["short_label"] for k in r["cited_by"].split(";") if k.strip()]
        for k in r["cited_by"].split(";"):
            if k.strip() and k.strip() not in W:
                fail(f"not_held.csv cites unknown key {k!r}")
        # a data cell must not print a raw key such as jacobson2013 (register F39 family): map keys to labels
        why = re.sub(r"\b([a-z_]+\d{4}[a-z]*)\b", lambda mm: W[mm.group(1)]["short_label"] if mm.group(1) in W else mm.group(1),
                     r["why_relevant"])
        if re.search(r"\b[a-z]+_?[a-z]*\d{4}[a-z]*\b", why):
            fail(f"not_held.csv row {r['label']!r} still prints a raw key: {why!r}")
        trs.append(f"<tr><td>{html.escape(r['label'])}</td><td class=\"n\">{html.escape(r['year'] or '—')}</td>"
                   f"<td>{html.escape(why)}</td><td>{html.escape(', '.join(cited) or '—')}</td></tr>")
    if "{{NOT_HELD}}" not in page:
        fail("template has no {{NOT_HELD}} token")
    page = page.replace("{{NOT_HELD}}",
        '<p class="cue" hidden>&larr; the table is wider than the screen &mdash; scroll it sideways</p>'
        '<div class="scroll"><table class="wide"><thead><tr><th>Work or strand</th><th class="n">Year</th>'
        '<th>Why it matters</th><th>Named by</th></tr></thead><tbody>' + "".join(trs) + "</tbody></table></div>")

    # ---- the debate status board, rendered from debates.csv so a status can never drift from the data.
    # The corpus-limit note travels WITH the status (synthesis 9): a badge shown without its scope invites
    # the reader to take a status as a fact about the field rather than about 36 reviewed works.
    drows = list(_csv.DictReader(open(f"{DATA}/debates.csv", encoding="utf-8")))
    npos = _csv.DictReader(open(f"{DATA}/positions.csv", encoding="utf-8"))
    held = {}
    for r in npos:
        held.setdefault(r["debate_id"], set()).update(k.strip() for k in r["keys"].split(";") if k.strip())
    cards = []
    for i, r in enumerate(drows, 1):
        for cell in ("status_reason", "status_scope", "question"):
            if re.search(r"\b[a-z]+_?[a-z]*\d{4}[a-z]*\b", r[cell]):
                fail(f"debates.csv {r['debate_id']} {cell} prints a raw manifest key: {r[cell]!r}")
        if r["status"] not in {"open", "leaning", "settled", "stalled", "untested"}:
            fail(f"debates.csv {r['debate_id']}: unknown status {r['status']!r}")
        # the direction column already starts with "toward"; prefixing "leaning toward" doubled the word
        d = r["status_direction"]
        if d and not d.startswith("toward"):
            fail(f"debates.csv {r['debate_id']}: status_direction should start with 'toward', got {d!r}")
        lean = f'<p class="dd"><strong>Leaning {html.escape(d)}.</strong></p>' if d else ""
        cards.append(
            f'<div class="debate"><p class="dnum">Debate {i} of {len(drows)} &middot; '
            f'{html.escape(r["first_year"])}&ndash;{html.escape(r["latest_year"])} &middot; '
            f'{len(held[r["debate_id"]])} works</p>'
            f'<p class="dq">{html.escape(r["title"])}</p>'
            f'<p class="dd">{html.escape(r["question"])}</p>'
            f'<p class="ds">status in this corpus: {html.escape(r["status"])}</p>'
            f'{lean}'
            f'<p class="dd">{html.escape(r["status_reason"])}</p>'
            f'<p class="dlimit"><strong>What this corpus cannot show.</strong> '
            f'{html.escape(r["status_scope"])}</p></div>')
    if "{{DEBATES}}" not in page:
        fail("template has no {{DEBATES}} token")
    page = page.replace("{{DEBATES}}", "\n".join(cards))
    page = page.replace("{{N_DEBATES}}", str(len(drows)))

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
          f"{len(full_order)} references, {len(order)} cited in text)")


if __name__ == "__main__":
    main()
