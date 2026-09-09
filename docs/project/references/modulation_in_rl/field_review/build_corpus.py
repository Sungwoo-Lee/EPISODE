#!/usr/bin/env python
"""Build corpus.csv — one row per distinct paper in the FiLM/hypernetwork-in-RL field review.

Parses the pipe tables written by the three `literature-curator` digests and the
`literature-reviewer` merge-row files, all of which share a fixed 10-column schema:

    paper | year | venue-as-printed | mechanism | conditioning signal |
    injection site | RL algorithm | benchmark | headline result | claim strength

Nothing here is typed by hand. Every figure in the field review reads this file, so a
number on the page can always be traced back to a row of a digest, and a digest row back
to a named section of a review. That is the guide's "generate every number, transcribe
none" rule applied to a literature corpus rather than to training data.

Papers appear in more than one digest (the FiLM digest's tiers A3/A4 catalogue papers whose
reviews live in the Hypernetwork and modulation_in_rl folders). Rows are therefore keyed on
a normalised first-author + year slug and merged, with the richer row winning field by
field, and the merge recorded in `n_sources` so double-counting is visible rather than
silent.

Usage:  python build_corpus.py [--digests DIR] [--out corpus.csv]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

DEFAULT_DIGESTS = Path(
    "/media/nas01/projects/Interoceptive-AI/grid_world_pain/tmp/20260909_153028_filmhyper_rl"
)

# --------------------------------------------------------------------------------------
# Classification vocabularies.
#
# These are the only judgement calls in the file. Each maps a free-text cell written by a
# reviewer onto a small closed set the figures can count. They are deliberately explicit
# and order-sensitive: the FIRST pattern that matches wins, so more specific patterns are
# listed before more general ones.
# --------------------------------------------------------------------------------------

# Mechanism: what operator conditions the network. Six classes; F12 in the format register
# caps a figure at about six colour-distinguished series, and this is that budget spent.
MECHANISM_RULES = [
    ("plasticity", r"plasticity"),
    ("concatenation", r"\bconcat"),
    ("attention", r"attention"),
    ("routing", r"routing|mixture|moe|mixture-of-experts"),
    ("hypernetwork", r"hypernet|weight generation|parameter composition|low-rank|lora"),
    ("FiLM", r"film|adaln|adain|conditional (instance|batch|layer)|gating|gain|scale.?and.?shift|affine"),
]

# Venue tier. "Top-tier peer-reviewed" is the class the user weights highest, so the
# pattern list is conservative: a venue only counts when the string names the venue, and
# anything hedged ("unstated", "preprint", "under review", "submitted") falls through to
# preprint regardless of what else the cell says.
PREPRINT_MARKERS = r"unstated|preprint|under review|submitted|arxiv:|arxiv \d|no venue|unconfirmed|biorxiv"
TOP_TIER = r"neurips|nips\b|icml|iclr|\baaai|\bcvpr|\biccv|\beccv|\bcorl|\brss\b|\bicra\b|ijcai|\bacl\b"
WORKSHOP = r"workshop"


def classify_mechanism(cell: str) -> str:
    c = cell.lower()
    for name, pat in MECHANISM_RULES:
        if re.search(pat, c):
            return name
    return "other"


def classify_venue(cell: str) -> str:
    """Return one of: top-tier, other-peer-reviewed, workshop, preprint.

    Order matters. A workshop paper at a top-tier venue is a workshop paper; a cell that
    hedges the venue is a preprint even when it names one, because the review's own rule is
    that the venue must be printed inside the PDF.
    """
    c = cell.lower()
    if re.search(WORKSHOP, c):
        return "workshop"
    # A hedge anywhere in the cell demotes it, unless the cell also carries an explicit
    # verification note ("verified", "page-1 footer", "running header").
    hedged = re.search(PREPRINT_MARKERS, c)
    verified = re.search(r"verified|page-1 footer|running header|page header|copyright block|proceedings", c)
    if hedged and not verified:
        return "preprint"
    if re.search(TOP_TIER, c):
        return "top-tier"
    if re.search(r"journal|plos|nature|neural networks|ijrr|pami|distill|tmlr|foundations and trends", c):
        return "other-peer-reviewed"
    if hedged:
        return "preprint"
    return "unclassified"


# Words that demote an ablation from clean to qualified. These are the reviewers' own
# hedges, and keeping them as a separate class is the point of the evidence-quality figure:
# the corpus contains many more ablations than it contains ablations you can lean on.
ABLATION_HEDGES = (
    r"confounded|but weak|graphical only|no numerical value|no seeds|no error bars|"
    r"directional only|cannot support|too thin|unablated|never ablated|isolat\w+ neither|"
    r"qualitative only|no confidence interval|single-author|one run per"
)


def classify_claim(cell: str) -> str:
    """Return one of: ablated, ablated-qualified, asserted, no-experiment, unverified.

    'ablated' means the paper ran a controlled comparison of the conditioning mechanism.
    'ablated-qualified' means it ran one but a reviewer recorded a hedge that stops the
    number being quotable — a confound left un-ablated, a figure with no printed value, or
    a single run per configuration. The distinction is load-bearing: the field review's
    headline evidence claim is that clean isolations of what modulation contributes are
    much rarer than the count of ablations suggests.
    """
    c = cell.lower()
    if "unverified" in c or "second-hand" in c:
        return "unverified"
    if "no-experiment" in c or "no experiment" in c:
        return "no-experiment"
    if "ablated" in c:
        return "ablated-qualified" if re.search(ABLATION_HEDGES, c) else "ablated"
    if "asserted" in c:
        return "asserted"
    return "unclassified"


def classify_rl(cell: str) -> str:
    """Return 'RL' or 'not RL' from the RL-algorithm column."""
    c = cell.lower().strip()
    if re.search(r"\bnot rl\b|^n/?a$|imitation|behaviou?r clon|supervised", c) and not re.search(
        r"\bppo\b|\bsac\b|\btd3\b|\ba2c\b|\ba3c\b|dqn|dreamer|impala|q-learning", c
    ):
        return "not RL"
    if c in {"", "-", "—"}:
        return "unclassified"
    return "RL"


def classify_conditioner(cell: str) -> str:
    """What the modulator reads. The review's sharpest axis, so it gets its own vocabulary.

    Order is deliberate. 'own activity / statistic' is tested before 'observation' because a
    conditioner reading a *pooled* or *batch-averaged* summary of the stream it modulates is
    a different design from one reading the raw stream at full bandwidth — that distinction
    is exactly what separates Temporal FiLM and CaFiLM from naive self-conditioning.
    """
    c = cell.lower()
    if not c.strip() or re.search(r"^n/?a$", c):
        return "n/a"
    if re.search(r"timestep|denoising|flow \w*step|diffusion step|noise level", c):
        return "denoising timestep"
    # Tested before the observation class on purpose. A conditioner reading the network's own
    # Q-values "at that state", or a curiosity score "per state", is reading a statistic the
    # network computed — not the observation. Matching a bare \bstate\b first put three such
    # papers in the observation row and made the corpus look like it contradicted itself.
    if re.search(r"own (past )?(hidden|activity|activation)|its own|pooled|batch (feature )?mean|"
                 r"block-pooled|entropy|uncertainty|prediction error|recurrent hidden state|"
                 r"q-value|curiosity score|novelty score|rnd score|value estimate", c):
        return "own activity / statistic"
    if re.search(r"gait phase|cyclic|clock|phase \$|open-loop phase|episode phase", c):
        return "exogenous phase / clock"
    if re.search(r"member index|ensemble.member|ensemble index|searched by evolution|"
                 r"noise variable|normalizing flow", c):
        return "index / noise (not a task signal)"
    if re.search(r"language|instruction|sentence|\btext\b|clip|caption|question|"
                 r"source token sequence|symbolic layout", c):
        return "language instruction"
    if re.search(r"belief|inferred|latent context|posterior|vae|variational|context latent|"
                 r"inferred from transitions|history", c):
        return "inferred belief / latent"
    if re.search(r"physical param|torso|speed|mass|stiffness|damping|morpholog|capability|"
                 r"actuator|fault|system parameter|kinemat", c):
        return "physical parameters"
    if re.search(r"task id|task index|one-hot|task embedding|task specification|style index|"
                 r"discrete task|task descriptor|agent embedding|goal|task command|"
                 r"task encoder|task-mixture|support set|per-layer embedding", c):
        return "task / goal identity"
    if re.search(r"quantile|discount|temperature|hyperparameter|exploration|gamma|horizon|"
                 r"return-to-go|target return|meta-gradient", c):
        return "algorithmic knob"
    if re.search(r"\bobservation\b|\bstate\b|\bpixel\b|current input|same input|"
                 r"the input\b|token representation itself", c):
        return "observation (raw)"
    return "other"


def classify_site(cell: str) -> str:
    """Coarse injection site: encoder / trunk / actor / critic / actor+critic / world-model / weights / n-a."""
    c = cell.lower()
    if re.search(r"\bn/?a\b", c) or not c.strip():
        return "n/a"
    has_actor = bool(re.search(r"actor|policy", c))
    has_critic = bool(re.search(r"critic|value", c))
    if re.search(r"world model|rssm|dynamics model", c):
        return "world model"
    if re.search(r"all weights|weight tensor|every weight|generates the policy|policy mlp|target policy", c):
        return "generated weights"
    if has_actor and has_critic:
        return "actor + critic"
    if has_critic:
        return "critic only"
    if has_actor:
        return "actor only"
    if re.search(r"encoder|visual|conv|cnn|feature map|perception", c):
        return "encoder"
    if re.search(r"transformer|block|layer|trunk|residual|u-net|backbone|norm", c):
        return "trunk / all blocks"
    return "other"


# --------------------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------------------

HEADER_RE = re.compile(r"^\|\s*paper\s*\|", re.I)
SEP_RE = re.compile(r"^\|[\s:\-|]+\|$")


def strip_md(s: str) -> str:
    """Remove markdown emphasis, links, footnote marks and collapse whitespace."""
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)          # links
    s = re.sub(r"[*_`]{1,3}", "", s)                          # emphasis / code
    s = re.sub(r"⚠️|†|ᶠ¹|\bf1\b(?=\s|$)", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


STOPWORDS = {"the", "a", "an", "on", "of", "in", "for", "with", "via", "and", "to", "is", "are"}

# One paper, written two ways in two digests. Each of these was surfaced by the
# same-author-same-year warning at the bottom of this script and then checked by hand
# against the papers; they are aliases, not distinct works. Guo 2026 and Li 2025 also trip
# that warning and are NOT listed here, because those really are two papers each.
ALIASES = {
    "sarafian_2021_recomposing": "sarafian_2021_hypernetwork",   # Recomposing the RL Building Blocks with Hypernetworks
    "schopf_2022_hypernetwork": "schopf_2022_hn",                # Hypernetwork-PPO / HN-PPO
    "vecoven_2020_introducing": "vecoven_2020_neuromodulat",     # Introducing neuromodulation in deep neural networks
    # Split by YEAR, not by surname: the arXiv v1 is 2024 and the venue is NeurIPS 2025, and
    # two digests recorded different years for the one paper. The same-author-same-year
    # warning cannot see this, which is why the collision check below also compares titles.
    "tessera_2025_hypermarl": "tessera_2024_hypermarl",
    # Split by surname PARSING: "Marquis & Farhood" keyed once as `marquis` and once as
    # `marquisfarhood`, depending on which delimiter the digest used.
    "marquisfarhood_2026_hypernetwork": "marquis_2026_farhood",
}

# One digest cell that names TWO papers. A digest wrote "Schaul et al. — UVFA; Borsa et al.
# — USFA" as a single row because both are universal value-function approximators cited
# together; they are separate works, published three years apart, and both are held as
# separate PDFs. Left merged, the corpus undercounts by one and the reference list could
# never match the paper statistics quoted on the page.
#
# Each entry replaces one parsed row with several. Fields not given are inherited from the
# row being split, since the shared cells (mechanism, site, claim strength) were written
# about both papers together.
SPLITS = {
    "schaul_2015_uvfa": [
        {"key": "schaul_2015_universal", "year": "2015",
         "paper": "Schaul et al. — Universal Value Function Approximators (UVFA)",
         "venue_raw": "ICML 2015"},
        {"key": "borsa_2018_universal", "year": "2018",
         "paper": "Borsa et al. — Universal Successor Features Approximators (USFA)",
         "venue_raw": "ICLR 2019"},
    ],
}


def paper_key(paper_cell: str, year: str) -> str:
    """First surname + year + first significant title word.

    The title token is not decoration. `Li et al. 2025` names two different papers in this
    corpus — CogVLA and Neuro-Vesicles — and a surname+year key silently merged them into
    one row, taking CogVLA's mechanism and Neuro-Vesicles' claim strength. Any first-author
    surname repeating within a year does the same, so the key carries a title token.
    """
    p = strip_md(paper_cell)
    p = re.sub(r"\(.*?\)", " ", p)
    # Split on a dash FIRST. Digests write the author list in two styles — "Yoon et al. —
    # PAPL" and "Yoon, Jeong et al. — PAPL" — and splitting on the comma first takes the
    # second author as the title token, which splits one paper into two rows.
    if re.search(r"\s(?:—|–|--)\s", p):
        parts = re.split(r"\s*(?:—|–|--)\s*", p, maxsplit=1)
    else:
        parts = re.split(r"\s*(?:,|\bet al\.?\b|&)\s*", p, maxsplit=1)
    surname = unicodedata.normalize("NFKD", parts[0]).encode("ascii", "ignore").decode()
    surname = re.sub(r"[^A-Za-z]", "", surname.split(",")[0].split(" et al")[0]).lower()
    tail = parts[1] if len(parts) > 1 else ""
    tail = re.sub(r"^(?:[A-Z][a-z]+(?:,\s*)?)*\bet al\.?\b\s*", " ", tail)  # residual author list
    tail = unicodedata.normalize("NFKD", tail).encode("ascii", "ignore").decode()
    words = [w for w in re.findall(r"[A-Za-z]+", tail.lower()) if w not in STOPWORDS]
    token = words[0][:12] if words else ""
    yr = re.sub(r"[^0-9]", "", year)[:4]
    base = surname or "unknown"
    return f"{base}_{yr}_{token}" if token else f"{base}_{yr}"


def parse_tables(path: Path) -> list[dict]:
    """Yield one dict per data row of every 10-or-more-column table in `path`."""
    rows: list[dict] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None
    for line in lines:
        if HEADER_RE.match(line):
            header = [strip_md(c) for c in line.strip().strip("|").split("|")]
            continue
        if header is None:
            continue
        if SEP_RE.match(line.strip()):
            continue
        if not line.startswith("|"):
            header = None          # table ended
            continue
        cells = [strip_md(c) for c in line.strip().strip("|").split("|")]
        if len(cells) < 10:
            continue
        rec = dict(zip(header, cells))
        rec["_source"] = path.name
        rows.append(rec)
    return rows


def col(rec: dict, *names: str) -> str:
    """Fetch the first present column among `names`, tolerant of header wording drift."""
    for n in names:
        for k, v in rec.items():
            if k.lower().startswith(n.lower()):
                return v
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--digests", type=Path, default=DEFAULT_DIGESTS)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "corpus.csv")
    args = ap.parse_args()

    src_files = sorted(
        [p for p in args.digests.glob("digest_*.md")]
        + [p for p in args.digests.glob("rows_*.md")]
    )
    if not src_files:
        print(f"ERROR: no digest_*.md or rows_*.md under {args.digests}", file=sys.stderr)
        return 1

    raw: list[dict] = []
    per_file = Counter()
    for f in src_files:
        got = parse_tables(f)
        per_file[f.name] = len(got)
        raw.extend(got)

    merged: dict[str, dict] = {}
    for rec in raw:
        paper = col(rec, "paper")
        year = col(rec, "year")
        if not paper or paper.lower() == "paper":
            continue
        key = paper_key(paper, year)
        key = ALIASES.get(key, key)
        row = {
            "key": key,
            "paper": paper,
            "year": re.sub(r"[^0-9]", "", year)[:4],
            "venue_raw": col(rec, "venue"),
            "mechanism_raw": col(rec, "mechanism"),
            "conditioner": col(rec, "conditioning signal"),
            "site_raw": col(rec, "injection site"),
            "rl_raw": col(rec, "RL algorithm"),
            "benchmark": col(rec, "benchmark"),
            "result": col(rec, "headline result"),
            "claim_raw": col(rec, "claim strength"),
            "sources": rec["_source"],
            "n_sources": 1,
        }
        if key not in merged:
            merged[key] = row
            continue
        # Merge free text only. Every classified field is derived AFTER the merge, below —
        # classifying first and merging second let a row keep a label computed from a cell
        # that the merge had already replaced, so `claim` and `claim_raw` disagreed on
        # exactly the rows whose reviewers had hedged hardest.
        old = merged[key]
        for field in ("venue_raw", "mechanism_raw", "conditioner", "site_raw",
                      "rl_raw", "benchmark", "result", "claim_raw", "paper"):
            if len(row[field]) > len(old[field]):
                old[field] = row[field]
        if not old["year"] and row["year"]:
            old["year"] = row["year"]
        if row["sources"] not in old["sources"]:
            old["sources"] += "; " + row["sources"]
            old["n_sources"] += 1

    # Split any row that names more than one paper. This runs BEFORE classification so each
    # part is classified from its own (inherited) text rather than copying a label computed
    # for the pair.
    for src_key, parts in SPLITS.items():
        if src_key not in merged:
            continue
        base = merged.pop(src_key)
        for part in parts:
            row = dict(base)
            row.update(part)
            row["sources"] = base["sources"] + f"; split from {src_key}"
            merged[row["key"]] = row

    # Derive every classified field from the merged free text, so a label always describes
    # the cell printed beside it in the CSV.
    for r in merged.values():
        r["venue_tier"] = classify_venue(r["venue_raw"])
        r["mechanism"] = classify_mechanism(r["mechanism_raw"])
        r["site"] = classify_site(r["site_raw"])
        r["cond_class"] = classify_conditioner(r["conditioner"])
        r["is_rl"] = classify_rl(r["rl_raw"])
        r["claim"] = classify_claim(r["claim_raw"])

    rows = sorted(merged.values(), key=lambda r: (r["year"] or "0000", r["key"]))

    # Near-duplicate warning. Two keys sharing a surname and year are usually two genuinely
    # different papers (Li 2025 is both CogVLA and Neuro-Vesicles), but they are also what a
    # false split looks like. Print them so the split is a decision rather than an accident.
    by_author_year: dict[str, list[str]] = {}
    for r in rows:
        by_author_year.setdefault("_".join(r["key"].split("_")[:2]), []).append(r["key"])
    collisions = {k: v for k, v in by_author_year.items() if len(v) > 1}
    if collisions:
        print("\nsame first author + year, kept as separate papers — check these are not one paper twice:")
        for k, v in sorted(collisions.items()):
            for key in v:
                title = next(r["paper"] for r in rows if r["key"] == key)
                print(f"   {key:34s} {title[:76]}")

    fields = ["key", "paper", "year", "venue_raw", "venue_tier", "mechanism_raw", "mechanism",
              "conditioner", "cond_class", "site_raw", "site", "rl_raw", "is_rl", "benchmark", "result",
              "claim_raw", "claim", "sources", "n_sources"]
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # Provenance sidecar. Figures read this so their data-declaration blocks report real
    # denominators rather than hand-typed ones (guide §11b).
    prov = {
        "n_rows_parsed": len(raw),
        "n_distinct_papers": len(rows),
        "n_merged_across_digests": sum(1 for r in rows if r["n_sources"] > 1),
        "rows_per_source_file": dict(per_file),
        "mechanism_counts": dict(Counter(r["mechanism"] for r in rows)),
        "venue_tier_counts": dict(Counter(r["venue_tier"] for r in rows)),
        "claim_counts": dict(Counter(r["claim"] for r in rows)),
        "rl_counts": dict(Counter(r["is_rl"] for r in rows)),
        "site_counts": dict(Counter(r["site"] for r in rows)),
        "conditioner_counts": dict(Counter(r["cond_class"] for r in rows)),
        "conditioner_counts_rl": dict(Counter(r["cond_class"] for r in rows if r["is_rl"] == "RL")),
        "year_range": [min((r["year"] for r in rows if r["year"]), default=""),
                       max((r["year"] for r in rows if r["year"]), default="")],
        "source_files": [f.name for f in src_files],
    }
    (args.out.parent / "corpus_provenance.json").write_text(json.dumps(prov, indent=2))

    print(f"parsed {len(raw)} table rows from {len(src_files)} files")
    for name, n in per_file.items():
        print(f"   {n:3d}  {name}")
    print(f"→ {len(rows)} distinct papers ({prov['n_merged_across_digests']} merged across digests)")
    print("   mechanism:", prov["mechanism_counts"])
    print("   venue    :", prov["venue_tier_counts"])
    print("   claim    :", prov["claim_counts"])
    print("   rl       :", prov["rl_counts"])
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
