#!/usr/bin/env python
"""Pixel-overlap audit for episode-dashboard frames (RENDERER_LAYOUT_REDESIGN.md §D5.2).

WHAT THIS IS. The renderer redesign claims that panel overlap becomes structurally
impossible rather than hand-tuned away. That claim is only checkable if overlap can be
MEASURED in rendered pixels, so this script is the measuring instrument. It takes frames
from the production render path — a real `.rec.gz` recording, rendered by a real renderer,
not a figure, not a layout tree — and reports where drawn content collides.

It imports NEITHER the layout module NOR the panel registry (neither exists yet), and it
never asks a painter to declare which of its own ink is exempt. Its ground truths are the
rendered pixels and `get_observation_breakdown(params)`.

────────────────────────────────────────────────────────────────────────────────────────
WHAT COUNTS AS INK  (and why it is measured by ISOLATION, not by hiding)

An element's ink is the set of pixels it puts on the canvas, measured as:

    ink(E) = { p : |render(only E visible)[p] - render(nothing visible)[p]| > INK_DELTA }

§D5.2 item 2 describes the opposite operation — render once, then re-render with the
element HIDDEN, and call the difference its ink. That definition is wrong for exactly the
case this audit exists to find. If text is drawn opaquely on top of a card border, hiding
the border changes no pixel there (the text still covers them), so the border's "ink"
excludes the overlapped region, the intersection comes out empty, and the collision is
reported as clean. Isolation has no such blind spot: each element is measured against the
bare background, so two elements that fight over a pixel both claim it. This is a
deliberate, stated departure from the plan's wording; the plan's intent (pixels, not tags)
is preserved and strengthened.

A pixel counts as ink at a per-channel difference > INK_DELTA = 8/255. Below that is
anti-aliasing and alpha-blending noise that no viewer can see. A patch filled in the
background colour therefore has only its border as ink, which is correct and is what makes
the "text on a panel edge" rule work at all.

────────────────────────────────────────────────────────────────────────────────────────
WHAT COUNTS AS A COLLISION, AND THE TOLERANCE

Elements are classified FOREGROUND or BACKGROUND by artist TYPE and GEOMETRY only — never
by a painter's tag or `gid` (§D5.2 item 1, review finding 3):

  BACKGROUND (demoted)  filled patches covering >= BG_FRACTION of their axes (card fills),
                        images covering >= BG_FRACTION of their axes (thermal underlay,
                        minimap raster), and lines/collections spanning >= BG_FRACTION of
                        their axes in both directions (grid lines).
  FOREGROUND            everything else that draws: every Text; every unfilled patch
                        (card borders, spines) WHATEVER its size; bar fills, tiles, ticks,
                        icons, glyphs, scatter dots.

Findings, in the families the audit is asked to measure:

  text_over_text    a Text's ink, dilated by DILATE = 1 px, shares >= MIN_OVERLAP_PX
                    pixels with another Text's ink.
  text_over_border  the same, where the partner is an unfilled patch or a spine — i.e. a
                    panel edge. Text on a border is FORBIDDEN, not tolerated (§D5.2 item
                    3): a card edge is the panel's own outline, and a label lying across
                    it belongs to neither side of it.
  text_over_fill    the same, where the partner is any other foreground element (a bar
                    fill, an icon, a tile) and THE LABEL IS COMPOSED LAST, so what the
                    frame shows at the shared pixels is the glyph. A number drawn inside
                    its own bar with a halo is this case and is legible by design.
                    Counted and reported; it is NOT one of the calibrated controls.
  fill_over_text    the same collision, except that the partner is composed AFTER the text
                    and covers some of the text's own (undilated) ink — the reader is
                    shown drawn content where a glyph should be. A defect whatever the
                    intent. THIS CLASS IS NOT BENIGN and must not be reported as though it
                    were: it is how a label silently loses part of itself.

                    WHY COMPOSITION ORDER, AND NOT A PIXEL TEST. Three discriminators were
                    implemented and MEASURED on the eleven fill collisions of V1 M4 and
                    V2 M4 before this one was kept:

                      (A) hide the text, and call its ink pixels "lost" where the frame
                          does not change. FALSE POSITIVE on the body-temperature readout:
                          its white halo blends to within INK_DELTA of the #F3F4F6 card
                          behind it, so 29 px read as "covered" with nothing covering them.
                      (B) compare a solo render of the text against text+partner. FALSE
                          POSITIVE on all four thermoception cell readings (33-43 px each)
                          and on V2's GRS label, because the solo render has the BARE
                          canvas behind the glyph, so every anti-aliased edge pixel differs
                          whatever the paint order.
                      (C) composition order, kept: does the partner draw after the text
                          within the same Axes (zorder first, then insertion order), and is
                          any of the text's RAW ink actually shared.

                    Anti-aliasing is what defeats (A) and (B): a glyph's fringe pixels are
                    mostly background by construction, so a colour test on them measures
                    the blend rather than the occlusion. (C) is NOT the classification-by-
                    declaration that §D5.2 item 1 forbids — no painter is asked which of
                    its own ink to ignore; this is the order matplotlib composed the image
                    in. And it was CHECKED against the pixels at the decisive (solid-ink)
                    pixels of all eleven collisions: where (C) says the partner is on top
                    the frame shows the partner's colour exactly and the glyph's not at all
                    (`+84`: final [103 0 31] = the strip segment, 157 and 243 away from the
                    text drawn alone); where (C) says the label is on top, the frame shows
                    the glyph (0-3 away from the text drawn alone).

                    Measured: 5 of the 6 fill collisions on V1 M4, and all 5 on V2 M4, are
                    labels composed last. The one exception is the thermal scale's `+84`
                    end label, 2 px of whose `+` are painted over by the colour strip's
                    last segment — structural, and independent of the world: the label is
                    anchored at axes-fraction x 0.77000 with ha='left' while the strip's
                    52nd segment runs to 0.77220, because each segment is drawn
                    strip_w/51 + 0.002 wide to close the hairline gaps between segments.
  out_of_card       a Text with ink in a card's TITLE STRIP — the band between the card's
                    top edge and its own title. That band belongs to the title alone, so a
                    label there has escaped the card whose content it labels and reads as
                    part of the title line. This is the "content outside its allotted box"
                    family, and on a renderer whose panels share one Axes it is the only
                    way to state that idea: V1 draws a whole column into a single Axes, so
                    "outside its axes" is vacuous and the CARD is the real box.
  clipped           a Text whose ink touches the canvas edge.

                    ONLY the canvas-edge half is implemented, deliberately. The other half
                    a reader might expect — "re-render with the clip path removed and see
                    whether the glyph grows" — is absent because, MEASURED on both
                    renderers, there is nothing for it to measure: of 103 texts on V1 M4
                    and 54 on V2 M4, exactly ZERO have a clip path or a clip box set (49
                    and 10 respectively carry the `clip_on` flag, which here clips against
                    nothing). Writing it now would add an extra render per text to execute
                    a branch no fixture can enter — untestable dead code. The redesign's
                    painters DO clip text to their panel; the half gets written, with a
                    fixture that exercises it, in the phase that introduces them.
  out_of_canvas     any foreground ink inside the outer CANVAS_MARGIN_PX of the frame.

Border-vs-fill is decided from MEASURED INK, not from a declared face colour: an element
whose ink lies on the perimeter of its own bounding box is an outline. V1's cards are
filled in the background colour, so an alpha test calls them solid while the canvas shows
only their edge — and "text on a panel edge" is precisely a forbidden case.

Tolerances, stated so they can be argued with later:
  INK_DELTA        = 8     per-channel 0-255 difference for a pixel to count as ink
  DILATE           = 1 px  text ink is grown by one pixel before intersecting (§D5.2 item 3)
  MIN_OVERLAP_PX   = 2 px  a single shared pixel is an anti-aliasing touch, not a defect
  BG_FRACTION      = 0.90  the plan's 90% rule for demoting an element to background
  CANVAS_MARGIN_PX = 4     the plan's outer-margin rule (§D5.2 item 9)

The text_over_fill / fill_over_text split adds NO tolerance of its own: it asks only
whether the partner is composed after the text and whether any raw ink is shared. There is
exactly one hand-chosen number in this file beyond
the five above — the title strip's "one title line" bound (2.0x the title's own ink
height, at `_title_strips`) — and it survives a sweep from 1.0 to 7.8 without changing a
single verdict on the control frame.

Every finding reports the measured overlap in pixels and its bounding box, so a reader can
see how much margin a control passed or failed by rather than trusting a boolean.

────────────────────────────────────────────────────────────────────────────────────────
THE OTHER RULES (ground truth = the observation breakdown, not the renderer)

  panel_absent      (§D5.2 item 6) For every name in `get_observation_breakdown(params)`,
                    the frame must carry a panel title that maps to it, via the fixed
                    TITLE_TABLE below, with non-empty ink, not marked OFFLINE. A name with
                    no such title is a silently dropped panel.
  observed_caption  (§D5.2 item 7) Any text starting `OBS`/`REAL`, or containing
                    "obs only", must belong to a panel whose title maps to a breakdown
                    name that is PRESENT. Captioning a hidden state value as observed is a
                    false claim about what the agent can sense.
  legibility        (§D5.2 item 5) Every text's rendered size >= --text-floor-px. V1 and
                    the dormant V2 are judged at the old 8 pt floor (11.1 px at 100 dpi),
                    not at the redesign's 14 px floor.
  numeric_in_arena  (§D5.2 item 10) No Text containing a digit or sign has ink inside the
                    arena's extent. Enabled with --arena-axes NAME, because the arena can
                    only be NAMED, never guessed: V1 draws its arena into an UNLABELLED
                    Axes, so the rule cannot run on V1 at all, while the dormant V2 labels
                    its axes (`arena`, `thermoception`, `visual`, …) so
                    `--renderer v2 --arena-axes arena` runs it against a real frame.

────────────────────────────────────────────────────────────────────────────────────────
CO-OCCUPANCY: DOES A SQUARE SHOW EVERY OCCUPANT IT HOLDS?  (`cell_overdraw`, §D5.2 item 11,
specified in §R19.1 and re-scoped by §R20.1–§R20.8)

The redesign exists because a square holding two animals was drawn as one animal. That is
only checkable if "how many occupants can a viewer actually see here" is MEASURED, and the
measurement has to survive a painter that draws the right thing in the right place and
then paints something over it. So this rule measures THREE things per square, not one:

  isolated ink       what each element lays down alone (`FrameProbe.ink`) — the original
                     check, and what catches a painter that draws two occupants
                     concentrically (one component where the snapshot says two).
  visible token ink  the pixels at which NO element drawn afterwards has ink. A token
                     drawn correctly and then covered keeps all of its isolated ink, so
                     an isolated-ink rule alone passes the exact defect this exists for.
  survival floor     per component, `|surviving| / |isolated| >= SURVIVAL_MIN`. A token
                     95 % hidden still leaves one component and would pass any pure
                     component count. A correct composition measures 1.000.

Ground truth is the snapshot's set of DISTINCT NON-TERRAIN KINDS at that square — kinds,
never instances (§R17.5 item 1): two predators in one square are one predator token by
design, and an instance count would report a failure that is not one.

Excluded from the token union, BY MEASUREMENT and never by a painter's tag:
  * an element whose ink covers >= CELL_FLOOR_FRACTION (40 %) of the square is the bed or
    the ground — the floor the occupants stand on, not an occupant;
  * an element whose ink sits on the perimeter of ITS OWN bounding box (`_ink_is_outline`)
    is a square outline or a seam. The agent's 2 px iris outline is the case that matters:
    left in, it runs around the rim and bridges two tokens into one component, failing a
    CORRECT painter. It stays in the OCCLUDER set — only the assertion narrows.
    Guard, in the failing direction (§R20.7 item 1): an outline-classified element whose
    bbox spans under OUTLINE_SPAN_MIN (80 %) of the square is reported as
    `outline_like_token` and FAILS rather than quietly leaving the count — a ring-shaped
    token part drawn as its own artist is exactly that shape.

THE NARROWING RULE, which is the invariant this section must not break (§R20 head). A fix
here may narrow WHICH ELEMENTS AND PIXELS THE RULE ASSERTS THINGS ABOUT. It may never
narrow WHICH ELEMENTS ARE CAPABLE OF COVERING A TOKEN: the occluder set stays "every
element in the figure". Every precondition below is therefore scoped to `L(p)` — the
last-drawn element with ink at token pixel `p` — and `L(p)` is COMPUTED FROM THE FULL
OCCLUDER SET, so the narrowing consumes that set rather than editing it. A painter-set
property (alpha, face colour, outline shape) may be read ONLY where reading it can make
the rule FAIL; nothing may ever be read to EXEMPT ink from the count. That is finding #3's
discipline — the audit never lets the painter under test declare which of its own ink is
off-limits — carried into this rule. The shortcut this forbids (stop counting translucent
things, or outlines, as able to cover anything) would silence a false alarm and SILENTLY
re-open the draw-order hole the rule exists to close.

Three preconditions, which FAIL rather than skip, because "what was drawn last" is only a
valid proxy for "what the viewer sees" under them:

  (a′) opacity where it decides   If `L(p)` is not a token element of that square it must
       be fully opaque (artist alpha None/1.0, no RGBA face or edge alpha below 1). A
       translucent element above a token is not an occlusion a viewer can see through, so
       the rule would be wrong in both directions. Scoped to `L(p)`, NOT arena-global: the
       agent's own halo (alpha 0.16) and shadow (0.12) are token elements of their own
       square, and an arena-global demand fails every frame that has an agent in it.
  (b′) one Axes where it decides  `L(p)` must belong to the named arena Axes.
       `_is_painted_over` returns False across two Axes, so token ink drawn into a foreign
       Axes would be silently un-orderable and would pass. Scoped to `L(p)`, NOT
       arena-global: the page's background rectangle lies under the whole arena in its own
       Axes and is never `L(p)`, so an arena-global demand fails every frame.
  (c′) probe visibility           An element whose every declared paint lies within
       INK_DELTA (8/255) of the FIGURE FACECOLOR has no isolated ink at all — so it can
       never be `L(p)` and cannot occlude anything as far as this instrument is concerned.
       That is the one genuinely silent case in the pass, and it is not hypothetical: the
       arena's neutral ground `TRACK #ECEEEA` is 5–6/255 from the page colour
       `CANVAS #F2F3F0`, so a renderer that set `fig.set_facecolor(CANVAS)` — a natural
       thing to do — would make "the ground was painted over the animals" UNDETECTABLE.
       Mutation M-F1g is that exact frame, and without (c′) it passes silently.

The composition comparator is extended to rank ACROSS Axes as `(axes rank, zorder, child
index)` — matplotlib's own composition rule, not a new invention — because `L(p)` cannot
be found at all with a comparator that refuses to order two Axes. The derivation is pinned
by a rendered two-Axes control rather than trusted. The rank is built ONCE per frame as
`dict[id(artist) -> rank]`; the previous per-pair `_draw_index` scan is O(N) per
comparison, which a 100-square arena cannot afford.

The only permitted exclusion from the WORK (never from the occluder set) is an element
whose REACH_PAD_PX-padded bbox cannot meet a square: the padded bbox bounds the element's
ink, so `L(p)` is unchanged by construction, and a control asserts both ways give
identical findings.

The MINIMAP variant is measured on the COMPOSITE, not by isolation — isolation would call
a split dot correct even when one half is painted over the other, which is the exact
defect §R17.4 exists to prevent. Its ground truth is the distinct palette colours the
KINDS present map to (two predators are one colour, not two movers), and its area
denominator is the SAME census run on the isolated wedge, so edge blends are excluded from
numerator and denominator alike and a correct dot measures ~1.000. A geometric wedge would
be unreachable on a correct ~13 px dot, a third to a half of whose pixels are blends.

Tolerances added by this rule, all argued above:
  SURVIVAL_MIN         = 0.98   per-component surviving fraction (swept at CP0.3b)
  CELL_FLOOR_FRACTION  = 0.40   ink area share at which an element IS the floor
  OUTLINE_SPAN_MIN     = 0.80   bbox span below which an "outline" is a suspect token
  REACH_PAD_PX         = 2      bbox padding for the work-only reach test
  MINIMAP_DELTA        = 12     per-channel distance for the minimap colour census

Tolerance between components is ZERO shared pixels, with NO dilation: the 1 px dilation in
the text rules exists for glyph anti-aliasing and is wrong here.

────────────────────────────────────────────────────────────────────────────────────────
CALIBRATION — the reason this file exists at all

An instrument nobody has calibrated is worthless, so the audit ships with POSITIVE
CONTROLS: known, real defects in today's V1 output and in the dormant V2 output that it
MUST flag (CP0.3). `--controls` runs them and prints, per control, whether it fired, on
which elements, at which coordinates, and by how many pixels. A control that fires for the
wrong reason (right frame, wrong collision) counts as NOT fired — both participants are
checked, not just the count. If any control misses, the audit is not sensitive enough to
be trusted and the exit code is non-zero.

SENSITIVITY IS ONLY HALF OF CALIBRATION. An instrument that flagged EVERYTHING would pass
every positive control above, so the controls alone cannot tell this audit apart from one
that always says yes. What rules that out lives in `tests/env/test_render_audit_controls.py`
as NEGATIVE controls: the exact SET of absent panels on V1 M4, and the exact per-rule
finding COUNT on two frozen frames — including the rules that must stay SILENT on them.
Those counts are exact rather than lower bounds on purpose, and a mutation test proves
they break when `FrameProbe.ink()` is made to return all-True.

USAGE
    python scripts/eval/render_layout_audit.py --controls
    python scripts/eval/render_layout_audit.py --cell M4 --renderer v1 --step 0
    python scripts/eval/render_layout_audit.py --cell M1 --renderer v1 --steps 0 1 2
    python scripts/eval/render_layout_audit.py --rec-dir results/.../recordings/X --renderer v2
    python scripts/eval/render_layout_audit.py --cell M4 --renderer v2 --arena-axes arena

Frames come from `results/render_audit/recordings/<cell>/<cell>/` (written by
`scripts/eval/make_render_fixture_recordings.py`). The frozen V1 files are imported and
executed READ-ONLY; nothing here edits one. Matplotlib's pyplot is patched during a render
only to keep the Figure alive after the renderer would have closed it — no frozen file is
touched, and the captured figure is proven byte-identical to the returned frame before any
measurement is taken.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.artist import Artist  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.axis import Axis, Tick  # noqa: E402
from matplotlib.collections import Collection  # noqa: E402
from matplotlib.figure import Figure, SubFigure  # noqa: E402
from matplotlib.image import AxesImage, BboxImage  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.offsetbox import AnnotationBbox  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.spines import Spine  # noqa: E402
from matplotlib.text import Text  # noqa: E402

# ---- tolerances (see the module docstring; every one of these is argued there) -------
INK_DELTA = 8
DILATE = 1
MIN_OVERLAP_PX = 2
BG_FRACTION = 0.90
CANVAS_MARGIN_PX = 4
# Legibility floor, in rendered px. DEFAULT OFF (0.0), deliberately. The plan judges V1
# control frames "at the old 8 pt floor", but V1 draws most of its labels at 4-7 pt, so an
# 8 pt floor reports ~40 findings per frame on a renderer that is frozen and will not be
# fixed — noise that buries the defects this audit exists to find. The rule is kept and is
# enabled explicitly with --text-floor-px (the redesign's floors are 14 px / 12 px).
DEFAULT_TEXT_FLOOR_PX = 0.0

DEFAULT_FIXTURE_ROOT = "results/render_audit/recordings"

# Panel title (as RENDERED, normalised) -> observation-breakdown name. Read from pixels,
# never from a registry: this is the §D5.2 item 6 "fixed title table in the audit module".
TITLE_TABLE = {
    "SATIATION": "Satiation",
    "NUTRITION": "Nutrition",
    "INJURY": "Injury",
    "INTERO NOC": "Interoceptive Nociception",
    "INTEROCEPTIVE NOCICEPTION": "Interoceptive Nociception",
    "INOC": "Interoceptive Nociception",
    "BODY TEMP": "Body Temperature",
    "BODY TEMPERATURE": "Body Temperature",
    "EXTERO NOCICEPTION": "Extero Nociception",
    "THERMOCEPTION": "Thermoception",
    "OLFACTORY": "Olfaction",
    "OLFACTION": "Olfaction",
    "COLLISION": "Collision",
    "VISUAL": "Visual",
    "LOC": "Location",
    "LOCATION": "Location",
    "PROPRIOCEPTION": "Proprioception",
}

_TITLE_SUFFIXES = ("(OBS ONLY)", "OFFLINE", "(OFFLINE)")


class AuditError(Exception):
    """The audit cannot produce a trustworthy verdict."""


# ------------------------------------------------------------------ frame construction


class _Snap:
    """Attribute view over a snapshot dict — the shim render_recordings.py builds."""


def _snap_shim(snap):
    s = _Snap()
    for k, v in snap.items():
        setattr(s, k, v)
    return s


@dataclasses.dataclass
class FrameInputs:
    rec_dir: Path
    params: object
    icon_config: object
    state: object
    sensory_data: list
    action: object
    step: int
    n_steps: int
    episode_index: int
    thermal_clim: object
    breakdown: dict


def load_inputs(rec_dir: Path, step: int, episode: int = 0) -> FrameInputs:
    """Build one step's renderer inputs exactly as `render_recordings._render_episode` does."""
    from src.environment.renderer import thermal_color_limits
    from src.environment.sensor import build_sensory_viz, get_observation_breakdown
    from src.utils.eval_recording import load_episode, load_run_meta

    if not rec_dir.is_dir():
        raise AuditError(f"recordings directory not found: {rec_dir}")
    eps = sorted(rec_dir.glob("episode_*.rec.gz"))
    if not eps:
        raise AuditError(f"no episode_*.rec.gz in {rec_dir}")
    meta = load_run_meta(rec_dir)
    params = meta["params"]
    ep = load_episode(eps[episode])
    n = len(ep["snapshots"])
    if not 0 <= step < n:
        raise AuditError(f"step {step} out of range for {eps[episode].name} ({n} snapshots)")

    snap = ep["snapshots"][step]
    state = _snap_shim(snap)
    true_obs = ep["true_obs"][step] if ep["true_obs"] is not None else None
    sensory = build_sensory_viz(ep["obs"][step], state, params, true_obs)
    action = int(ep["actions"][step]) if ep["actions"][step] >= 0 else None
    # Pinned ONCE from snapshot 0, exactly as the production offline renderer does.
    clim = thermal_color_limits(ep["snapshots"][0].get("thermal_field"), params)
    return FrameInputs(rec_dir, params, meta["icon_config"], state, sensory, action,
                       step, n, ep["episode_index"], clim,
                       dict(get_observation_breakdown(params)))


