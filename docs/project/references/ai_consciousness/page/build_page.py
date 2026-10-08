#!/usr/bin/env python3
"""build_page.py - build the AI-consciousness field-review page from the synthesis and the figures.

SINGLE SOURCE. The page text is the PUBLIC part of `../ai_consciousness_synthesis.md`, rendered from
Markdown at build time, so the page and the synthesis cannot disagree. Sections the synthesis marks
"internal - not for the public page" (7, 10, 11), the Table of Contents, the appended reviewer
feedback and the revision log are left out. Review-locus brackets such as "[review Part B]" are
stripped (they point to files a reader cannot open). Wiki links become links to the published
companion page or plain text.

This page introduces ideas and debates; it is not a data-analysis report, so the generation guide's
analysis-only requirements (11a axes sentence, 11b data-used statement, 11c how-it-is-computed block)
do not apply, by the user's instruction of 2026-10-07. Everything else does: the House Style Sheet,
figures drawn only by scripts, the format register, citations that resolve.

FIGURES are written in `page_template.html` inside the holding block, each with
`data-at="before:<heading-id>"`; the builder moves each one to just before that heading.
CITATIONS: author-year mentions of works in the collection ("Michel 2026", "Butlin et al. 2023",
"Seth, response") become links to the reference list, which is the whole collection.
FAILS LOUDLY on: a missing synthesis section; a figure with no script or PNG, drawn in the page, or
whose anchor heading does not exist; a page class reusing a house class (register F54); any token
left unsubstituted.
"""
from __future__ import annotations

import base64
import csv
import html
import os
import re
import sys
import unicodedata

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
os.chdir(ROOT)
TEMPLATE = f"{HERE}/page_template.html"
OUT = f"{HERE}/ai_consciousness_review.html"
FIGS = f"{HERE}/figures"
SYN = f"{HERE}/../ai_consciousness_synthesis.md"
DATA = f"{HERE}/../field_data"
MANIFEST = f"{HERE}/../references_manifest.csv"
HOUSE = "docs/develop/active/meta/house_style_sheet.template.html"
FONTS = "assets/fonts/pretendard/subset"
CF_PAGE = "https://claude.ai/artifact/YFbbuZWRXHCfNEfrXdDp2b"
PUBLIC = ["What this document is about", "Reading conventions", "1.", "2.", "3.", "4.", "5.", "6.", "8.", "9."]


def fail(msg):
    sys.exit(f"build_page: {msg}")


def rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def slug(text):
    """GitHub-style heading id, so the synthesis's own (#...) links keep working on the page."""
    t = re.sub(r"<[^>]+>", "", text)
    t = html.unescape(t).strip().lower()
    t = re.sub(r"[^\w\- ]", "", t, flags=re.U)
    return t.replace(" ", "-")


def sections(md):
    parts = re.split(r"(?m)^## ", md)
    out = {}
    for p in parts[1:]:
        title = p.split("\n", 1)[0].strip()
        out[title] = "## " + p
    return out


