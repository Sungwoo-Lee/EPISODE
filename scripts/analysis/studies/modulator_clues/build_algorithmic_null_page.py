#!/usr/bin/env python3
"""build_algorithmic_null_page.py - assemble the "What Both Agents Compute" page.

WHAT IT DOES. Reads the page template, takes the House Style Sheet's `<style>` block, its full-size
figure viewer (guide 2.6) and its measured-scroll-cue script from `house_style_sheet.template.html`
(so the page cannot drift from the house look), inlines the Pretendard subsets, embeds each figure
PNG written by an `an0N_*.py` script, renders each figure's data statement from the `.data.txt` the
script emitted, resolves `{{CITE:key}}` tokens to numbered citations and renders the reference
list. The built page is never edited by hand.

FAILS LOUDLY, rather than writing a partial page, on:
  * an inline <svg> or <canvas> anywhere in the template                         - guide 2.7
  * a <figure> without <img data-fig>, or a figure shown twice                   - guide 2.7, F16
  * a figure caption with no <b>Axes.</b> sentence                                - guide 11a
  * a figure with no {{DATA:stem}} token, or a data statement without used / available rows
                                                                                  - guide 11b
  * a "How it is computed" block missing, mislabelled, or outside 150-250 words   - guide 11c
  * a figure with no generating script beside this builder, or no PNG / SVG / PDF / data.txt
  * a data statement with no `decision_rules:` line, a rules file other than the page's, or a sha
    that is neither the current rules file nor a registered revision's `sha256_before`
  * a data statement marked TEST INPUT (a synthetic or partial source), unless --preview
  * any file in the page's OWN figure folder (figures/algorithmic_null/) the page never shows;
    the parent figures/ folder belongs to another page and is never listed
  * a class defined in the page's own CSS that the house block also defines       - register F54
  * a citation to a key not in REFS, or a REFS entry the page never cites         - guide 12c
  * any token left unsubstituted.

--preview writes a local page that may show TEST INPUT figures, only to a path outside docs/, under
a banner saying so. It is for checking a layout before the real data exists; it is never published.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
os.chdir(ROOT)

DOC = "docs/experiments/active/modulator_clues"
TEMPLATE = f"{DOC}/algorithmic_null.template.html"
OUT = f"{DOC}/algorithmic_null.html"
FIGS = f"{DOC}/figures/algorithmic_null"          # this page's OWN subfolder; never its parent
RULES = f"{DOC}/algorithmic_null_decision_rules.yaml"
HOWTO_EYEBROW = "How it is computed"
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


def words(fragment: str) -> int:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = re.sub(r"\{\{[^}]+\}\}", " ", text)
    return len(html.unescape(text).split())


def rules_shas(path: str = RULES) -> tuple[str, dict]:
    """(current sha256, {earlier sha256: revision date}) of the page's decision-rules file."""
    b = open(path, "rb").read()
    rules = yaml.safe_load(b)["decision_rules"]
    earlier = {rv["sha256_before"]: rv.get("date", "?") for rv in rules.get("revisions", [])
               if rv.get("sha256_before")}
    return hashlib.sha256(b).hexdigest(), earlier


def parse_data(stem: str, path: str) -> dict:
    """The data statement an an0N script emitted (format in `_an_common.py`)."""
    d = {"status": None, "rules": None, "source": None, "rows": []}
    for line in open(path).read().splitlines():
        if not line.strip():
            continue
        key, _, val = line.partition(": ")
        if key == "row":
            cells = val.split("|")
            if len(cells) != 5:
                fail(f"{stem}: data row does not have 5 cells: {line!r}")
            d["rows"].append(cells)
        elif key == "decision_rules":
            m = re.fullmatch(r"(\S+) ([0-9a-f]{64}) @ (\S+)", val)
            if not m:
                fail(f"{stem}: malformed decision_rules line: {line!r}")
            d["rules"] = m.groups()
        elif key in ("status", "source"):
            d[key] = val
        else:
            fail(f"{stem}: unknown data-statement line: {line!r}")
    if not d["rules"]:
        fail(f"{stem}: data statement has no decision_rules line")
    if not (d["status"] and d["source"] and d["rows"]):
        fail(f"{stem}: data statement lacks a status, a source or used / available rows (guide 11b)")
    return d