def render_capture(renderer: str, fi: FrameInputs):
    """Render one frame and keep its Figure alive. Returns (frame, figure).

    pyplot's `figure`/`close` are patched for the duration of the call ONLY so the Figure
    survives the renderer's own `plt.close`. No frozen file is modified, and the caller
    proves the captured figure redraws byte-identically before measuring anything.
    """
    plt.close("all")
    created, orig_figure, orig_close = [], plt.figure, plt.close

    def _spy(*a, **k):
        f = orig_figure(*a, **k)
        created.append(f)
        return f

    plt.figure, plt.close = _spy, (lambda *a, **k: None)
    try:
        if renderer == "v1":
            from src.environment.renderer import render_jax_state
            frame = render_jax_state(
                fi.state, fi.params, episode=fi.episode_index, step=fi.step,
                train_episode=None, action=fi.action, sensory_data=fi.sensory_data,
                info=None, icon_config=fi.icon_config, thermal_clim=fi.thermal_clim)
        elif renderer == "v2":
            from src.environment.renderer_v2 import render_jax_state_v2
            frame = render_jax_state_v2(
                fi.state, fi.params, episode=fi.episode_index, step=fi.step,
                train_episode=None, action=fi.action, sensory_data=fi.sensory_data,
                info=None, icon_config=fi.icon_config)
        else:
            raise AuditError(f"unknown renderer {renderer!r} (expected 'v1' or 'v2')")
    finally:
        plt.figure, plt.close = orig_figure, orig_close
    if not created:
        raise AuditError(f"renderer {renderer!r} created no figure to audit")
    return np.asarray(frame), created[-1]


