#!/usr/bin/env python
"""Build references.json — one full bibliographic entry per paper in corpus.csv.

The page quotes statistics over the corpus ("N papers", "N of them run an RL algorithm"),
so the reference list has to be the SAME set, not a curated subset: one entry per corpus
row, no more and no fewer. `build_page.py` asserts that equality and refuses to build if it
breaks, because a reference list that silently disagrees with the statistics beside it is
worse than no list.

Titles are not typed. Every source PDF in the reference library is named
`<authors> <year> - <full title>.pdf`, so the filename carries the title, and this script
recovers it by matching each corpus row to a held file on first-author surname and year.
Rows with no held PDF — papers the digests catalogued from other folders' reviews or from a
web survey, which the library cites but does not hold — keep the digest's own label and are
marked `held: false`, so a reader can tell a first-hand entry from a second-hand one.

Identifiers (arXiv ids, DOIs, OpenReview forum ids) are pulled out of the venue string the
reviewers recorded, which is where they already live.

Usage:  python build_references.py
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

from _ident import surnames as name_candidates

HERE = Path(__file__).parent
LIB = HERE.parent.parent          # docs/project/references
OUT = HERE / "references.json"

# Papers the corpus holds under a different first author than the digest label implies, or
# whose held filename cannot be matched by surname+year alone. Each maps a corpus key to the
# exact PDF filename stem, so the match is stated rather than guessed.
MANUAL_FILE = {
    # Two rows the digests labelled by METHOD name rather than by author ("DIVERSE",
    # "Don't flatten, tokenize!"), so no surname can be recovered from the label and the
    # generic-word blocklist correctly refuses "diverse"/"flatten" as surnames.
    "dontflatten_2025_tokenize": "Sokar et al. 2025 - Don't flatten, tokenize - Unlocking the key to SoftMoE's efficacy in deep RL",
    "diverse_2026": "Eerlings et al. 2026 - DIVERSE - Disagreement-inducing vector evolution for Rashomon set exploration (preprint)",
    "botteghi_2025_hyperl": "Botteghi et al. 2026 - HypeRL - Hypernetwork-based reinforcement learning for control of parametrized dynamical systems (preprint)",
    "schaul_2015_universal": "Schaul et al. 2015 - Universal Value Function Approximators",
    "borsa_2018_universal": "Borsa et al. 2018 - Universal Successor Features Approximators",
}


# Papers whose held filename does not carry "<authors> <year> - <title>" and so cannot be
# indexed at all. One entry, and it is a library naming inconsistency rather than a missing
# paper: the file is called "How Does Batch Normalization Help Optimization_.pdf".
MANUAL_ENTRY = {
    "santurkar_2018_how": {
        "authors": "Santurkar, Tsipras, Ilyas & Madry", "year": "2018",
        "title": "How Does Batch Normalization Help Optimization?",
        "topic": "FiLM", "stem": "How Does Batch Normalization Help Optimization_",
    },
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s)
                  .encode("ascii", "ignore").decode().lower())


def first_surname(authors: str) -> str:
    """First author's surname, normalised.

    Written as a cut-at-the-first-delimiter rather than a split, because a split on
    `\\s+et al\\.?\\s+` needs whitespace AFTER "et al." and a filename ends right there —
    so "Perez et al." normalised to "perezetal" and matched nothing. 93 of 99 references
    fell back to a second-hand label because of it.
    """
    a = re.split(r"\bet al\b|\band\b|&|,", authors, maxsplit=1)[0]
    return norm(a)


def index_pdfs() -> dict[tuple[str, str], list[dict]]:
    """Index every held PDF by (first-author surname, year) -> [{title, authors, topic, stem}]."""
    idx: dict[tuple[str, str], list[dict]] = {}
    for p in LIB.glob("*/sources/*.pdf"):
        stem = p.stem
        m = re.match(r"^(.*?)\s((?:19|20|21)\d{2})\s*-\s*(.+)$", stem)
        if not m:
            continue
        authors, year, title = m.group(1).strip(), m.group(2), m.group(3).strip()
        surname = first_surname(authors)
        rec = {"authors": authors, "year": year, "title": title,
               "topic": p.parent.parent.name, "stem": stem}
        idx.setdefault((surname, year), []).append(rec)
    return idx


IDENT_PATTERNS = [
    (r"arXiv[:\s]*((?:19|20|21)\d{2}\.\d{4,5})", "arXiv:{}"),
    (r"\b((?:19|20|21)\d{2}\.\d{4,5})v\d\b", "arXiv:{}"),
    (r"(10\.\d{4,9}/[^\s,;)\]]+)", "DOI {}"),
    (r"OpenReview[`\s]*([A-Za-z0-9]{8,12})\b", "OpenReview {}"),
]


def identifier(venue_raw: str) -> str:
    for pat, fmt in IDENT_PATTERNS:
        m = re.search(pat, venue_raw, re.I)
        if m:
            return fmt.format(m.group(1).rstrip(".,);"))
    return ""


def clean_venue(venue_raw: str) -> str:
    """The venue as printed, trimmed of the reviewers' commentary.

    The venue cells are prose written for a reviewer, not bibliography fields: they quote
    the printed string and then explain where on the page it was found. The quotes and the
    explanation both have to go, or the reference list reads as somebody's notes.
    """
    v = re.sub(r"\s+", " ", venue_raw).strip()
    v = re.split(r"\s*[—–]\s*|\s*\((?:page|running|arXiv|later|NB)", v)[0].strip()
    # Cut the reviewer's provenance clause: "... (NeurIPS 2025)" printed at the foot of p.1
    v = re.split(r";|\bprinted at\b|\bverified\b|\bper the\b|\bfrom the\b|\bat the foot\b|"
                 r"\brunning header\b|\bpage-1\b|\bp\. ?1 footer\b", v)[0].strip()
    v = v.strip('"“”\' ').strip()
    # A stray opening quote with no closer, or a dangling bracket, after the cut.
    if v.count("(") > v.count(")"):
        v = v.rsplit("(", 1)[0].strip()
    v = v.rstrip(".;,")
    return v or "venue not printed in the held copy"


def clean_label(paper: str) -> str:
    """Strip the digests' parenthetical notes from a fallback label."""
    p = re.sub(r"\s*\((?:a review landed|no PDF|NB:|see the).*?\)\s*", " ", paper)
    return re.sub(r"\s+", " ", p).strip()


