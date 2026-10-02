"""Shared paths and helpers for the 'Body Rules and the Modulator' page figures (level-05
body-interactions factorial, docs/experiments/active/level05_body_interactions/).

Same house pattern as scripts/analysis/studies/internal_state_interactions/_common.py. This folder
sits FOUR levels below the repo root (scripts/analysis/studies/level05_body_interactions/page/),
one deeper than the study's own analysis scripts, so ROOT walks five '..'.

Colour: on this project's pages blue / orange / green already mean rest-in-cover / warm-up / eat, so
these figures spend no hue on data. Agents and nutrition bands are told apart by ink vs grey and by
marker shape (and line style), never by colour alone.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house                                                          # noqa: E402
from figguards import (assert_min_text_px, assert_no_text_overlap,   # noqa: E402,F401
                       assert_ticks_dont_collide, COLUMN_PX)

OUT = os.path.join(ROOT, "results/analysis/level05_body_interactions")
PAGE_OUT = os.path.join(OUT, "page")          # data derived here for the page (shard_cells.py)
FIG = os.path.join(ROOT, "docs/experiments/active/level05_body_interactions/figures")

KIND = {"recordings": "recordings — trained agents' own evaluation episodes, final checkpoint",
        "training": "training logs — WandB, last tenth of training"}

# The four body rules, in world-code order (w<B5><B3><A1><A4>), in plain words.
RULES = ["healing slower when hungry", "healing uses up food",
         "being cold or hot uses up food", "less food per bite"]
RULE_HEAD = ["healing\nslower\nwhen\nhungry", "healing\nuses up\nfood",
             "cold or\nhot uses\nup food", "less\nfood per\nbite"]
FACTORS = ["B5", "B3", "A1", "A4"]            # the design doc's names, same order
WORLDS = [f"w{i:04b}" for i in range(16)]

# The two agents: ordinary = filled ink circle, modulator = open ink square (as on c1 of the
# internal-state page). Grey is the second series where two lines must differ without markers.
GREY = "#8a8f99"
AGENT = {"ordinary": dict(marker="o", mfc=house.INK, mec=house.INK, label="ordinary agent"),
         "modulated": dict(marker="s", mfc="none", mec=house.INK, label="modulator agent")}

SMALLEST_PT = 9.5         # every hand-set text size in these figures; the ticks are 11 pt
FLOOR_PX = 685            # the page's .figscroll min-width; see save()


def rules_on(world):
    return [RULES[i] for i, b in enumerate(world[1:]) if b == "1"]


def world_words(world):
    on = rules_on(world)
    return "plain level 05 (no rule on)" if not on else ("all four rules" if len(on) == 4 else " + ".join(on))


def load(name):
    return json.load(open(os.path.join(OUT, name)))


def draw_rule_matrix(ax, worlds, y):
    """Left-hand panel shared by the per-world figures: one column per body rule, a filled dot
    where the rule is on in that row's world, a faint ring where it is off. Column headings are
    the rules in plain words, so no world code is ever printed."""
    for j in range(4):
        for w, yy in zip(worlds, y):
            on = w[1 + j] == "1"
            ax.plot([j], [yy], "o", ms=7.5 if on else 5, mfc=house.INK if on else "none",
                    mec=house.INK if on else house.RULE, mew=1.0, zorder=3)
    ax.set_xlim(-0.6, 3.6)
    ax.set_xticks(range(4)); ax.set_xticklabels(RULE_HEAD, fontsize=SMALLEST_PT, color=house.INK)
    ax.xaxis.tick_top()
    ax.set_yticks([]); ax.grid(False)
    for yy in y:
        ax.axhline(yy, color=house.TICK_LINE, lw=0.6, zorder=0)


def record_samples(stem, rows):
    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(FIG, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            assert "|" not in r["what"] + r["note"], f"'|' is the field separator: {r}"
            pct = 100.0 * r["used"] / r["total"] if r["total"] else 0.0
            u = f"{r['used']:,}" if isinstance(r["used"], int) else r["used"]
            t = f"{r['total']:,}" if isinstance(r["total"], int) else r["total"]
            fh.write(f"{r['what']}|{u}|{t}|{pct:.1f}|{r['note']}\n")
    print(f"  wrote {stem}.data.txt ({len(rows)} rows)")


def record_kind(stem, kind):
    assert kind in KIND, kind
    os.makedirs(FIG, exist_ok=True)
    open(os.path.join(FIG, f"{stem}.kind.txt"), "w").write(kind + "\n")


def save(fig, stem):
    """Guards, then house.save, then the phone-floor check on the SAVED raster.

    The page gives every figure `.figscroll img { min-width: 685px }` (F65): below that width the
    image scrolls instead of shrinking. That only keeps the smallest text at >= 9 px if the saved
    canvas is narrow enough: 9.5 pt at 220 dpi is 29.0 px, so the PNG must be at most
    685 x 29.0 / 9 = 2209 px wide. bbox_inches='tight' can widen a canvas past its figsize, so
    this is checked on the file, not on figsize."""
    assert_no_text_overlap(fig)
    assert_min_text_px(fig)
    dpi = fig.dpi
    house.save(fig, os.path.join(FIG, stem), column_px=COLUMN_PX)
    from PIL import Image
    w = Image.open(os.path.join(FIG, f"{stem}.png")).size[0]
    small_px = SMALLEST_PT * dpi / 72.0
    need = w * 9.0 / small_px
    if need > FLOOR_PX:
        raise SystemExit(f"{stem}: canvas {w}px needs a {need:.0f}px phone floor for 9px text, "
                         f"above the page's {FLOOR_PX}px; narrow the figure")
    print(f"  {stem}: canvas {w}px, phone floor needed {need:.0f}px (page gives {FLOOR_PX}px)")