# ------------------------------------------------------------------------- elements


@dataclasses.dataclass
class Element:
    artist: Artist
    kind: str            # 'text' | 'border' | 'patch' | 'image' | 'line' | 'collection'
    text: str | None
    bbox: tuple          # (x0, y0, x1, y1) in display coords, origin bottom-left
    layer: str           # 'foreground' | 'background'
    axes_name: str

    @property
    def label(self) -> str:
        if self.kind == "text":
            return f"text {self.text!r}"
        return f"{self.kind} {type(self.artist).__name__} in {self.axes_name}"


def _axes_name(art) -> str:
    ax = getattr(art, "axes", None)
    if ax is None:
        return "figure"
    return getattr(ax, "get_label", lambda: "")() or f"axes@{id(ax) % 10000}"


def _is_unfilled(p: Patch) -> bool:
    """A border: no fill, or a fully transparent face, but a visible edge."""
    try:
        fc = p.get_facecolor()
        ec = p.get_edgecolor()
    except Exception:
        return False
    face_alpha = fc[3] if (fc is not None and len(np.shape(fc)) == 1 and len(fc) == 4) else 1.0
    edge_alpha = ec[3] if (ec is not None and len(np.shape(ec)) == 1 and len(ec) == 4) else 0.0
    if isinstance(p, Spine):
        return edge_alpha > 0
    return bool(face_alpha <= 0.01 and edge_alpha > 0)


def _ink_is_outline(mask: np.ndarray, bbox, height: int) -> bool:
    """True when an element's ink sits on the PERIMETER of its bbox, not in its middle.

    Border-vs-fill is decided from measured pixels, not from a declared face colour.
    V1's cards are `Rectangle`s filled in the BACKGROUND colour with a visible edge: an
    alpha test calls them filled, while on the canvas the only ink they lay down is their
    outline. A label lying across one is text-on-a-panel-edge, which §D5.2 item 3
    forbids outright, so getting this class right decides whether a real defect is
    reported as the thing it is.
    """
    total = int(mask.sum())
    if total == 0:
        return False
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return False
    core = _rect_mask(mask.shape[0], mask.shape[1],
                      x0 + 0.25 * w, y0 + 0.25 * h, x1 - 0.25 * w, y1 - 0.25 * h)
    return bool(int((mask & core).sum()) / total < 0.02)


def _collection_extent(art):
    """Display-coordinate extent of a Collection, taken from its OWN paths.

    `Collection.get_window_extent` returns an EMPTY bbox — `(inf, inf, -inf, -inf)` —
    for a collection whose data limits were never computed, and `enumerate_elements`
    filters a degenerate bbox out. The result was that EVERY Collection silently left the
    element list, on every frame.

    That is not a cosmetic gap in a list. An artist that is not an Element is never hidden
    by `FrameProbe._draw`, so it is drawn into every isolated render INCLUDING the bare
    background, and it eats the ink of whatever it covers. Measured on a two-token square:
    the page rectangle's isolated ink came out 665 px short, which is exactly the area of
    the two tokens sitting on top of it.

    It matters twice over here. The redesign draws every bed and every token as one
    `PatchCollection` (§R20.8 requires a bed to be exactly one artist), so without this
    fallback the co-occupancy rule would measure an arena in which nothing is standing.
    And the frozen V1 and dormant-V2 frames carry 17 visible `LineCollection`s each, whose
    ink has been contaminating every isolation measurement taken on them.

    The bbox is used as a BOUND on ink (the reach test), so the stroke width is added:
    a stroke is centred on its path and reaches half a width beyond it either side.
    """
    try:
        paths, trans = art.get_paths(), art.get_transform()
    except Exception:
        return None
    exts = []
    for p in paths:
        try:
            e = p.get_extents(trans)
        except Exception:
            continue
        if np.all(np.isfinite([e.x0, e.y0, e.x1, e.y1])):
            exts.append(e)
    if not exts:
        return None
    try:
        lw_pt = float(np.max(np.atleast_1d(np.asarray(art.get_linewidth(), dtype=float))))
    except Exception:
        lw_pt = 0.0
    dpi = float(getattr(getattr(art, "figure", None), "dpi", 72.0) or 72.0)
    pad = max(lw_pt * dpi / 72.0, 0.0)
    return (min(e.x0 for e in exts) - pad, min(e.y0 for e in exts) - pad,
            max(e.x1 for e in exts) + pad, max(e.y1 for e in exts) + pad)


def _draw_index(art) -> int | None:
    """Where this artist sits in its Axes' child list — matplotlib's insertion order."""
    ax = getattr(art, "axes", None)
    if ax is None:
        return None
    for i, child in enumerate(ax.get_children()):
        if child is art:
            return i
    return None


def _is_painted_over(t: "Element", o: "Element") -> bool:
    """True when `o` is composed AFTER `t`, so o's ink lands ON TOP of the label.

    Matplotlib composes an Axes' children by zorder, and by insertion order within one
    zorder, so this is the order the image the viewer sees was actually built in. It is
    the discriminator for the fill class; the module docstring records the two pure-pixel
    alternatives that were implemented, measured and rejected (both false-positive on
    anti-aliased glyph fringes), and the pixel check that corroborates this one.

    Across two Axes the question is not decidable this way — and a text colliding with a
    foreign Axes' content is a bigger defect that the border/card rules already state — so
    that case is deliberately NOT called a defect here.
    """
    if o.artist.axes is None or o.artist.axes is not t.artist.axes:
        return False
    z_o, z_t = float(o.artist.get_zorder()), float(t.artist.get_zorder())
    if z_o != z_t:
        return z_o > z_t
    i_o, i_t = _draw_index(o.artist), _draw_index(t.artist)
    if i_o is None or i_t is None:
        return False
    return i_o > i_t


def _is_rule_like(el: "Element") -> bool:
    """A hairline: a stroke thin enough that it IS an edge (accent rules, spines)."""
    w = el.bbox[2] - el.bbox[0]
    h = el.bbox[3] - el.bbox[1]
    return min(w, h) <= 3.0


def _rect_mask(height: int, width: int, x0, y0, x1, y1) -> np.ndarray:
    """Boolean mask of a display-coordinate rectangle, in image rows/cols."""
    m = np.zeros((height, width), dtype=bool)
    r0 = max(int(np.floor(height - y1)), 0)
    r1 = max(int(np.ceil(height - y0)), 0)
    c0 = max(int(np.floor(x0)), 0)
    c1 = max(int(np.ceil(x1)), 0)
    if r1 > r0 and c1 > c0:
        m[r0:r1, c0:c1] = True
    return m


def _frac_of_axes(art, bbox) -> float:
    """How much of its own axes this element's bbox covers, by area."""
    ax = getattr(art, "axes", None)
    if ax is None:
        return 0.0
    try:
        ab = ax.get_window_extent()
    except Exception:
        return 0.0
    a_area = max(ab.width * ab.height, 1e-9)
    e_area = max((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]), 0.0)
    return float(e_area / a_area)


def _spans_axes(art, bbox) -> bool:
    ax = getattr(art, "axes", None)
    if ax is None:
        return False
    try:
        ab = ax.get_window_extent()
    except Exception:
        return False
    return ((bbox[2] - bbox[0]) >= BG_FRACTION * ab.width
            and (bbox[3] - bbox[1]) >= BG_FRACTION * ab.height)