def render(md_text):
    md_text = re.sub(r"\s*\*?\[reviews? [^\]\n]*\]\*?", "", md_text)            # review-locus brackets
    md_text = md_text.replace("[[computational_functionalism_field_history_synthesis]]",
                              f"the companion review *[Running the Right Program]({CF_PAGE})*")
    md_text = re.sub(r"\[\[([A-Za-z0-9_]+)\]\]", "the topic's index in the project repository", md_text)
    # display maths: lift it out before Markdown (which would read its underscores and backslashes as
    # emphasis and escapes), put it back afterwards for MathJax to typeset
    maths = []
    def keep(m):
        maths.append(m.group(1).strip())
        return f"\n\nMATHBLOCK{len(maths) - 1}\n\n"
    md_text = re.sub(r"(?ms)^[ \t]*\$\$\s*\n(.*?)\n[ \t]*\$\$[ \t]*$", keep, md_text)
    # Python-Markdown needs a blank line before a list that follows a paragraph line; the synthesis is
    # written for renderers that do not (format gate 2026-10-07: 99 list items had become run-on text)
    md_text = re.sub(r"(?m)^(?![ \t]*(?:[-*+]|\d+\.)[ \t])(?![ \t]*$)(.+)\n([ \t]*(?:[-*+]|\d+\.)[ \t])", r"\1\n\n\2", md_text)
    body = markdown.markdown(md_text, extensions=["tables", "sane_lists"])
    for i, tex in enumerate(maths):
        # relations written side by side with \qquad are stacked, so the block fits a phone column
        if "\\qquad" in tex:
            rows = [r.strip().rstrip(",") for r in re.split(r",?\s*\\qquad\s*", tex) if r.strip()]
            tex = "\\begin{aligned} " + " \\\\ ".join(re.sub(r"\s*([<>=])\s*", r" &\1 ", r, count=1) for r in rows) + " \\end{aligned}"
        cue = '<p class="cue" hidden>&larr; the formula is wider than the screen &mdash; scroll it sideways</p>'
        body = re.sub(rf"<p>MATHBLOCK{i}</p>|MATHBLOCK{i}\b",
                      lambda _m: f'{cue}<div class="mathblock" role="math">$$ {html.escape(tex, quote=False)} $$</div>', body)
    body = body.replace("<hr />", "")                                  # the template draws its own rules
    # heading ids; h4 ids are prefixed by their h3 so repeated sub-headings stay unique
    cur = [""]
    def hid(m):
        lvl, inner = m.group(1), m.group(2)
        s = slug(inner)
        if lvl in ("2", "3"):
            cur[0] = s
        else:
            s = f"{cur[0]}--{s}"
        return f'<h{lvl} id="{s}">{inner}</h{lvl}>'
    body = re.sub(r"<h([234])>(.*?)</h\1>", hid, body)
    # status words on question headings become chips
    body = re.sub(r"(<h3 [^>]*>.*?) — <strong>(open|leaning|settled)</strong>(</h3>)",
                  r'\1 <span class="qst">\2</span>\3', body)
    # curator's notes and other block quotes: the house callout
    body = body.replace("<blockquote>", '<div class="callout">').replace("</blockquote>", "</div>")
    # tables scroll inside their own box; three or more columns get the house wide-table floor
    def wrap(m):
        t = m.group(0)
        ncol = len(re.findall(r"<th[ >]", t.split("</tr>")[0]))
        cls = ' class="wide"' if ncol >= 3 else ""
        cue = '<p class="cue" hidden>&larr; the table is wider than the screen &mdash; scroll it sideways</p>' if ncol >= 3 else ""
        return f'{cue}<div class="scroll">{t.replace("<table>", f"<table{cls}>", 1)}</div>'
    body = re.sub(r"<table>.*?</table>", wrap, body, flags=re.S)
    return body


def link_citations(body, works):
    """Author-year mentions of collection works become links to their reference entry."""
    alias = {}
    for k, w in works.items():
        lab = re.sub(r"\s*\(.*?\)", "", w["short_label"]).strip()
        alias[lab] = k
        m = re.match(r"([A-Z][\wÀ-ſ'\-]+(?: [a-z]+)?)[ ,&].*?(\d{4})$", lab)
        if m and (" & " in lab or "," in lab or " et al." in lab):
            alias.setdefault(f"{m.group(1)} et al. {m.group(2)}", k)
    alias["Seth, target article"] = "seth2025"
    alias["Seth, response"] = "seth2026response"
    alias.pop("Seth 2025", None)                     # the target article is always named "Seth, target article"
    names = sorted(alias, key=len, reverse=True)
    pat = re.compile("|".join(re.escape(n) for n in names))
    out, depth = [], 0
    for tok in re.split(r"(<[^>]+>)", body):
        if tok.startswith("<"):
            if re.match(r"<a[ >]", tok):
                depth += 1
            elif tok.startswith("</a"):
                depth -= 1
            elif re.match(r"<h[1-6][ >]", tok):
                depth += 1
            elif re.match(r"</h[1-6]", tok):
                depth -= 1
            out.append(tok)
        elif depth:
            out.append(tok)
        else:
            out.append(pat.sub(lambda m: f'<a class="cref" href="#ref-{alias[m.group(0)]}">{m.group(0)}</a>', tok))
    return "".join(out)