def render_data(stem: str, d: dict, note: str) -> str:
    """The data statement as a caption block: status and provenance in words, then the table."""
    rfile, sha, commit = d["rules"]
    esc = html.escape
    status = d["status"].split(" Rules note:")[0].rstrip(".")   # the builder states the verified note
    head = (f'<span><b>Data.</b> Evidence status: {esc(status)}. Decision rules <code>{esc(rfile)}</code> '
            f'sha256 <code>{sha[:12]}</code> @ <code>{esc(commit if commit == "uncommitted" else commit[:8])}</code>{esc(note)}. '
            f'Read from <code>{esc(d["source"].split(" (")[0])}</code>'
            f'{esc(" (" + d["source"].split(" (", 1)[1]) if " (" in d["source"] else ""}; '
            f'counts emitted by <code>{stem}.py</code>.</span>')
    rows = "".join(f'<tr><td>{esc(w)}</td><td class="n">{esc(u)}</td><td class="n">{esc(t)}</td>'
                   f'<td class="n">{esc(p)}{"" if p == "n/a" else "%"}</td><td>{esc(n)}</td></tr>'
                   for w, u, t, p, n in d["rows"])
    return (head + '<p class="cue" hidden>&larr; wider than the screen &mdash; scroll it sideways; '
            'the right-hand columns are cut off</p><div class="scroll"><table class="wide"><thead><tr>'
            '<th>subset</th><th class="n">used</th><th class="n">available</th><th class="n">share</th>'
            f'<th>why</th></tr></thead><tbody>{rows}</tbody></table></div>')