def enumerate_elements(fig: Figure, renderer) -> list[Element]:
    """Every artist that draws, classified by TYPE and GEOMETRY only (§D5.2 item 1)."""
    skip = set()
    for obj in fig.findobj():
        if isinstance(obj, (Figure, SubFigure, Axes)):
            patch = getattr(obj, "patch", None)
            if patch is not None:
                skip.add(id(patch))          # backgrounds are the canvas, not elements
    for ab in fig.findobj(AnnotationBbox):
        for child in ab.findobj():
            if child is not ab:
                skip.add(id(child))          # the icon is the AnnotationBbox, once

    out: list[Element] = []
    for art in fig.findobj():
        if id(art) in skip or isinstance(art, (Figure, SubFigure, Axes, Axis, Tick)):
            continue
        if not isinstance(art, (Text, Line2D, AxesImage, BboxImage, Patch, Collection,
                                AnnotationBbox)):
            continue
        if not art.get_visible():
            continue
        if isinstance(art, Text) and not art.get_text().strip():
            continue
        try:
            bb = art.get_window_extent(renderer=renderer)
            bbox = (float(bb.x0), float(bb.y0), float(bb.x1), float(bb.y1))
        except Exception:
            bbox = None

        def _degenerate(b):
            return (b is None or not np.all(np.isfinite(b))
                    or b[2] <= b[0] or b[3] <= b[1])

        # A Collection reports an EMPTY window extent, so every one of them used to drop
        # out of this list — and an artist that is not an Element is never hidden by
        # `FrameProbe._draw`, which corrupts every ink measurement it overlaps. See
        # `_collection_extent`.
        if _degenerate(bbox) and isinstance(art, Collection):
            bbox = _collection_extent(art)
        if _degenerate(bbox):
            continue

        if isinstance(art, Text):
            kind, layer = "text", "foreground"
        elif isinstance(art, (AxesImage, BboxImage, AnnotationBbox)):
            kind = "image"
            layer = "background" if _frac_of_axes(art, bbox) >= BG_FRACTION else "foreground"
        elif isinstance(art, Patch):
            if _is_unfilled(art):
                kind, layer = "border", "foreground"      # whatever its size
            else:
                kind = "patch"
                layer = ("background" if _frac_of_axes(art, bbox) >= BG_FRACTION
                         else "foreground")
        else:   # Line2D / Collection
            kind = "line" if isinstance(art, Line2D) else "collection"
            layer = "background" if _spans_axes(art, bbox) else "foreground"
        out.append(Element(art, kind, art.get_text() if isinstance(art, Text) else None,
                           bbox, layer, _axes_name(art)))
    return out


# ---------------------------------------------------------------------------- ink


class FrameProbe:
    """Holds one rendered figure and measures each element's ink by isolation."""

    def __init__(self, fig: Figure, frame: np.ndarray):
        self.fig = fig
        # A constrained/tight layout engine would RE-SOLVE the layout on every redraw, so
        # hiding one artist could move every other one and the diff would be meaningless.
        try:
            fig.set_layout_engine("none")
        except Exception:
            pass
        fig.canvas.draw()
        self.renderer = fig.canvas.get_renderer()
        self.elements = enumerate_elements(fig, self.renderer)
        self._orig = [e.artist.get_visible() for e in self.elements]

        check = self._draw(None)
        if check.shape != frame.shape or not np.array_equal(check, frame):
            raise AuditError(
                "the captured figure does not redraw to the frame the renderer returned "
                f"(shape {check.shape} vs {frame.shape}); every ink measurement would be "
                "taken against a different picture from the one under audit")
        self.baseline = check
        self.h, self.w = check.shape[:2]
        self.empty = self._draw(set())
        self._ink: dict[int, np.ndarray] = {}

    def _draw(self, show) -> np.ndarray:
        for el, orig in zip(self.elements, self._orig):
            el.artist.set_visible(orig if show is None else (id(el.artist) in show))
        self.fig.canvas.draw()
        img = np.asarray(self.fig.canvas.buffer_rgba())[..., :3].copy()
        for el, orig in zip(self.elements, self._orig):
            el.artist.set_visible(orig)
        return img

    def ink(self, el: Element) -> np.ndarray:
        """Boolean mask of the pixels this element puts on a bare background."""
        key = id(el.artist)
        if key not in self._ink:
            img = self._draw({key})
            diff = np.abs(img.astype(np.int16) - self.empty.astype(np.int16)).max(axis=2)
            self._ink[key] = diff > INK_DELTA
        return self._ink[key]

    def close(self):
        plt.close(self.fig)


def _dilate(mask: np.ndarray, n: int = DILATE) -> np.ndarray:
    out = mask.copy()
    for _ in range(max(0, n)):
        g = out
        out = g.copy()
        out[1:, :] |= g[:-1, :]
        out[:-1, :] |= g[1:, :]
        out[:, 1:] |= g[:, :-1]
        out[:, :-1] |= g[:, 1:]
    return out


def _mask_bbox(mask: np.ndarray):
    rows = np.flatnonzero(mask.any(axis=1))
    cols = np.flatnonzero(mask.any(axis=0))
    if not len(rows) or not len(cols):
        return None
    # Reported in image coordinates (x right, y DOWN from the top-left), which is how a
    # reader crops a PNG — not matplotlib's bottom-left display coordinates.
    return int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])


# ------------------------------------------------------------------------- findings


@dataclasses.dataclass
class Finding:
    rule: str
    detail: str
    a: str
    b: str
    overlap_px: int
    bbox: tuple | None

    def as_dict(self):
        return dataclasses.asdict(self)


# ------------------------------------------------ co-occupancy (§R19.1 / §R20.1–§R20.8)
#
# Everything below measures ONE question: does a square show every occupant it holds? The
# module docstring argues each constant and each precondition; this is the implementation.

#: Per-component surviving fraction. A correct composition measures exactly 1.000, so any
#: floor below 1 is pure tolerance for a single anti-aliased seam. SWEPT on both sides at
#: CP0.3b (§R20.3) — the minimum over every negative control against the maximum over the
#: M-F2 family — and the value moves only in the plan text, with its evidence, NEVER in a
#: test to turn a red checkpoint green.
SURVIVAL_MIN = 0.98

#: Ink area share of a square at which an element IS the floor (the bed or the ground)
#: rather than an occupant. Measured area, never a painter's say-so — which is why §R20.8
#: requires a bed to be exactly ONE artist, so this test measures it whole.
CELL_FLOOR_FRACTION = 0.40

#: An outline-classified element must span at least this much of the square in BOTH
#: dimensions to be excluded quietly; below it, it is a suspect token and FAILS (§R20.7).
OUTLINE_SPAN_MIN = 0.80

#: Padding for the work-only reach test. The padded bbox bounds an element's ink, so an
#: element that cannot meet a square cannot put ink in it and `L(p)` is unchanged.
REACH_PAD_PX = 2

#: Per-channel distance (0–255) for the minimap's composite colour census. Deliberately
#: strict: a blend between two occupant colours, the white ring or the terrain tint must
#: classify as NEITHER, so it is excluded from numerator and denominator alike.
MINIMAP_DELTA = 12

#: Share of colour-bearing map squares that may come up completely blank before the rule
#: stops believing its own grid. A real draw-order defect hits the FEW squares that are
#: shared; a grid derived from the wrong rectangle misses MOST squares at once, so the two
#: are told apart by how wholesale the failure is rather than by a tag.
MINIMAP_ALIGN_MAX_BLANK = 0.5

#: Fallback floor for the minimap, used ONLY when a wedge cannot be isolated as its own
#: artist and the denominator falls back to geometry (§R20.4). It is never `SURVIVAL_MIN`
#: reused: it measures a different thing and is swept on the minimap's own controls.
MINIMAP_AREA_MIN = 0.55

#: The audit's OWN copy of the entity -> map colour table. It is a copy, and not an import,
#: because the audit may not import the package it audits (§D5.2, pinned by
#: `test_audit_imports_neither_layout_nor_registry`). A test compares the two tables so the
#: copy cannot drift — the test may import the package, the instrument may not.
MINIMAP_PALETTE = {
    "rock": "#6B7380", "bush": "#4F8A34", "tree": "#2F7A45", "campfire": "#7C4A2D",
    "food": "#E03151", "hiding_predator": "#2B3442", "predator": "#1F2733",
    "neutral": "#A8A29A", "agent": "#5B4BDB",
}

#: Terrain is the FLOOR, not an occupant, so it never counts toward a square's kinds.
TERRAIN_KINDS = frozenset({"rock", "bush", "tree", "campfire"})

#: The caption the World map must carry on any frame holding a shared square (§R17.4).
SHARED_CAPTION = "shared square"


class DrawOrder:
    """Figure-wide composition order, built ONCE per frame.

    `_is_painted_over` deliberately refuses to order two artists in different Axes, which
    is right for the text rules and useless here: with precondition (b′) scoped to `L(p)`,
    the rule must be able to find the last-drawn element at a pixel ACROSS the whole
    figure or it cannot evaluate its own precondition.

    The order is matplotlib's own, not a new invention: a Figure composes its Axes sorted
    by zorder (stable, so insertion order breaks ties), and an Axes composes its children
    the same way. Hence the triple `(axes rank, artist zorder, child index)`.

    An artist in no Axes ranks LAST-RESORT — if it is ever `L(p)` the rule fails (b′),
    which is the fail-closed direction. §R20.1 requires this derivation to be PINNED by a
    rendered two-Axes control rather than trusted: a derived order the pixels contradict
    is a broken instrument.
    """

    def __init__(self, fig: Figure):
        axes = list(fig.axes)
        order = sorted(range(len(axes)), key=lambda i: float(axes[i].get_zorder()))
        ax_rank = {id(axes[i]): k for k, i in enumerate(order)}
        self._n_axes = len(axes)
        self._rank: dict[int, tuple] = {}
        for ax in axes:
            for i, child in enumerate(ax.get_children()):
                self._rank[id(child)] = (ax_rank[id(ax)], float(child.get_zorder()), i)

    def of(self, art) -> tuple:
        r = self._rank.get(id(art))
        if r is not None:
            return r
        return (self._n_axes, float(art.get_zorder()), 0)

    def in_an_axes(self, art) -> bool:
        return id(art) in self._rank


def _paints(art) -> list:
    """Every colour this artist declares it will PAINT with, as RGBA rows.

    A face at alpha 0 or `'none'` paints nothing and is not a paint; an edge is a paint
    only where the line width is above zero. Read in the failing direction only — by
    (a′), which fails on a translucent paint, and by (c′), which fails on a paint the
    probe cannot see. Nothing here can exempt ink from the count.
    """
    from matplotlib.colors import to_rgba

    out = []
    if isinstance(art, Text):
        return [np.asarray(to_rgba(art.get_color()), dtype=float)]
    if isinstance(art, Line2D):
        if float(art.get_linewidth()) > 0:
            return [np.asarray(to_rgba(art.get_color()), dtype=float)]
        return []

    def add(colours, widths=None):
        try:
            arr = np.atleast_2d(np.asarray(colours, dtype=float))
        except Exception:
            return
        if arr.ndim != 2 or arr.shape[-1] != 4:
            return
        for i, row in enumerate(arr):
            if row[3] <= 0.0:
                continue
            if widths is not None:
                if not len(widths) or float(widths[i % len(widths)]) <= 0:
                    continue
            out.append(row)

    try:
        add(art.get_facecolor())
    except Exception:
        pass
    try:
        lw = np.atleast_1d(np.asarray(art.get_linewidth(), dtype=float))
        add(art.get_edgecolor(), lw)
    except Exception:
        pass
    return out