def main():
    page = open(TEMPLATE, encoding="utf-8").read()
    house = open(HOUSE, encoding="utf-8").read()
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    v = re.search(r'(<div class="lb fit" id="lb".*?</script>)', house, re.S)
    if not (m and v):
        fail(f"could not find the style block or the figure viewer in {HOUSE}")
    own = re.search(r"\{\{HOUSE_STYLE\}\}\s*<style>(.*?)</style>", page, re.S)
    if not own:
        fail("template has no page-specific <style> block after {{HOUSE_STYLE}}")
    house_classes = set(re.findall(r"\.([A-Za-z][A-Za-z0-9_-]*)", re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)))
    leading = set()
    for sel in re.findall(r"([^{}]+)\{", re.sub(r"/\*.*?\*/", "", own.group(1), flags=re.S)):
        for part in sel.split(","):
            mm = re.match(r"\s*(?:[a-z0-9]+)?\.([A-Za-z][A-Za-z0-9_-]*)", part)
            if mm:
                leading.add(mm.group(1))
    clash = (leading & house_classes) - {"callout"}
    if clash:
        fail(f"page CSS starts a rule with a house class name (register F54): {sorted(clash)}")
    page = page.replace("{{HOUSE_STYLE}}", m.group(1)).replace("{{HOUSE_VIEWER}}", v.group(1))

    # ---- the synthesis, public sections only -------------------------------------------------
    secs = sections(open(SYN, encoding="utf-8").read())
    for want in PUBLIC:
        hit = [t for t in secs if t.startswith(want)]
        if len(hit) != 1:
            fail(f"synthesis section starting {want!r}: found {hit}")
        key = want.rstrip(".") if want[0].isdigit() else ("entry" if want.startswith("What") else "conventions")
        md = secs[hit[0]]
        if key in ("entry", "conventions"):
            md = re.sub(r"(?m)^## .*\n", "", md, count=1)          # the template supplies these headings
        tok = f"{{{{SYN:{key}}}}}"
        if tok not in page:
            fail(f"template has no {tok}")
        page = page.replace(tok, render(md))
    if re.search(r"internal\s*[—-]\s*not for the public page", page, re.I):
        fail("an internal section reached the page")

    # numbered section headings: '1. Vocabulary' -> house number chip
    page = re.sub(r'<h2 id="([^"]+)">(\d+)\. (.*?)</h2>',
                  lambda mm: f'<h2 id="{mm.group(1)}"><span class="num">{int(mm.group(2)):02d}</span> {mm.group(3)}</h2>', page)

    # ---- contents list, from the rendered headings --------------------------------------------
    toc = []
    for mm in re.finditer(r'<h([23]) id="([^"]+)">(.*?)</h\1>', page):
        lvl, i, inner = mm.groups()
        txt = re.sub(r"<[^>]+>", "", re.sub(r'<span class="num">(\d+)</span>', r"\1 ", inner)).strip()
        txt = re.sub(r"\s+(open|leaning|settled)$", "", txt)
        toc.append(f'<li class="t{lvl}"><a href="#{i}">{html.escape(txt, quote=False)}</a></li>')
    page = page.replace("{{TOC}}", '<ol class="toc">' + "".join(toc) + "</ol>")

    # ---- figures: check, embed, move to their anchors ------------------------------------------
    hold = re.search(r'<div id="figure-holding">(.*?)</div><!-- /figure-holding -->', page, re.S)
    if not hold:
        fail("template has no figure-holding block")
    figs = re.findall(r"<figure\b.*?</figure>", hold.group(1), re.S)
    page = page.replace(hold.group(0), "")
    stems = []
    for block in figs:
        s = re.search(r'<img data-fig="([A-Za-z0-9_]+)"', block)
        at = re.search(r'data-at="before:([^"]+)"', block)
        if not s or not at:
            fail("a figure lacks data-fig or data-at")
        stem, anchor = s.group(1), at.group(1)
        if re.search(r"<(svg|canvas)\b", block):
            fail(f"{stem}: the figure is drawn in the page - write it from a script (guide 2.7)")
        if not os.path.exists(f"{HERE}/{stem}.py") or not os.path.exists(f"{FIGS}/{stem}.png"):
            fail(f"{stem}: missing script or PNG")
        b64 = base64.b64encode(open(f"{FIGS}/{stem}.png", "rb").read()).decode()
        note = f"{FIGS}/{stem}.data.txt"
        block = block.replace(f'<img data-fig="{stem}"', f'<img data-fig="{stem}" src="data:image/png;base64,{b64}"', 1)
        block = block.replace(f"{{{{NOTE:{stem}}}}}", html.escape(open(note).read().strip(), quote=False) if os.path.exists(note) else "")
        target = re.search(rf'<h[234] id="{re.escape(anchor)}">', page)
        if not target:
            fail(f"{stem}: anchor heading #{anchor} not found on the page")
        page = page[:target.start()] + block + "\n" + page[target.start():]
        stems.append(stem)
    unused = {f[:-4] for f in os.listdir(FIGS) if f.endswith(".png")} - set(stems)
    if unused:
        fail(f"figures on disk that the page never shows: {sorted(unused)}")

    # ---- citations and the reference list -----------------------------------------------------
    man = {r["key"]: r for r in rows(MANIFEST)}
    works = {r["key"]: r for r in rows(f"{DATA}/works.csv")}
    if set(man) != set(works):
        fail(f"works.csv and the manifest disagree: {sorted(set(man) ^ set(works))}")
    page = link_citations(page, works)
    ctitle = {r["key"]: r["title"] for r in rows(f"{DATA}/commentaries.csv")}
    def sortkey(k):
        lab = unicodedata.normalize("NFKD", works[k]["short_label"]).encode("ascii", "ignore").decode().lower()
        return (0 if man[k]["batch"] in "AB" else 1 if man[k]["batch"] == "D" else 2, lab)
    items = []
    for k in sorted(man, key=sortkey):
        r, w = man[k], works[k]
        title = ctitle[k] if r["batch"] == "C" else ("The stuff matters: Consciousness, computation, and biology"
                                                    if r["batch"] == "D" else r["file_stem"].split(" - ", 1)[-1])
        title = re.sub(r"\s*\((BBS with commentaries and response)\)", "", title)
        tag = ("read", "reviewed in full") if r["tier"] == "full" else ("short", "structured review")
        where = f' &middot; BBS {r["bbs_article_number"]}' if r["batch"] in "CD" and r["bbs_article_number"] else ""
        link = f' &middot; <a href="https://doi.org/{r["doi"]}">doi.org/{html.escape(r["doi"])}</a>' if r["doi"] else ""
        items.append(f'<li id="ref-{k}"><span class="rbody"><span>{html.escape(w["short_label"], quote=False)} &mdash; '
                     f'<strong>{html.escape(title, quote=False)}</strong> <span class="rtag {tag[0]}">{tag[1]}</span></span>'
                     f'<span class="rmeta">{html.escape(w["kind"], quote=False)}{where}{link}</span></span></li>')
    page = page.replace("{{REFS}}", '<ul class="refs">\n' + "\n".join(items) + "\n</ul>")
    from collections import Counter
    b = Counter(r["batch"] for r in man.values())
    page = (page.replace("{{N_REFS}}", str(len(man))).replace("{{N_CORE}}", str(b["A"] + b["B"]))
                .replace("{{N_COMM}}", str(b["C"])))

    for weight in set(re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page)):
        f = f"{FONTS}/Pretendard-{weight}.latin.woff"
        if not os.path.exists(f):
            fail(f"font {weight}: no subset at {f}")
        page = page.replace(f"{{{{FONT:{weight}}}}}", base64.b64encode(open(f, "rb").read()).decode())
    page = re.sub(r"<code>([^<]{1,32})</code>", lambda mm: "<code>" + mm.group(1).replace("-", "-⁠") + "</code>", page)
    if "[[" in re.sub(r"<script.*?</script>", "", page, flags=re.S):
        fail("a [[wiki link]] survived into the page")
    if re.search(r"<p>[^<]*\n\s*(?:- |\d+\. )", page):
        fail("a list rendered as run-on text inside a paragraph")
    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        fail(f"unsubstituted tokens remain: {sorted(set(left))}")
    dead = sorted({a for a in re.findall(r'href="#([^"]+)"', page) if f'id="{a}"' not in page})
    if dead:
        fail(f"in-page links with no target: {dead[:12]}")
    open(OUT, "w", encoding="utf-8").write(page)
    cited = len(set(re.findall(r'class="cref" href="#ref-([^"]+)"', page)))
    print(f"  built {os.path.relpath(OUT, ROOT)} ({len(page):,} chars; {len(stems)} figures, "
          f"{len(man)} references, {cited} linked from the text)")


if __name__ == "__main__":
    main()