def main() -> int:
    rows = list(csv.DictReader((HERE / "corpus.csv").open(encoding="utf-8")))
    idx = index_pdfs()
    by_stem = {r["stem"]: r for recs in idx.values() for r in recs}

    refs, matched, unmatched = [], 0, []
    for r in rows:
        key, year = r["key"], r["year"]
        # Every plausible surname, not just the key's token: the key packs "Asadi & Littman"
        # into `asadilittman`, which matches no filename.
        cands_names = name_candidates(r["paper"], key)
        rec = None

        if key in MANUAL_ENTRY:
            rec = MANUAL_ENTRY[key]
        elif key in MANUAL_FILE:
            rec = by_stem.get(MANUAL_FILE[key])

        if rec is None:
            # Try the exact year, then +/- 1: a paper is often held as its preprint, whose
            # year differs from the venue year the digest recorded.
            years = [year]
            if year.isdigit():
                years += [str(int(year) + 1), str(int(year) - 1)]
            for y in years:
                cands = [c for n in cands_names for c in idx.get((n, y), [])]
                if not cands:
                    continue
                if len(cands) == 1:
                    rec = cands[0]
                    break
                # Disambiguate on the key's title token.
                tok = key.split("_", 2)[2] if key.count("_") >= 2 else ""
                hit = [c for c in cands if tok and tok[:6] in norm(c["title"])]
                rec = hit[0] if len(hit) == 1 else cands[0]
                break

        if rec:
            matched += 1
            entry = {"key": key, "authors": rec["authors"], "year": rec["year"],
                     "title": rec["title"], "topic": rec["topic"], "held": True}
        else:
            unmatched.append(key)
            entry = {"key": key, "authors": clean_label(r["paper"]), "year": year,
                     "title": "", "topic": "", "held": False}

        entry["venue"] = clean_venue(r["venue_raw"])
        entry["identifier"] = identifier(r["venue_raw"])
        entry["venue_tier"] = r["venue_tier"]
        entry["mechanism"] = r["mechanism"]
        entry["is_rl"] = r["is_rl"]
        refs.append(entry)

    # Alphabetical by first-author surname, then year — the order a reader expects, and the
    # order the in-text numbers will follow.
    refs.sort(key=lambda e: (norm(e["key"].split("_")[0]), e["year"]))
    for i, e in enumerate(refs, 1):
        e["num"] = i

    OUT.write_text(json.dumps(refs, indent=2, ensure_ascii=False))
    print(f"{len(refs)} references written ({matched} matched to a held PDF, "
          f"{len(unmatched)} catalogued but not held)")
    if unmatched:
        print("  not held (label from the digest, marked second-hand on the page):")
        for k in unmatched:
            print(f"    {k}")
    assert len(refs) == len(rows), "reference count must equal corpus row count"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