def _is_fully_opaque(art) -> bool:
    """(a′): artist alpha None or 1.0, and no RGBA face or edge alpha below 1."""
    a = art.get_alpha()
    if a is not None and float(a) < 1.0:
        return False
    return all(float(row[3]) >= 1.0 for row in _paints(art))


def _probe_blind_distance(art, fig_fc) -> float | None:
    """(c′): the worst per-channel distance, when EVERY paint is within INK_DELTA.

    Returns None when the element has at least one paint the probe can see. An element
    all of whose paints match the figure facecolor lays down no isolated ink, so it can
    never be `L(p)` and can never be counted as an occluder — the one genuinely silent
    case, which this converts into a failure.
    """
    paints = _paints(art)
    if not paints:
        return None
    worst = max(float(np.max(np.abs(row[:3] - fig_fc[:3])) * 255.0) for row in paints)
    return worst if worst <= INK_DELTA else None


def _components(mask: np.ndarray):
    """Connected components at 8-connectivity: a diagonal touch IS a touch.

    Tolerance is zero shared pixels with no dilation (§R19.1 item 8), so the component
    count IS the touch test — two tokens that touch anywhere are one component and the
    count falls short.
    """
    from scipy import ndimage

    lab, n = ndimage.label(mask, structure=np.ones((3, 3), dtype=int))
    return lab, int(n)


def _bbox_meets(b, rect, pad: float) -> bool:
    return not (b[2] + pad < rect[0] or rect[2] + pad < b[0]
                or b[3] + pad < rect[1] or rect[3] + pad < b[1])


def _named_axes(fig: Figure, name: str):
    for ax in fig.axes:
        if (ax.get_label() or "") == name:
            return ax
    raise AuditError(
        f"no Axes labelled {name!r} in this figure (labels: "
        f"{sorted((a.get_label() or '') for a in fig.axes)}). The arena can only be "
        f"NAMED, never guessed, so the rule refuses to run rather than invent a grid.")


def square_rects(ax, world_h: int, world_w: int) -> dict:
    """Display-coordinate rect per world square, from the AXES EXTENT and the world size.

    Derived from the named arena axes and the recording's world size — never from the
    layout module, which this file may not import. Row 0 is the TOP row, so display y
    (which grows upward) is flipped.
    """
    bb = ax.get_window_extent()
    sw = (bb.x1 - bb.x0) / float(world_w)
    sh = (bb.y1 - bb.y0) / float(world_h)
    out = {}
    for r in range(world_h):
        for c in range(world_w):
            out[(r, c)] = (bb.x0 + c * sw, bb.y1 - (r + 1) * sh,
                           bb.x0 + (c + 1) * sw, bb.y1 - r * sh)
    return out


def occupancy_from_state(state, params) -> dict:
    """Which entity KINDS are in which square — the rule's ground truth.

    Kinds, never instances (§R17.5 item 1): two predators in one square are one predator
    token by design, so an instance count would report a failure that is not one.
    Inactive entity slots are parked off the grid each step, so an out-of-bounds position
    is skipped rather than counted (environment rule R5).
    """
    from src.environment.state import select_by_class

    h, w = int(params.height), int(params.width)
    out: dict[tuple[int, int], set] = {}

    def put(r, c, name):
        if 0 <= r < h and 0 <= c < w:
            out.setdefault((r, c), set()).add(name)

    names = list(params.obstacle_names)
    obs_type = np.asarray(params.obs_type)
    for i, pos in enumerate(np.asarray(getattr(state, "obs_pos"))):
        put(int(pos[0]), int(pos[1]), names[int(obs_type[i])])

    res_type = np.asarray(params.res_type)
    res_active = np.asarray(getattr(state, "res_active"))
    for i, pos in enumerate(np.asarray(getattr(state, "res_pos"))):
        if bool(res_active[i]):
            put(int(pos[0]), int(pos[1]),
                "food" if int(res_type[i]) == 0 else "hiding_predator")

    pred = np.asarray(select_by_class(params, "predator"))
    animal = np.asarray(getattr(state, "animal_pos"))
    for i in range(animal.shape[0]):
        put(int(animal[i, 0]), int(animal[i, 1]),
            "predator" if bool(pred[i]) else "neutral")

    a = np.asarray(getattr(state, "agent_pos"))
    put(int(a[0]), int(a[1]), "agent")
    return {k: tuple(sorted(v)) for k, v in out.items()}


def cell_overdraw(probe: "FrameProbe", arena_axes: str, occupancy: dict,
                  world_h: int, world_w: int, *, restrict_work: bool = True,
                  floor_fraction: float = CELL_FLOOR_FRACTION,
                  survival_min: float = SURVIVAL_MIN):
    """Does every square show every occupant it holds? Returns (findings, measurements).

    `occupancy` maps `(row, col)` to the KINDS at that square (terrain included; it is
    filtered out here, because terrain is the floor). `restrict_work=False` disables the
    padded-bbox reach optimisation and probes every element for every square — the two
    must produce identical findings, which a control asserts.
    """
    ax = _named_axes(probe.fig, arena_axes)
    order = DrawOrder(probe.fig)
    rects = square_rects(ax, world_h, world_w)
    fig_fc = np.asarray(probe.fig.get_facecolor(), dtype=float)
    els = probe.elements
    findings: list[Finding] = []
    measured: list[dict] = []

    for (r, c), rect in rects.items():
        kinds = tuple(k for k in occupancy.get((r, c), ()) if k not in TERRAIN_KINDS)
        n_kinds = len(set(kinds))
        square = _rect_mask(probe.h, probe.w, *rect)
        area = float(square.sum())
        if area <= 0:
            continue
        where = f"square ({r},{c})"

        # The occluder set is every element in the figure. The ONLY exclusion is from the
        # WORK: an element whose padded bbox cannot meet this square cannot put ink in it.
        cands = [e for e in els
                 if (not restrict_work) or _bbox_meets(e.bbox, rect, REACH_PAD_PX)]
        if not cands:
            continue

        # (c') probe visibility, over the arena's own elements — the colours this rule
        # depends on being able to see (ground, bed bases, outline, keyline).
        for e in cands:
            if e.axes_name != arena_axes:
                continue
            d = _probe_blind_distance(e.artist, fig_fc)
            if d is not None:
                findings.append(Finding(
                    "cell_probe_blind",
                    f"every declared paint of this element is within {d:.1f}/255 of the "
                    f"figure facecolor (threshold {INK_DELTA}), so it lays down NO "
                    f"isolated ink and can never be seen to occlude anything",
                    e.label, where, 0, _mask_bbox(square)))

        # BOTH masks are kept: the square-restricted one is what the square's own counts
        # are made of, and the FULL one is what the containment test below needs — an
        # element's ink pre-clipped to the square trivially has nothing outside it.
        ink_full = {id(e.artist): probe.ink(e) for e in cands}
        ink = {k: (v & square) for k, v in ink_full.items()}

        # Classify the arena's elements: floor, outline, or token — by MEASUREMENT.
        tokens, floors = [], []
        for e in cands:
            if e.axes_name != arena_axes:
                continue
            m = ink[id(e.artist)]
            n = int(m.sum())
            if n == 0:
                continue
            # An occupant belongs to exactly ONE square: slots are computed inside the
            # square and the keyline is inset so a token never reaches the square's edge.
            # An element with ink on BOTH sides of the boundary is therefore an overlay
            # passing through — a sense's footprint diamond spans three squares — and it
            # is not an occupant of this one. It stays in the OCCLUDER set, so raising it
            # above the tokens still fires the survival floor: only the assertion narrows.
            # Without this the footprint edge of §R20.2's own negative control is counted
            # as token ink and splits a correct two-mover square into six components.
            if int((ink_full[id(e.artist)] & ~square).sum()) > MIN_OVERLAP_PX:
                continue
            if n / area >= floor_fraction:
                floors.append((e, n / area))
                continue
            if _ink_is_outline(m, e.bbox, probe.h):
                span_x = (e.bbox[2] - e.bbox[0]) / (rect[2] - rect[0])
                span_y = (e.bbox[3] - e.bbox[1]) / (rect[3] - rect[1])
                if min(span_x, span_y) < OUTLINE_SPAN_MIN:
                    findings.append(Finding(
                        "outline_like_token",
                        f"ink sits on the perimeter of its own bbox, but the bbox spans "
                        f"only {min(span_x, span_y):.0%} of the square (floor "
                        f"{OUTLINE_SPAN_MIN:.0%}) — a ring-shaped TOKEN part drawn as its "
                        f"own artist, which must not disappear from the count",
                        e.label, where, n, _mask_bbox(m)))
                continue
            tokens.append(e)

        token_ids = {id(e.artist) for e in tokens}
        token_ink = np.zeros_like(square)
        for e in tokens:
            token_ink |= ink[id(e.artist)]
        n_token_px = int(token_ink.sum())

        # Two token elements may not share a pixel — §R19.1 item 3's "pairwise touching in
        # 0 px", asserted on the ELEMENTS and not only on the merged components. It has to
        # be said of the elements as well, because the component count cannot see this at
        # |K| = 1: an occluder that is itself counted as a token MERGES with the token it
        # covers, and one component over one kind then passes a frame in which an occupant
        # has been painted out. That is exactly how the M-F2 family escapes at the 0.10
        # inset, where the shrunken bed falls under the floor test and is read as a token.
        for i, e in enumerate(tokens):
            for o in tokens[i + 1:]:
                both = int((ink[id(e.artist)] & ink[id(o.artist)]).sum())
                if both:
                    findings.append(Finding(
                        "cell_overdraw",
                        f"two occupant drawings of this square share {both}px; occupants "
                        f"are laid out in disjoint slots, so overlapping ink means one is "
                        f"drawn over the other (tolerance is ZERO shared pixels)",
                        f"{e.label} x {o.label}", where, both,
                        _mask_bbox(ink[id(e.artist)] & ink[id(o.artist)])))

        if n_kinds == 0 and n_token_px == 0:
            continue
        if n_kinds == 0:
            findings.append(Finding(
                "cell_overdraw",
                "the snapshot places no non-terrain kind here, but the square carries "
                f"{n_token_px}px of token ink — something is drawn that nothing holds",
                where, ", ".join(e.label for e in tokens[:3]), n_token_px,
                _mask_bbox(token_ink)))
            continue

        # L(p): the last-drawn element with ink at each pixel, over the FULL occluder set.
        # Painting each candidate's id in ascending rank order leaves the LAST writer.
        last = np.full(square.shape, -1, dtype=np.int32)
        for idx, e in sorted(enumerate(cands), key=lambda t: order.of(t[1].artist)):
            m = ink[id(e.artist)]
            if m.any():
                last[m] = idx

        # (a') and (b'), scoped to L(p) — asserted only where reading them can FAIL.
        for idx in np.unique(last[token_ink]):
            if idx < 0:
                continue
            e = cands[int(idx)]
            if id(e.artist) in token_ids:
                continue                      # a token of this square: (a′) exempts it
            hit = token_ink & (last == idx)
            if not _is_fully_opaque(e.artist):
                findings.append(Finding(
                    "cell_opacity",
                    "the last-drawn element at these token pixels is TRANSLUCENT, so "
                    "'drawn after' is not a valid proxy for what the viewer sees: this "
                    "is an occlusion a viewer can partly see through",
                    e.label, where, int(hit.sum()), _mask_bbox(hit)))
            if e.axes_name != arena_axes or not order.in_an_axes(e.artist):
                findings.append(Finding(
                    "cell_foreign_axes",
                    f"the last-drawn element at these token pixels belongs to "
                    f"{e.axes_name!r}, not to the named arena axes {arena_axes!r}; token "
                    f"ink under a foreign Axes cannot be ordered and must not pass",
                    e.label, where, int(hit.sum()), _mask_bbox(hit)))

        # A pixel of a token survives exactly when the LAST element to write it is a token
        # of this square — which is the same statement as "no element drawn after it has
        # ink there", and is why a token's own parts never eat into its own denominator.
        visible = np.zeros_like(square)
        for idx in np.unique(last[token_ink]):
            if idx >= 0 and id(cands[int(idx)].artist) in token_ids:
                visible |= token_ink & (last == idx)

        _lab_i, n_iso = _components(token_ink)
        _lab_v, n_vis = _components(visible)
        lab_i = _lab_i

        ratios = []
        for k in range(1, n_iso + 1):
            comp = lab_i == k
            tot = int(comp.sum())
            ratios.append(float(int((comp & visible).sum()) / tot) if tot else 0.0)

        measured.append({
            "square": [r, c], "kinds": sorted(set(kinds)), "n_kinds": n_kinds,
            "components_isolated": n_iso, "components_visible": n_vis,
            "survival": ratios, "min_survival": min(ratios) if ratios else None,
            "token_px": n_token_px,
            "floor_fraction": [round(f, 4) for _e, f in floors],
        })

        if n_iso != n_kinds:
            findings.append(Finding(
                "cell_overdraw",
                f"the square holds {n_kinds} kind(s) {sorted(set(kinds))} but its token "
                f"ink forms {n_iso} connected component(s) — occupants drawn on one "
                f"centre merge into one, which is the defect this rule exists for",
                where, f"{n_iso} component(s)", n_token_px, _mask_bbox(token_ink)))
        if n_vis != n_kinds:
            findings.append(Finding(
                "cell_overdraw",
                f"the square holds {n_kinds} kind(s) {sorted(set(kinds))} but only "
                f"{n_vis} survive(s) the painting — an occupant is drawn and then covered "
                f"by something painted after it, so the viewer never sees it",
                where, f"{n_vis} visible component(s)", int(visible.sum()),
                _mask_bbox(visible)))
        for k, ratio in enumerate(ratios, start=1):
            if ratio < survival_min:
                comp = lab_i == k
                findings.append(Finding(
                    "cell_overdraw",
                    f"an occupant keeps only {ratio:.1%} of its own ink (floor "
                    f"{survival_min:.0%}); a correct composition measures 100.0%. A "
                    f"component count alone cannot see this — a token 95% hidden is "
                    f"still one component",
                    where, f"component {k} of {n_iso}",
                    int((comp & ~visible).sum()), _mask_bbox(comp & ~visible)))

    return findings, measured


