"""Shared figure style for the FiLM/hypernetwork-in-RL field review.

Two jobs, both of them defect prevention rather than decoration.

**One colour, one meaning (format-register F11).** Every mechanism, venue tier and claim
strength gets its colour here and nowhere else. A reader who learns on figure 1 that amber
means "hypernetwork" must be able to carry that to figure 4. Palettes are capped at six
entries because F12 records that more than about six series distinguished by colour alone
stop being distinguishable.

**Opaque backgrounds (F30).** Figures are saved with an explicit white face colour, never
`transparent=True`. A transparent PNG inherits the reader's theme ground while its ink stays
the one colour it was drawn in, which is how two plots once shipped as empty rectangles in
dark mode. The page places these on a light plate in both themes for the same reason.

**Sample recording (guide §11b).** `record_samples` writes each figure's used / available /
percentage breakdown to a JSON sidecar that the page builder reads. These counts are emitted
here and never typed into the HTML, so a figure whose filter changes cannot silently keep an
old denominator.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).parent
FIGDIR = HERE / "figures"
SAMPLES = FIGDIR / "_samples.json"

# --- palette -------------------------------------------------------------------------
# Page chrome is a deep indigo and is deliberately absent from every data palette below
# (F11 amendment: page chrome must not borrow the data palette).
INK = "#171B21"
MUTED = "#5C6773"
GRID = "#DFE3E8"
PAPER = "#FFFFFF"

# --- the colour contract -------------------------------------------------------------
# A format review found teal carrying FOUR meanings across the figure set — FiLM, then
# "encoder site", then "runs an RL algorithm", then "ablated" — with the page's own chrome
# borrowing it for a fifth. That is F11 and its amendment, and it is exactly what this
# module's docstring promised not to do.
#
# The contract now: the six MECHANISM_COLORS are spent on figure 1 and NOWHERE else. Every
# other figure encodes an ordinal or a binary, so each uses a single-hue steel ramp, where
# darker means "more" of whatever that figure's axis measures. Nothing carries a semantic
# hue it does not own, and the page's chrome uses its indigo accent, which appears in no
# palette here.
MECHANISM_COLORS = {
    "FiLM": "#1F8A8F",            # teal — the affine operator
    "hypernetwork": "#C2681B",    # amber — generated weights
    "routing": "#6E4E9E",         # purple — conditional computation
    "attention": "#B03A5B",       # rose
    "plasticity": "#4A7C3F",      # green — modulates the update, not the activation
    "concatenation": "#7A8590",   # grey — the negative control, deliberately colourless
    "other": "#B9C0C8",
}

# Single-hue steel ramp, dark → light. Used wherever the categories are ordered.
STEEL = ["#2B4A5E", "#41647A", "#5C8096", "#7D9CAF", "#A2BAC8", "#C6D4DD"]
NEUTRAL = "#B9C0C8"      # always and only "other / unclassified"
PRIMARY = "#41647A"      # the single-series colour, for figures with one meaning

# Ordinal: strongest evidence darkest. Not semantic — no green-good / amber-bad here.
CLAIM_COLORS = {
    "ablated": STEEL[0],
    "ablated-qualified": STEEL[2],
    "asserted": STEEL[3],
    "no-experiment": STEEL[4],
    "unverified": NEUTRAL,
    "unclassified": "#D6DBE0",
}

VENUE_COLORS = {
    "top-tier": STEEL[0],
    "other-peer-reviewed": STEEL[2],
    "workshop": STEEL[3],
    "preprint": STEEL[4],
    "unclassified": NEUTRAL,
}

MECHANISM_ORDER = ["FiLM", "hypernetwork", "routing", "attention", "plasticity",
                   "concatenation", "other"]
CLAIM_ORDER = ["ablated", "ablated-qualified", "asserted", "no-experiment",
               "unverified", "unclassified"]
VENUE_ORDER = ["top-tier", "other-peer-reviewed", "workshop", "preprint", "unclassified"]


def load_corpus() -> list[dict]:
    with (HERE / "corpus.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": PAPER,
        "axes.facecolor": PAPER,
        "savefig.facecolor": PAPER,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def record_samples(stem: str, rows: list[dict]) -> None:
    """Record a figure's used/available breakdown. `rows` = [{what, used, total, note}]."""
    FIGDIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(SAMPLES.read_text()) if SAMPLES.exists() else {}
    for r in rows:
        r["pct"] = round(100.0 * r["used"] / r["total"], 1) if r["total"] else 0.0
    data[stem] = rows
    SAMPLES.write_text(json.dumps(data, indent=2))


def finish(fig, stem: str) -> None:
    """Save opaquely, at a width the page can show, and report the path."""
    FIGDIR.mkdir(parents=True, exist_ok=True)
    out = FIGDIR / f"{stem}.png"
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    print(f"wrote {out}")
