#!/usr/bin/env python
"""Assemble field_review.html from the template, the rendered figures and the corpus counts.

Every number the page states about the corpus is substituted here from `corpus.csv` /
`corpus_provenance.json`, and every figure is embedded by its own key. Nothing about the
corpus is typed into the template by hand, because the guide's §9 lesson is that hand-carried
counts drift the moment the underlying set changes — and this corpus changed four times while
the page was being written.

Build-time enforcement (guide §11 — these are build failures, not review findings):
  11a  every <figcaption> carries an "Axes." sentence
  11b  every figure carries a used / available / percentage block, emitted by its script
  11c  every figure carries a "How it is computed" block of roughly 150-250 words
plus §3.3: every {{FIG:...}} placeholder resolves to a PNG that exists, and every rendered
PNG is referenced by the page — a figure that exists but is never shown is as much a defect
as a placeholder with no figure.

Usage:  python build_page.py
"""
from __future__ import annotations

import base64
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
FIGDIR = HERE / "figures"
TEMPLATE = HERE / "page_template.html"
OUT = HERE / "field_review.html"

WORD_MIN, WORD_MAX = 140, 280


def die(msg: str) -> None:
    print(f"BUILD FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def corpus_stats() -> dict[str, str]:
    rows = list(csv.DictReader((HERE / "corpus.csv").open(encoding="utf-8")))
    prov = json.loads((HERE / "corpus_provenance.json").read_text())
    rl = [r for r in rows if r["is_rl"] == "RL"]
    claims_rl = Counter(r["claim"] for r in rl)
    venue_rl = Counter(r["venue_tier"] for r in rl)
    mech_rl = Counter(r["mechanism"] for r in rl)
    cond_rl = Counter(r["cond_class"] for r in rl)
    years = [int(r["year"]) for r in rows if r["year"].isdigit()]
    return {
        "N_PAPERS": str(len(rows)),
        "N_RL": str(len(rl)),
        "N_NOT_RL": str(len(rows) - len(rl)),
        "N_MERGED": str(prov["n_merged_across_digests"]),
        "N_ROWS_PARSED": str(prov["n_rows_parsed"]),
        "N_SOURCE_FILES": str(len(prov["source_files"])),
        "YEAR_MIN": str(min(years)),
        "YEAR_MAX": str(max(years)),
        "N_ABLATED_RL": str(claims_rl.get("ablated", 0)),
        "N_ABLATED_QUAL_RL": str(claims_rl.get("ablated-qualified", 0)),
        "N_ASSERTED_RL": str(claims_rl.get("asserted", 0)),
        "N_TOPTIER_RL": str(venue_rl.get("top-tier", 0)),
        "N_PREPRINT_RL": str(venue_rl.get("preprint", 0)),
        "N_FILM_RL": str(mech_rl.get("FiLM", 0)),
        "N_HYPER_RL": str(mech_rl.get("hypernetwork", 0)),
        "N_OBS_COND_RL": str(cond_rl.get("observation (raw)", 0)),
        "PCT_ABLATED_RL": f"{100 * claims_rl.get('ablated', 0) / max(len(rl), 1):.0f}",
    }


def samples_block(stem: str, samples: dict) -> str:
    if stem not in samples:
        die(f"figure '{stem}' recorded no sample counts (guide §11b)")
    rows = "".join(
        f"<tr><td>{r['what']}</td><td class='n'>{r['used']}</td>"
        f"<td class='n'>{r['total']}</td><td class='n'>{r['pct']}%</td>"
        f"<td class='why'>{r['note']}</td></tr>"
        for r in samples[stem]
    )
    return (
        "<div class='samples'><h5>How much of the corpus this figure uses</h5>"
        "<div class='scroll'><table class='samp'><thead><tr><th>Subset</th><th>Used</th>"
        "<th>Available</th><th>Share</th><th>Why this subset</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div></div>"
    )


def main() -> int:
    if not TEMPLATE.exists():
        die(f"no template at {TEMPLATE}")
    html = TEMPLATE.read_text(encoding="utf-8")
    samples = json.loads((FIGDIR / "_samples.json").read_text())

    # --- figures ---------------------------------------------------------------------
    wanted = set(re.findall(r"\{\{FIG:([a-z0-9_]+)\}\}", html))
    rendered = {p.stem for p in FIGDIR.glob("fig*.png")}
    if wanted - rendered:
        die(f"template references figures that were never rendered: {sorted(wanted - rendered)}")
    if rendered - wanted:
        die(f"figures rendered but never shown on the page: {sorted(rendered - wanted)}")

    for stem in sorted(wanted):
        b64 = base64.b64encode((FIGDIR / f"{stem}.png").read_bytes()).decode()
        html = html.replace(f"{{{{FIG:{stem}}}}}", f"data:image/png;base64,{b64}")

    for stem in sorted(re.findall(r"\{\{SAMPLES:([a-z0-9_]+)\}\}", html)):
        html = html.replace(f"{{{{SAMPLES:{stem}}}}}", samples_block(stem, samples))

    # --- corpus counts ---------------------------------------------------------------
    for k, v in corpus_stats().items():
        html = html.replace(f"{{{{{k}}}}}", v)

    leftover = re.findall(r"\{\{([A-Z0-9_:a-z]+)\}\}", html)
    if leftover:
        die(f"unresolved placeholders remain: {sorted(set(leftover))}")

    # --- the three standing requirements ---------------------------------------------
    figures = re.findall(r"<figure\b.*?</figure>", html, flags=re.S)
    if len(figures) != len(wanted):
        die(f"{len(figures)} <figure> elements but {len(wanted)} figure placeholders")
    for i, fig in enumerate(figures, 1):
        cap = re.search(r"<figcaption\b.*?</figcaption>", fig, flags=re.S)
        if not cap:
            die(f"figure {i} has no <figcaption>")
        if "<b>Axes.</b>" not in cap.group(0):
            die(f"figure {i}: caption has no '<b>Axes.</b>' sentence (guide §11a)")
        if "How much of the corpus this figure uses" not in fig:
            die(f"figure {i}: no used/available/percentage block (guide §11b)")
        m = re.search(r"How it is computed</h5>(.*?)</div>", fig, flags=re.S)
        if not m:
            die(f"figure {i}: no 'How it is computed' block (guide §11c)")
        words = len(re.sub(r"<[^>]+>", " ", m.group(1)).split())
        if not (WORD_MIN <= words <= WORD_MAX):
            die(f"figure {i}: 'How it is computed' is {words} words, want {WORD_MIN}-{WORD_MAX} (§11c)")

    # --- structural checks -----------------------------------------------------------
    if "<title>" not in html:
        die("no <title>")
    for tag in ("<!doctype", "<html", "<head>", "<body>"):
        if tag in html.lower():
            die(f"template contains {tag} — the publish step adds the skeleton")
    # F29: a table header row must have as many cells as its body rows.
    for ti, tbl in enumerate(re.findall(r"<table\b.*?</table>", html, flags=re.S), 1):
        head = re.search(r"<thead>.*?</thead>", tbl, flags=re.S)
        if not head:
            continue
        ncols = len(re.findall(r"<th\b", head.group(0)))
        for ri, row in enumerate(re.findall(r"<tr>(?:(?!</tr>).)*</tr>", tbl.split("</thead>")[-1], flags=re.S), 1):
            n = len(re.findall(r"<t[dh]\b", row))
            if n and n != ncols:
                die(f"table {ti} row {ri}: {n} cells under {ncols} headers (format defect F29)")

    OUT.write_text(html, encoding="utf-8")
    kb = len(html.encode()) / 1024
    print(f"wrote {OUT}  ({kb:.0f} KB, {len(figures)} figures embedded)")
    if kb > 16 * 1024:
        die("page exceeds the 16 MB artifact limit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