def _classify_census(img: np.ndarray, mask: np.ndarray, colours: dict) -> dict:
    """Count pixels inside `mask` that match each named colour within MINIMAP_DELTA.

    A blend — between two occupant colours, the white ring, the 0.8 px split line or the
    terrain tint — matches NEITHER, and is therefore excluded from the numerator and from
    the denominator alike. That is what makes a correct split dot measure ~1.000 against a
    census-measured denominator, where it could never reach 0.98 of a GEOMETRIC wedge.
    """
    from matplotlib.colors import to_rgb

    out = {}
    px = img[mask].astype(np.int16)
    for name, hexc in colours.items():
        want = np.asarray([round(v * 255) for v in to_rgb(hexc)], dtype=np.int16)
        out[name] = int((np.abs(px - want).max(axis=1) <= MINIMAP_DELTA).sum())
    return out


def minimap_overdraw(probe: "FrameProbe", minimap_axes: str, occupancy: dict,
                     world_h: int, world_w: int):
    """The World map, measured on the COMPOSITE — plus the shared-square caption.

    Isolation would report a split dot as correct even when one half is painted over the
    other, which is the exact defect §R17.4 exists to prevent, so this rule classifies the
    pixels of the FINISHED image against the palette table. Ground truth is the distinct
    palette colours the KINDS present map to (§R20.4): two predators are one colour and
    one kind, and the withdrawn "at least as many colours as movers" wording failed that
    correct square.
    """
    ax = _named_axes(probe.fig, minimap_axes)
    rects = square_rects(ax, world_h, world_w)
    findings: list[Finding] = []
    pending: list[Finding] = []
    img = probe.baseline
    shared_anywhere = False
    n_expected = n_blank = 0

    # One solo render per element, reused across every square. The denominator is the
    # same census run on the isolated artist (§R20.4), and rendering per (square, colour)
    # instead would be thousands of renders on a 100-square map.
    solo_cache: dict[int, np.ndarray] = {}

    def solo(el):
        key = id(el.artist)
        if key not in solo_cache:
            solo_cache[key] = probe._draw({key})
        return solo_cache[key]

    for (r, c), rect in rects.items():
        kinds = [k for k in occupancy.get((r, c), ()) if k not in TERRAIN_KINDS]
        if len(set(kinds)) >= 2:
            shared_anywhere = True
        want = {}
        for k in set(kinds):
            if k in MINIMAP_PALETTE:
                want[k] = MINIMAP_PALETTE[k]
        if not want:
            continue
        square = _rect_mask(probe.h, probe.w, *rect)
        census = _classify_census(img, square, want)
        seen = {k for k, n in census.items() if n > 0}
        n_expected += 1
        n_blank += 0 if seen else 1
        distinct_want = {MINIMAP_PALETTE[k] for k in want}
        distinct_seen = {MINIMAP_PALETTE[k] for k in seen}
        where = f"map square ({r},{c})"
        if len(distinct_seen) != len(distinct_want):
            pending.append(Finding(
                "minimap_overdraw",
                f"the snapshot's kinds {sorted(want)} map to {len(distinct_want)} "
                f"distinct palette colour(s), but the composed map shows "
                f"{len(distinct_seen)} — a dot painted over its neighbour shows one "
                f"colour where the square holds two kinds",
                where, f"seen {sorted(seen)}", int(sum(census.values())),
                _mask_bbox(square)))
            continue
        # Denominator by the SAME census on the isolated artist, never geometry (§R20.4).
        for k, n in census.items():
            den, path = 0, "isolated-wedge"
            for e in probe.elements:
                if e.axes_name != minimap_axes:
                    continue
                if not _bbox_meets(e.bbox, rect, REACH_PAD_PX):
                    continue
                den = max(den, _classify_census(solo(e), square, {k: want[k]})[k])
            floor = SURVIVAL_MIN
            if den == 0:
                den, path, floor = int(square.sum()) or 1, "geometric", MINIMAP_AREA_MIN
            ratio = n / float(den)
            if ratio < floor:
                pending.append(Finding(
                    "minimap_overdraw",
                    f"{k}'s colour covers {ratio:.1%} of what it covers when drawn alone "
                    f"(floor {floor:.0%}, denominator measured by the {path} path)",
                    where, k, n, _mask_bbox(square)))

    # ALIGNMENT, asserted before any per-square verdict is believed. `square_rects`
    # divides the NAMED AXES into world squares, which is exact for the arena — whose
    # axes IS the grid — and wrong for a World map drawn as an inset grid inside a whole
    # card, where the map is offset by its title and its caption. A misaligned grid looks
    # exactly like "every dot has been painted over": the census samples the card's
    # background and finds no occupant colour anywhere. Reporting that as N separate
    # overdraw defects would be a confident wrong answer, so the rule says THE GRID IS
    # WRONG once, and reports nothing else.
    if n_expected and (n_blank / n_expected) > MINIMAP_ALIGN_MAX_BLANK:
        findings.append(Finding(
            "minimap_grid_unaligned",
            f"{n_blank} of {n_expected} map square(s) that should carry an occupant "
            f"colour contain NONE of it. The square grid is derived by dividing the "
            f"named axes {minimap_axes!r} into {world_h}x{world_w}, so a figure this "
            f"wholesale means that axes is not the map grid itself — a card with a title "
            f"and a caption around an INSET grid will do exactly this. A real draw-order "
            f"defect hits the few squares that are shared; a misaligned grid misses most "
            f"squares at once, which is what separates the two. No per-square verdict is "
            f"trustworthy here, so none is reported",
            minimap_axes, f"{world_h}x{world_w} grid", 0, None))
    else:
        findings.extend(pending)

    if shared_anywhere:
        caption = [e for e in probe.elements
                   if e.kind == "text" and SHARED_CAPTION in (e.text or "").lower()]
        if not caption:
            findings.append(Finding(
                "minimap_caption",
                "the snapshot holds a shared square, so the World map encodes two "
                "occupants as one split dot — and the card must SAY so in words, because "
                "at this square size colour is a code the viewer cannot infer (§R17.4)",
                "World map", f"no text containing {SHARED_CAPTION!r}", 0, None))
    return findings


def _normalise_title(s: str) -> str:
    t = " ".join(s.split()).upper()
    for suf in _TITLE_SUFFIXES:
        if t.endswith(suf):
            t = t[: -len(suf)].strip()
    return t.rstrip(":").strip()


def _title_name(norm: str) -> str | None:
    """Longest-prefix lookup in TITLE_TABLE.

    A panel's rendered caption is not always exactly its name: V1 labels the body
    temperature gauge `BODY TEMP   DIE -15 / +15`, one string carrying the title and its
    scale. An exact-match table reports that panel ABSENT while it is plainly drawn —
    a false "silently dropped panel", which is the one verdict this rule exists to give.
    """
    if norm in TITLE_TABLE:
        return TITLE_TABLE[norm]
    best = None
    for key, name in TITLE_TABLE.items():
        if norm.startswith(key) and (best is None or len(key) > len(best[0])):
            best = (key, name)
    return best[1] if best else None


def _panel_titles(elements: list[Element]) -> list[tuple[Element, str, bool]]:
    """(title element, breakdown name, offline) for every text that names a panel."""
    found = []
    for el in elements:
        if el.kind != "text":
            continue
        norm = _normalise_title(el.text or "")
        name = _title_name(norm)
        if name is not None:
            offline = "OFFLINE" in (el.text or "").upper()
            found.append((el, name, offline))
    return found