def main(argv=None):
    ap = argparse.ArgumentParser(description="build the What Both Agents Compute page")
    ap.add_argument("--template", default=TEMPLATE)
    ap.add_argument("--figures", default=FIGS, help="the page's own figure folder")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--preview", action="store_true",
                    help="local preview: TEST INPUT figures allowed, output outside docs/, bannered")
    args = ap.parse_args(argv)
    figs, out = args.figures, args.out
    if args.preview and os.path.abspath(out).startswith(os.path.abspath("docs") + os.sep):
        fail("--preview writes outside docs/ only (a preview page must never be published)")
    page = open(args.template).read()
    house = open(HOUSE).read()

    if re.search(r"<(svg|canvas)\b", page):
        fail("the template draws in the page (inline <svg> or <canvas>); figures come from "
             "scripts (guide 2.7)")

    # ---- the house look, viewer and cue script, taken from their one source -------------------
    m = re.search(r'(<link rel="stylesheet".*?</style>)', house, re.S)
    vm = re.search(r'(<div class="lb fit" id="lb".*?\n</div>)', house, re.S)
    vs = re.search(r"(\(function \(\) \{\s*// full-size figure viewer.*?\}\)\(\);)", house, re.S)
    s = re.search(r"(function updateCues\(\).*?)</script>", house, re.S)
    if not (m and vm and vs and s):
        fail(f"could not find the style block, the figure viewer or the cue script in {HOUSE}")
    house_css = m.group(1)

    # register F54: a page class reusing a house class name inherits every declaration it does not
    # override. Require the two definition sets to be disjoint.
    own = re.findall(r"<style>(.*?)</style>", page, re.S)
    clash = css_classes("".join(own)) & css_classes(house_css)
    if clash:
        fail(f"page CSS defines classes the house block already defines (F54): {sorted(clash)}")

    # the viewer script is useless without the markup it reaches by id (register F57), and two
    # copies would duplicate ids: each token exactly once
    for tok in ("{{HOUSE_STYLE}}", "{{HOUSE_VIEWER}}", "{{HOUSE_SCRIPT}}"):
        if page.count(tok) != 1:
            fail(f"{tok} must occur exactly once in the template (found {page.count(tok)})")
    page = page.replace("{{HOUSE_STYLE}}", house_css)
    page = page.replace("{{HOUSE_VIEWER}}", vm.group(1))
    page = page.replace("{{HOUSE_SCRIPT}}", "<script>\n" + vs.group(1) + "\n" + s.group(1) + "</script>")

    # ---- figures: one block at a time, never a pattern spanning two (register F16) ------------
    cur_sha, earlier = rules_shas()
    stems, earlier_used, test_used = [], [], []
    for block in re.findall(r"<figure\b.*?</figure>", page, re.S):
        st = re.search(r'<img data-fig="([A-Za-z0-9_]+)"', block)
        if not st:
            fail("a <figure> holds no <img data-fig>")
        stem = st.group(1)
        stems.append(stem)
        cap = re.search(r"<figcaption>.*?</figcaption>", block, re.S)
        if not cap or "<b>Axes.</b>" not in cap.group(0):
            fail(f"{stem}: caption has no <b>Axes.</b> sentence (guide 11a)")
        if f"{{{{DATA:{stem}}}}}" not in cap.group(0):
            fail(f"{stem}: no {{{{DATA:{stem}}}}} data-statement token in the caption (guide 11b)")
        how = re.search(r'<div class="howto">(.*?)</div>', block, re.S)
        if not how:
            fail(f"{stem}: no 'How it is computed' block (guide 11c)")
        eb = re.search(r'<p class="eyebrow">(.*?)</p>', how.group(1), re.S)
        if not eb or " ".join(html.unescape(eb.group(1)).split()) != HOWTO_EYEBROW:
            fail(f"{stem}: the method block's eyebrow must read exactly '{HOWTO_EYEBROW}'")
        n = words(how.group(1).replace(eb.group(0), " "))      # count without the eyebrow
        if not 150 <= n <= 250:
            fail(f"{stem}: 'How it is computed' is {n} words; guide 11c wants 150-250")
        if not os.path.exists(f"{HERE}/{stem}.py"):
            fail(f"{stem}: no generating script at {HERE}/{stem}.py")
        for ext in ("png", "svg", "pdf", "data.txt"):
            if not os.path.exists(f"{figs}/{stem}.{ext}"):
                fail(f"{stem}: no {ext} in {figs} -- run python {HERE}/{stem}.py")
        d = parse_data(stem, f"{figs}/{stem}.data.txt")
        rfile, sha, _ = d["rules"]
        if rfile != RULES:
            fail(f"{stem}: drawn under rules file {rfile}, not the page's {RULES}")
        if sha == cur_sha:
            note = ""
        elif sha in earlier:
            note = (f", the rules before their {earlier[sha]} revision (reported with that sha, as "
                    f"the revision requires; current file {cur_sha[:12]})")
            earlier_used.append(stem)
        else:
            fail(f"{stem}: rules sha {sha[:12]} is neither the current rules file ({cur_sha[:12]}) "
                 f"nor a registered revision's sha256_before")
        if d["status"].startswith("TEST INPUT"):
            if not args.preview:
                fail(f"{stem}: drawn from a TEST INPUT ({d['source']}); only --preview may show it")
            test_used.append(stem)
        page = page.replace(f"{{{{DATA:{stem}}}}}", render_data(stem, d, note), 1)
        print(f"  {stem}: how-it-is-computed {n} words; rules {sha[:12]}"
              + (" (earlier revision)" if note else "") + (" TEST INPUT" if stem in test_used else ""))
    if len(stems) != len(set(stems)):
        fail(f"a figure is shown twice: {stems}")
    # every file in the page's OWN subfolder must belong to a shown figure; the parent folder (the
    # other page's 111 files) is never listed, so no deletion there can satisfy or break this check
    if os.path.isdir(figs):
        allowed = {f"{st}.{ext}" for st in stems for ext in ("png", "svg", "pdf", "data.txt")}
        stray = sorted(f for f in os.listdir(figs) if f not in allowed)
        if stray:
            fail(f"files in {figs} that the page never shows: {stray}")
    for stem in stems:
        b64 = base64.b64encode(open(f"{figs}/{stem}.png", "rb").read()).decode()
        page = page.replace(f'<img data-fig="{stem}"',
                            f'<img data-fig="{stem}" src="data:image/png;base64,{b64}"', 1)
    if args.preview:
        banner = ('<div class="callout warn"><p class="eyebrow">Local preview &mdash; not for '
                  'publication</p><p>Built with <code>--preview</code>. '
                  + (f'Figures drawn from TEST INPUT (synthetic or partial data): '
                     f'{html.escape(", ".join(test_used))}. ' if test_used else '')
                  + 'Their numbers are fixture or partial values, not results.</p></div>')
        page = page.replace('<div class="wrap">', '<div class="wrap">\n' + banner, 1)

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

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w").write(page)
    print(f"  built {out}  ({len(page):,} chars; {len(stems)} figures, {len(order)} references"
          + (f"; {len(earlier_used)} figure(s) under an earlier rules revision" if earlier_used else "")
          + ("; PREVIEW" if args.preview else "") + ")")


if __name__ == "__main__":
    main()
