#!/usr/bin/env python
"""Audit how much of the corpus actually has a review written, and where it lives.

The page quotes statistics over 97 papers. That is the set the review DRAWS ON, which is not
the same as the set the project has READ end-to-end, and conflating the two would overstate
what the library contains. This script measures the difference.

Four levels of evidence, strongest first:

  per-paper     a dedicated review file for this paper (`<topic>/reviews/<author>_<year>_*.md`)
  master        a section inside a topic's master review document
  pending       a review written this session, still in tmp/ awaiting merge into a topic doc
  catalogued    named and characterised in a digest or survey, but never read end-to-end

Usage:  python audit_review_coverage.py
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

from _ident import fold_text, surnames

HERE = Path(__file__).parent
LIB = HERE.parent.parent
TMP = Path("/media/nas01/projects/Interoceptive-AI/grid_world_pain/tmp/20260909_153028_filmhyper_rl")


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s)
                  .encode("ascii", "ignore").decode().lower())


def main() -> int:
    rows = list(csv.DictReader((HERE / "corpus.csv").open(encoding="utf-8")))

    per_paper = {p.stem: p for p in LIB.glob("*/reviews/*.md")}
    per_paper_folded = {}
    for k, v in per_paper.items():
        f = fold_text(k)
        per_paper_folded[f] = v
        per_paper_folded[f.replace(" ", "")] = v
    masters = {}
    for p in list(LIB.glob("*/*.md")) + list(LIB.glob("*/archive/*.md")):
        # `_lit_review` / `_review` documents carry per-paper sections. `_synthesis` and
        # `_survey` documents are cross-paper arguments that CITE papers, including ones
        # nobody has read, so a hit in one of those is a mention, not a review.
        if re.search(r"lit_review|_review\b", p.name) and not re.search(r"synthesis|survey", p.name):
            try:
                masters[p] = fold_text(p.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
    pending = {}
    for p in TMP.glob("reviews_*.md"):
        try:
            pending[p] = fold_text(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass

    # Which papers are actually held as a PDF. A "master" hit on a paper the library does
    # NOT hold is a citation, not a reading — e-nmRNN scored that way while sitting in the
    # README's own "deliberately not downloaded" list. De Vries is the one real exception:
    # reviewed from an archived document, no PDF, and recorded as such in the corpus.
    held = {e["key"] for e in json.loads((HERE / "references.json").read_text()) if e["held"]}
    HELD_EXCEPTIONS = {"devries_2017_conditional"}

    out, tally = [], {"per-paper": 0, "master": 0, "pending": 0, "catalogued": 0}
    for r in rows:
        year = r["year"]
        names = surnames(r["paper"], r["key"])
        level, where = "catalogued", ""

        for stem_f, path in per_paper_folded.items():
            if year in stem_f and any(n in stem_f for n in names):
                level, where = "per-paper", str(path.relative_to(LIB))
                break

        if level == "catalogued":
            # A document counts only if it names an author AND the year within 400 chars —
            # a bare citation elsewhere in a long review is not a review OF that paper.
            for bucket, lvl, fmt in ((masters, "master", lambda p: str(p.relative_to(LIB))),
                                     (pending, "pending", lambda p: f"tmp/.../{p.name}")):
                for p, text in bucket.items():
                    for n in names:
                        if n not in text or year not in text:
                            continue
                        if any(year in text[max(0, i - 400):i + 400]
                               for i in (m.start() for m in re.finditer(re.escape(n), text))):
                            level, where = lvl, fmt(p)
                            break
                    if level != "catalogued":
                        break
                if level != "catalogued":
                    break

        if level == "master" and r["key"] not in held and r["key"] not in HELD_EXCEPTIONS:
            level, where = "catalogued", "cited in a review, but no PDF is held"

        tally[level] += 1
        out.append({"key": r["key"], "level": level, "where": where,
                    "is_rl": r["is_rl"], "paper": r["paper"][:70]})

    (HERE / "review_coverage.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))

    n = len(rows)
    print(f"corpus: {n} papers\n")
    for lvl in ("per-paper", "master", "pending", "catalogued"):
        print(f"  {tally[lvl]:3d}  {100*tally[lvl]/n:4.1f}%  {lvl}")
    read = tally["per-paper"] + tally["master"] + tally["pending"]
    print(f"\n  {read}/{n} ({100*read/n:.0f}%) have a review document somewhere")
    print(f"  {tally['catalogued']} are catalogued only — named in a digest, never read end-to-end\n")
    print("catalogued-only papers:")
    for e in out:
        if e["level"] == "catalogued":
            print(f"    [{e['is_rl']:6s}] {e['key']:34s} {e['paper'][:52]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