def _owning_title(caption: Element, titles) -> tuple[Element, str] | None:
    """The panel a caption belongs to: the nearest title at or above it, same axes.

    Attribution is by COLUMN (the axes the text was drawn into) and vertical order, not by
    horizontal proximity. A vitals row prints its label hard left and its value hard right
    of the same 180 px panel, so an x-overlap test rejects the row's own label and then
    silently blames the caption on some other panel — which turns the observed-caption
    rule into noise.
    """
    cx0, cy0, cx1, cy1 = caption.bbox
    best = None
    for el, name, _off in titles:
        if el.artist.axes is not caption.artist.axes:
            continue
        ty0 = el.bbox[1]
        if ty0 + 0.5 < cy0:                        # title must sit at or above the caption
            continue
        d = ty0 - cy0
        if best is None or d < best[0]:
            best = (d, el, name)
    return (best[1], best[2]) if best else None


def _card_elements(els: list[Element], probe) -> list[Element]:
    """Panel cards: outline-inked elements big enough to BE a panel (>= 40 x 25 px).

    The size floor says what counts as a card rather than what counts as a collision; a
    hairline rule or a 6 px glyph outline is not a panel.
    """
    cards = []
    for e in els:
        if e.layer != "foreground" or e.kind not in ("patch", "border"):
            continue
        if (e.bbox[2] - e.bbox[0]) < 40 or (e.bbox[3] - e.bbox[1]) < 25:
            continue
        if _ink_is_outline(probe.ink(e), e.bbox, probe.h):
            cards.append(e)
    return cards


def _title_strips(els: list[Element], titles, probe):
    """(description, mask) for each card's TITLE STRIP — the band between it and its title.

    That band belongs to the title alone. Any other text with ink in it has escaped the
    card whose content it labels, which is the "content outside its allotted box" defect:
    the label reads as part of the title line instead of as part of its own panel. The
    band is fully determined by the card's top edge and its title's ink — no free
    parameter, no tolerance beyond MIN_OVERLAP_PX.
    """
    strips = []
    for card in _card_elements(els, probe):
        cx0, _cy0, cx1, cy1 = card.bbox
        best = None
        for el, _name, _off in titles:
            tx0, ty0, tx1, _ty1 = el.bbox
            if tx1 < cx0 or tx0 > cx1:          # the title must sit over this card
                continue
            if ty0 < cy1:                       # ... and above its top edge
                continue
            d = ty0 - cy1
            if best is None or d < best[0]:
                best = (d, el)
        if best is None or best[0] <= 1.0:      # title inside the card: no strip exists
            continue
        el = best[1]
        # A title strip is ONE TEXT LINE tall. Without this, a card whose own title is not
        # in TITLE_TABLE (V1's "RUN CONTEXT") adopts the nearest table-matching text far
        # above it, and the "strip" becomes a 65 px band swallowing four unrelated labels
        # — four false positives, measured. The bound is the title's own ink height, so it
        # scales with the font rather than being a pixel count picked by hand.
        if best[0] > 2.0 * (el.bbox[3] - el.bbox[1]):
            continue
        strips.append((f"{card.label} titled {el.text!r}",
                       _rect_mask(probe.h, probe.w, cx0, cy1, cx1, el.bbox[1])))
    return strips


def audit_frame(fi: FrameInputs, renderer: str, text_floor_px: float = DEFAULT_TEXT_FLOOR_PX,
                arena_axes: str | None = None, verbose: bool = False,
                cell_axes: str | None = None, minimap_axes: str | None = None):
    """Render one frame and return (findings, probe, info)."""
    frame, fig = render_capture(renderer, fi)
    probe = FrameProbe(fig, frame)
    els = probe.elements
    texts = [e for e in els if e.kind == "text"]
    fg = [e for e in els if e.layer == "foreground"]
    findings: list[Finding] = []

    # --- collisions ------------------------------------------------------------------
    # bbox pre-filter: ink is contained in the artist's window extent (padded for stroke
    # effects), so bboxes that cannot touch cannot have inks that touch.
    pad = 2 + DILATE

    def _overlaps(a, b):
        return not (a[2] + pad < b[0] or b[2] + pad < a[0]
                    or a[3] + pad < b[1] or b[3] + pad < a[1])

    seen_pairs = set()
    for i, t in enumerate(texts):
        partners = [o for o in fg if o is not t and _overlaps(t.bbox, o.bbox)]
        if not partners:
            continue
        t_ink = _dilate(probe.ink(t))
        if not t_ink.any():
            continue
        for o in partners:
            o_ink = probe.ink(o)
            inter = t_ink & o_ink
            n = int(inter.sum())
            if n < MIN_OVERLAP_PX:
                continue
            # One collision is one finding. Two texts that fight over the same pixels are
            # otherwise reported once from each side, doubling every text-on-text count.
            pair = frozenset((id(t.artist), id(o.artist)))
            if o.kind == "text":
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
            if o.kind == "text":
                rule, detail = "text_over_text", "two text elements share pixels"
            elif (o.kind == "border" or _is_rule_like(o)
                  or _ink_is_outline(o_ink, o.bbox, probe.h)):
                rule, detail = "text_over_border", "text lies across a panel edge"
            else:
                # A label drawn inside its own widget, or a widget painted over a label?
                # Decided by composition order plus shared RAW ink — see the docstring for
                # the two pixel tests that were measured and rejected.
                covered = int((probe.ink(t) & o_ink).sum())
                if covered >= 1 and _is_painted_over(t, o):
                    rule = "fill_over_text"
                    detail = (f"drawn content composed AFTER this label covers {covered} px "
                              f"of its {int(probe.ink(t).sum())} px of ink")
                else:
                    rule = "text_over_fill"
                    detail = ("text shares pixels with drawn content but is composed "
                              "after it, so the label is what the frame shows")
            findings.append(Finding(rule, detail, t.label, o.label, n, _mask_bbox(inter)))

    # --- clipping and canvas ---------------------------------------------------------
    edge = np.zeros((probe.h, probe.w), dtype=bool)
    edge[0, :] = edge[-1, :] = True
    edge[:, 0] = edge[:, -1] = True
    margin = np.zeros((probe.h, probe.w), dtype=bool)
    m = CANVAS_MARGIN_PX
    margin[:m, :] = margin[-m:, :] = True
    margin[:, :m] = margin[:, -m:] = True

    for t in texts:
        ink = probe.ink(t)
        if not ink.any():
            continue
        if (ink & edge).sum() >= MIN_OVERLAP_PX:
            findings.append(Finding("clipped", "text ink reaches the canvas edge",
                                    t.label, "canvas edge", int((ink & edge).sum()),
                                    _mask_bbox(ink & edge)))
        size_px = float(t.artist.get_fontsize()) * probe.fig.dpi / 72.0
        if text_floor_px > 0 and size_px < text_floor_px - 1e-6:
            findings.append(Finding("legibility",
                                    f"rendered {size_px:.1f}px < floor {text_floor_px:.1f}px",
                                    t.label, "", 0, _mask_bbox(ink)))

    for e in fg:
        ink = probe.ink(e)
        n = int((ink & margin).sum())
        if n >= MIN_OVERLAP_PX:
            findings.append(Finding("out_of_canvas",
                                    f"foreground ink inside the outer {m}px margin",
                                    e.label, "canvas margin", n, _mask_bbox(ink & margin)))

    # --- content outside its card: the title strip belongs to the title alone ---------
    titles = _panel_titles(els)
    title_ids = {id(el.artist) for el, _n, _o in titles}
    for card_desc, gap in _title_strips(els, titles, probe):
        for t in texts:
            if id(t.artist) in title_ids:
                continue
            hit = probe.ink(t) & gap
            n = int(hit.sum())
            if n >= MIN_OVERLAP_PX:
                findings.append(Finding(
                    "out_of_card",
                    "text drawn in the strip between a card and its title — outside the "
                    "card whose content it labels",
                    t.label, card_desc, n, _mask_bbox(hit)))

    # --- presence, ground truth = the observation breakdown --------------------------
    drawn = {}
    for el, name, offline in titles:
        has_ink = probe.ink(el).any()
        if has_ink and not offline:
            drawn.setdefault(name, el)
    for name in fi.breakdown:
        if name not in drawn:
            findings.append(Finding("panel_absent",
                                    "a modality in the observation breakdown has no panel "
                                    "title with ink in the rendered frame",
                                    name, "", 0, None))

    # --- observed-caption rule -------------------------------------------------------
    for t in texts:
        s = (t.text or "").strip()
        up = s.upper()
        if not (up.startswith("OBS") or up.startswith("REAL") or "OBS ONLY" in up):
            continue
        own = _owning_title(t, titles)
        if own is None:
            findings.append(Finding("observed_caption",
                                    "an OBS/REAL caption belongs to no identifiable panel",
                                    t.label, "", 0, _mask_bbox(probe.ink(t))))
            continue
        _el, name = own
        if name not in fi.breakdown:
            findings.append(Finding("observed_caption",
                                    f"captioned as observed under {name!r}, which is NOT "
                                    f"in the observation breakdown",
                                    t.label, f"panel {name!r}", 0,
                                    _mask_bbox(probe.ink(t))))

    # --- no numeric text inside the arena --------------------------------------------
    if arena_axes:
        arena = [e for e in els if e.axes_name == arena_axes]
        if arena:
            ax = arena[0].artist.axes
            ab = ax.get_window_extent()
            for t in texts:
                if t.artist.axes is not ax:
                    continue
                if not any(ch.isdigit() or ch in "+-" for ch in (t.text or "")):
                    continue
                x0, y0, x1, y1 = t.bbox
                if x0 >= ab.x0 and x1 <= ab.x1 and y0 >= ab.y0 and y1 <= ab.y1:
                    findings.append(Finding("numeric_in_arena",
                                            "numeric text drawn inside the arena grid",
                                            t.label, "arena", 0, _mask_bbox(probe.ink(t))))

    # --- co-occupancy: does a square show every occupant it holds? -------------------
    #
    # Enabled by its OWN flag rather than by `--arena-axes`, deliberately. The two rules
    # want different axes: `numeric_in_arena` is legitimately pointed at any axes that
    # should carry no numbers (a test points it at `thermoception`), while this rule
    # divides the axes it is given into world squares — pointed at a pod it would invent
    # a grid over a card and report nonsense. Keeping them separate is also what leaves
    # every frozen V1 and dormant-V2 count UNCHANGED (#62), which CP0.3b asserts.
    cells_measured: list[dict] = []
    occ = None
    if cell_axes or minimap_axes:
        occ = occupancy_from_state(fi.state, fi.params)
    if cell_axes:
        cell_findings, cells_measured = cell_overdraw(
            probe, cell_axes, occ, int(fi.params.height), int(fi.params.width))
        findings.extend(cell_findings)
    if minimap_axes:
        findings.extend(minimap_overdraw(
            probe, minimap_axes, occ, int(fi.params.height), int(fi.params.width)))

    info = {
        "renderer": renderer, "cell_dir": str(fi.rec_dir), "step": fi.step,
        "n_steps": fi.n_steps, "frame": [int(probe.w), int(probe.h)],
        "elements": len(els), "foreground": len(fg), "texts": len(texts),
        "breakdown": fi.breakdown, "panels_drawn": sorted(drawn),
        "cells": cells_measured,
    }
    return findings, probe, info


# ------------------------------------------------------------------ positive controls
#
# Known, REAL defects that this audit must flag, with both participants pinned so a
# control cannot pass because something else was reported in the same frame. Their
# COORDINATES are pinned too, in tests/env/test_render_audit_controls.py: the right rule
# on the right pair at the wrong PLACE in the frame is also a miss.
#
# Plan §A2 classes D2 as "text-on-text". MEASURED, it is not: `REAL: --` and the
# EXTERO NOCICEPTION title are 1.55 px apart and share NO pixel — at any squeeze factor
# and in any world, because the two anchors are algebraically equal (Revision 15). What is
# real is that the readout is drawn OUTSIDE its own card, in the strip belonging to that
# card's title, which is `out_of_card`. `text_over_text` stays as an accepted alternative
# because it is the class the defect WOULD take if that 1.55 px ever closed.
# `text_over_border` was REMOVED from D2's rules as unreachable rather than lenient: a
# border finding reports its partner as `patch Rectangle in axes@NNNN` — the axes' name,
# never the card's title — so `b_contains: "EXTERO NOCICEPTION"` could never match one.

CONTROLS = {
    "D1": {
        "renderer": "v1", "cell": "M4", "step": 0,
        "what": "extero-nociception 'OBS:' readout overprints the THERMOCEPTION pod title",
        "rules": ("text_over_text",),
        "a_contains": "OBS:", "b_contains": "THERMOCEPTION",
    },
    "D2": {
        "renderer": "v1", "cell": "M4", "step": 0,
        "what": "'REAL: --' escapes its card into the EXTERO NOCICEPTION title strip",
        "rules": ("out_of_card", "text_over_text"),
        "a_contains": "REAL:", "b_contains": "EXTERO NOCICEPTION",
    },
    "D3": {
        "renderer": "v1", "cell": "M4", "step": 0,
        "what": "'MINIMAP' label lies across the Run Context box border",
        "rules": ("text_over_border",),
        "a_contains": "MINIMAP", "b_contains": None,
    },
    "D6": {
        "renderer": "v2", "cell": "M4", "step": 0,
        "what": "COLLISION card title overprints its C/U/R/D/L cell labels",
        "rules": ("text_over_text",),
        "a_contains": "COLLISION", "b_contains": None,
        "b_in": ("'C'", "'U'", "'R'", "'D'", "'L'"),
    },
    "D8": {
        "renderer": "v2", "cell": "M4", "step": 0,
        "what": "dormant V2 silently drops the interoceptive-nociception panel",
        "rules": ("panel_absent",),
        "a_contains": "Interoceptive Nociception", "b_contains": None,
    },
    # CP0.3 also names these two on the V1 M4 frame. They are not among the five the
    # brief pins, but they are free calibration and are reported with the rest.
    "D10": {
        "renderer": "v1", "cell": "M4", "step": 0,
        "what": "Nutrition/Injury captioned OBS/REAL although the campfire world's "
                "observation contains neither",
        "rules": ("observed_caption",),
        "a_contains": "OBS:", "b_contains": "Nutrition",
    },
    "D12": {
        "renderer": "v1", "cell": "M4", "step": 0,
        "what": "Proprioception is emitted by the viz adapter and never drawn",
        "rules": ("panel_absent",),
        "a_contains": "Proprioception", "b_contains": None,
    },
}

# There is deliberately NO "required subset" constant. `main()` fails on ANY missed
# control, so a constant naming five of the seven would read as though D10 and D12 were
# optional — and CP0.3 names those two as well.


def _control_matches(ctl, f: Finding) -> bool:
    if f.rule not in ctl["rules"]:
        return False
    if ctl["a_contains"] and ctl["a_contains"] not in f.a:
        return False
    if ctl.get("b_contains") and ctl["b_contains"] not in f.b:
        return False
    if ctl.get("b_in") and not any(tok in f.b for tok in ctl["b_in"]):
        return False
    return True


def run_controls(fixture_root: Path, verbose: bool = True) -> dict:
    """Fire every positive control; return {name: {fired, findings...}}."""
    results, cache = {}, {}
    for name, ctl in CONTROLS.items():
        key = (ctl["renderer"], ctl["cell"], ctl["step"])
        if key not in cache:
            fi = load_inputs(fixture_root / ctl["cell"] / ctl["cell"], ctl["step"])
            findings, probe, info = audit_frame(fi, ctl["renderer"],
                                                arena_axes=None)
            cache[key] = (findings, info)
            probe.close()
        findings, info = cache[key]
        hits = [f for f in findings if _control_matches(ctl, f)]
        results[name] = {
            "fired": bool(hits), "what": ctl["what"],
            "frame": f"{ctl['renderer'].upper()} {ctl['cell']} step {ctl['step']}",
            "hits": [h.as_dict() for h in hits],
            "n_findings_in_frame": len(findings),
        }
        if verbose:
            mark = "FIRED " if hits else "MISSED"
            print(f"  [{mark}] {name}: {ctl['what']}")
            for h in hits[:4]:
                where = f" at {h.bbox}" if h.bbox else ""
                px = f", {h.overlap_px}px" if h.overlap_px else ""
                print(f"            {h.rule}: {h.a} x {h.b}{px}{where}")
            if not hits:
                print(f"            frame reported {len(findings)} finding(s), none matching")
    return results


# ---------------------------------------------------------------------------- report


def summarise(findings: list[Finding]) -> dict:
    counts = {}
    for f in findings:
        counts[f.rule] = counts.get(f.rule, 0) + 1
    return counts


def write_report(out_dir: Path, entries: list[dict], controls: dict | None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"entries": entries, "controls": controls,
               "tolerances": {"INK_DELTA": INK_DELTA, "DILATE": DILATE,
                              "MIN_OVERLAP_PX": MIN_OVERLAP_PX,
                              "BG_FRACTION": BG_FRACTION,
                              "CANVAS_MARGIN_PX": CANVAS_MARGIN_PX}}
    p = out_dir / "audit.json"
    p.write_text(json.dumps(payload, indent=2, default=str))
    rows = []
    for e in entries:
        rows.append(f"<tr><td>{e['info']['renderer']}</td><td>{e['info']['cell_dir']}</td>"
                    f"<td>{e['info']['step']}</td><td>{e['counts']}</td></tr>")
    ctl_rows = ""
    if controls:
        ctl_rows = "".join(
            f"<tr><td>{k}</td><td>{'FIRED' if v['fired'] else 'MISSED'}</td>"
            f"<td>{v['what']}</td></tr>" for k, v in controls.items())
    (out_dir / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>render layout audit</title>"
        "<style>body{font:14px system-ui;margin:2rem}td,th{padding:4px 10px;"
        "border-bottom:1px solid #ddd;text-align:left}</style>"
        "<h1>Render layout audit</h1><h2>Frames</h2><table>"
        "<tr><th>renderer</th><th>recordings</th><th>step</th><th>findings</th></tr>"
        + "".join(rows) + "</table>"
        + ("<h2>Positive controls</h2><table><tr><th>control</th><th>state</th>"
           "<th>what</th></tr>" + ctl_rows + "</table>" if ctl_rows else ""))
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cell", default=None, help="fixture cell name, e.g. M4")
    ap.add_argument("--rec-dir", default=None, help="a recordings directory (overrides --cell)")
    ap.add_argument("--fixture-root", default=DEFAULT_FIXTURE_ROOT)
    ap.add_argument("--renderer", default="v1", choices=("v1", "v2"))
    ap.add_argument("--step", type=int, default=0)
    ap.add_argument("--steps", type=int, nargs="+", default=None)
    ap.add_argument("--text-floor-px", type=float, default=DEFAULT_TEXT_FLOOR_PX)
    ap.add_argument("--arena-axes", default=None,
                    help="name of the arena Axes, which ENABLES the numeric_in_arena rule "
                         "(V1's arena Axes is unlabelled, so the rule cannot run on V1; "
                         "the dormant V2 labels its axes, e.g. --arena-axes arena)")
    ap.add_argument("--cell-axes", default=None,
                    help="name of the arena grid Axes, which ENABLES the cell_overdraw "
                         "co-occupancy rule. Separate from --arena-axes on purpose: this "
                         "rule divides the named axes into world squares, so pointing it "
                         "at a pod would invent a grid over a card")
    ap.add_argument("--minimap-axes", default=None,
                    help="name of the World-map Axes, which ENABLES the minimap colour "
                         "census and the shared-square caption check")
    ap.add_argument("--controls", action="store_true",
                    help="run the CP0.3 positive controls and exit non-zero if any misses")
    ap.add_argument("--out", default=None, help="report directory")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.fixture_root)
    if not root.is_absolute():
        root = REPO_ROOT / root
    out_dir = Path(args.out) if args.out else None

    controls = None
    entries = []
    rc = 0

    if args.controls:
        print("== positive controls (CP0.3): known defects the audit MUST flag")
        controls = run_controls(root)
        missed = [k for k, v in controls.items() if not v["fired"]]
        print(f"== {len(controls) - len(missed)}/{len(controls)} controls fired")
        if missed:
            print(f"HARD STOP: control(s) {missed} did not fire. The audit is not "
                  f"sensitive enough to be trusted; do not weaken the defect list or "
                  f"tune the threshold until they pass.")
            rc = 1

    if args.cell or args.rec_dir:
        rec_dir = (Path(args.rec_dir) if args.rec_dir
                   else root / args.cell / args.cell)
        if not rec_dir.is_absolute():
            rec_dir = REPO_ROOT / rec_dir
        for step in (args.steps if args.steps is not None else [args.step]):
            fi = load_inputs(rec_dir, step)
            findings, probe, info = audit_frame(fi, args.renderer,
                                                text_floor_px=args.text_floor_px,
                                                arena_axes=args.arena_axes,
                                                cell_axes=args.cell_axes,
                                                minimap_axes=args.minimap_axes)
            probe.close()
            counts = summarise(findings)
            entries.append({"info": info, "counts": counts,
                            "findings": [f.as_dict() for f in findings]})
            if not args.quiet:
                print(f"\n== {args.renderer.upper()} {rec_dir.name} step {step} "
                      f"({info['frame'][0]}x{info['frame'][1]}, {info['elements']} elements, "
                      f"{info['texts']} texts)")
                print(f"   findings: {counts or '(none)'}")
                for f in findings:
                    where = f" at {f.bbox}" if f.bbox else ""
                    px = f" [{f.overlap_px}px]" if f.overlap_px else ""
                    print(f"   - {f.rule}: {f.a} x {f.b}{px}{where}")

    if out_dir:
        p = write_report(out_dir, entries, controls)
        print(f"\nreport written: {p}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
