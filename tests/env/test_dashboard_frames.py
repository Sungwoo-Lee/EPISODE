"""Checkpoint CP2.8's own evidence, in the committed suite instead of a scratch harness.

WHAT THIS FILE IS FOR, IN PLAIN WORDS. A square of this world can hold more than one
thing at once — an agent standing where a predator is, food lying on a bush — and the old
renderer drew them on the same spot, so one covered the other and the video showed a lie.
The redesign fixes that, and checkpoint CP2.8 is what certifies the fix: every occupant of
a shared square must actually be VISIBLE in a rendered frame, the measuring instrument
must be shown to CATCH the defect when the defect is deliberately put back (a "mutation"),
and somebody must look at the pictures.

Until now that evidence was produced by hand through throwaway scripts under `tmp/`. This
file is its named home (plan §R17.6), so the numbers are reproducible by CI rather than by
remembering which script to run.

THE TWO PICTURES, AND WHY ONLY ONE OF THEM IS HERE. The dashboard draws the world twice:
a big grid panel at 50 px a square, and a small "World map" at 18.40 px a square. The grid
panel's rule (`cell_overdraw`) was measured clean across all nine verification worlds
before this file existed, so what it needs here is one frame-level proof in CI rather than
a re-derivation — that is the last test in the file, and it is the slow one (~50 s: the
instrument isolates every element in the frame, which is N+1 renders).

The World map is the part Revision 22 changed, and most of this file measures it. At 18 px
no shape survives, so the map gives up drawing WHAT things are and encodes them as COLOUR:
one dot per square, divided between its occupants — a whole dot for one, halves for two,
120° wedges for three, 90° for four — with a small amber dot inside the mark of a *hiding*
predator, which is otherwise the same colour as an ordinary one to within 15 parts in 255.

WHAT A MUTATION IS, SINCE FOUR OF THEM ARE BELOW. A test that only checks correct pictures
cannot tell a working instrument from one that says yes to everything. So each control has
a partner that breaks the drawing on purpose and requires the instrument to complain:

  * **M-F3** paints the agent's dot over its neighbour's wedge — the original defect.
  * **M-F4** puts the amber identity pip back at the square's CENTRE, where it straddles
    both halves of a shared dot and eats the NEIGHBOUR's colour. This is the painter as it
    stood before Revision 22, and it is the control that stops the census's new
    "amber belongs to the hiding predator" rule becoming a blanket amnesty.
  * **M-F5** paints amber with something that is not a hiding predator's pip, which is the
    only condition under which that rule is safe.
  * **M-E / M-F1** (grid panel) force every occupant onto the square's centre, or paint
    the terrain floor over the occupants standing on it.

Fixtures live under gitignored `results/`, so every frame-level test SKIPS with an explicit
reason when they are absent rather than passing vacuously.
"""
import contextlib
import os
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts" / "eval"))

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import matplotlib  # noqa: E402
matplotlib.use("Agg")

import render_layout_audit as audit  # noqa: E402
from src.environment.dashboard import cells as C  # noqa: E402
from src.environment.dashboard import painters as PN  # noqa: E402
from src.environment.dashboard import palette as P  # noqa: E402

FIXTURES = _ROOT / audit.DEFAULT_FIXTURE_ROOT
_MISSING = (f"render-audit fixtures not on disk ({FIXTURES}); regenerate with "
            f"scripts/eval/make_render_fixture_recordings.py")


def _have(cell="M4"):
    d = FIXTURES / cell / cell
    return d.is_dir() and any(d.glob("episode_*.rec.gz"))


needs_fixtures = pytest.mark.skipif(not _have(), reason=_MISSING)


# ===========================================================================
# the encoding, as arithmetic — no fixtures, no rendering
# ===========================================================================
@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_the_dot_is_divided_between_its_occupants_and_nothing_is_left_over(n):
    """n wedges of 360/n degrees, starting at 12 o'clock, with no gap and no overlap."""
    spans = [PN._wedge_angles(n, i) for i in range(n)]
    assert spans[0][0] == 90.0
    assert spans[-1][1] == pytest.approx(450.0)
    for (t1, t2), (u1, _u2) in zip(spans, spans[1:]):
        assert t2 - t1 == pytest.approx(360.0 / n)
        assert t2 == pytest.approx(u1), "a gap or an overlap between two wedges"


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_the_identity_pip_sits_inside_its_owners_wedge_and_inside_the_dot(n):
    """The whole point of moving it off the square's centre (§R22.3 item 4).

    At the centre the pip straddles every wedge, so on a shared square it annotates the
    wrong occupant — mutation M-F4 below. Inside its own sector it annotates only its own
    mark. Two conditions, both checked for every wedge of every n: the pip clears both
    radii that bound its sector, and it stays inside the dot — which is also the claim
    that nothing is drawn outside the dot any more, now that the rim pip is retired.
    """
    r_dot = 1.0
    for i in range(n):
        dx, dy, r_p = PN._pip_place(n, i, r_dot)
        d = float(np.hypot(dx, dy))
        assert r_p > 0
        assert d + r_p <= r_dot + 1e-9, "the pip reaches outside the dot"
        if n == 1:
            assert d == 0.0
            continue
        half = np.pi / n
        assert d * np.sin(half) >= r_p, "the pip crosses into a neighbouring wedge"
        mid = np.radians(sum(PN._wedge_angles(n, i)) / 2.0)
        assert dx == pytest.approx(d * np.cos(mid))
        assert dy == pytest.approx(d * np.sin(mid))


def test_the_retired_rim_pip_was_infeasible_and_the_pip_that_replaced_it_is_not():
    """§R22.2's bound, recomputed rather than quoted.

    A pip outside the 0.30 × cell dot AND inside the square must satisfy
    r_p ≤ 0.1016 × cell; the painter drew 0.12, so "outside the dot" was unachievable by
    construction and the pip ate the wedge it sat on. The identity pip is not subject to
    that bound at all, because it is drawn INSIDE the dot — which is why retiring the rim
    pip removed the constraint rather than tightening it.
    """
    r_d, ring_d, ring_p, half_extent = 0.300, 0.0326, 0.0217, 0.4457
    bound = ((2 ** 0.5) * (half_extent - ring_p) - (r_d + ring_d + ring_p)) / (1 + 2 ** 0.5)
    assert bound == pytest.approx(0.1016, abs=5e-4)
    assert 0.12 > bound, "the retired rim pip's radius was inside its own feasible bound?"
    for n in (1, 2, 3, 4):
        dx, dy, r_p = PN._pip_place(n, 0, 0.30)
        assert float(np.hypot(dx, dy)) + r_p <= 0.30 + 1e-9


def test_the_ceiling_is_four_kinds_and_the_agent_is_never_the_one_dropped():
    """§R22.3 item 6 / §R17.5 item 5: five kinds are out of scope for BOTH panels.

    `CELL_PRIORITY` puts the agent first, so the map keeps answering the question it is
    for — where the agent is — however crowded the square gets.
    """
    five = ["neutral", "food", "hiding_predator", "predator", "agent"]
    shown = C.by_priority(five)[:4]
    assert shown[0] == "agent"
    assert len(shown) == 4
    assert "neutral" not in shown, "the LAST by priority is the one dropped"


def test_amber_is_reserved_to_the_hiding_predators_identity_pip():
    """The condition the census's amber exemption rests on (§R22.1, M-F5's subject)."""
    assert P.HIDE_EYE not in set(P.MINIMAP_COLOUR.values())
    assert P.MINIMAP_MARK_COLOURS["hiding_predator"] == frozenset({P.HIDE_BODY, P.HIDE_EYE})
    others = [v for k, v in P.MINIMAP_MARK_COLOURS.items() if k != "hiding_predator"]
    assert all(P.HIDE_EYE not in v for v in others)


# ===========================================================================
# the World map at its real square size, on a real frame
# ===========================================================================
@contextlib.contextmanager
def _frame(squares, cell="M4", episode=1, step=0):
    """Render a real recording with the given occupants placed on the given squares.

    DERIVED INPUT, AND SAID SO. Some of the compositions CP2.8 asks about occur in no
    episode of any verification world — a four-way square occurs in none at all — so they
    are produced by overriding the occupancy of a real snapshot. The renderer and the
    audit are then handed THE SAME dict, so the drawing and the ground truth cannot drift
    apart and quietly agree about a frame neither is describing, and the frame's own
    header says `SYNTHETIC derived input`.
    """
    from src.environment.dashboard import episode as EP
    from src.utils.eval_recording import load_episode, load_run_meta

    rec = FIXTURES / cell / cell
    meta = load_run_meta(rec)
    payload = load_episode(sorted(rec.glob("episode_*.rec.gz"))[episode])
    real = EP.occupancy_of(payload["snapshots"][step], meta["params"])
    occ = dict(real)
    occ.update({sq: tuple(names) for sq, names in squares.items()})
    original = EP.occupancy_of
    EP.occupancy_of = lambda _snap, _params: occ
    try:
        r = EP.EpisodeRenderer(meta["params"], meta["icon_config"], payload,
                               title=f"SYNTHETIC derived input · {cell}")
        try:
            yield r, r.frame(step), occ, meta["params"]
        finally:
            r.close()
    finally:
        EP.occupancy_of = original


def _redraw(r):
    r.canvas.draw()
    return np.asarray(r.canvas.buffer_rgba())[..., :3].copy()


def _map_geometry(r, square):
    gax = r.axes["minimap"]
    cell = gax._px_w / r.meta["width"]
    return gax, cell, (square[1] + 0.5) * cell, (square[0] + 0.5) * cell


def _mutate(r, name, square, amount=None):
    """Break the MAP on purpose, on the artists the real painter drew.

    GRADED, since Revision 23 §R23.2. `amount` makes the same defect progressively
    shallower, which is what turns a single defect POINT into a population the ratio floor
    can be swept against:

      * `M-F3` — the overpainting disc's radius as a fraction of the dot's. 1.0 (the
        default) is the original full-dot mutation, which removes a neighbour's colour
        entirely and is caught by the DISTINCTNESS check, never reaching the floor.
      * `M-F4` — how far the identity pip is dragged from its own wedge towards the
        square's centre. 1.0 (the default) is the centre itself, i.e. the painter as it
        stood before Revision 22; 0.8 is a shallow crossing that eats two pixels.

    The pip's radius is set to the pre-Revision-22 value for every M-F4 member, so the only
    thing that varies across the family is how far it crosses — otherwise the family would
    be sweeping two things at once and its gap table would mean nothing.
    """
    from matplotlib.patches import Circle, Wedge

    gax, cell, cx, cy = _map_geometry(r, square)
    frac = 1.0 if amount is None else float(amount)
    here = [a for a in gax.get_children()
            if isinstance(a, (Circle, Wedge)) and a.get_visible()
            and abs(a.center[0] - cx) < cell / 2 and abs(a.center[1] - cy) < cell / 2]
    if name == "M-F3":
        gax.add_patch(Circle((cx, cy), cell * 0.30 * frac, fc=P.MINIMAP_COLOUR["agent"],
                             ec=P.WHITE, lw=1.2, zorder=9))
    elif name == "M-F4":
        pips = [a for a in here if isinstance(a, Circle) and a.get_radius() < cell * 0.2]
        assert pips, "no identity pip on that square to move back to the centre"
        px, py = pips[0].get_center()
        pips[0].set_center((px + frac * (cx - px), py + frac * (cy - py)))
        pips[0].set_radius(cell * 0.30 * PN.IDENT_FRAC)
    elif name == "M-F5":
        wedges = [a for a in here if isinstance(a, Wedge)]
        assert wedges, "no wedge on that square to paint amber"
        wedges[-1].set_facecolor(P.HIDE_EYE)
    else:                                               # pragma: no cover - typo guard
        raise AssertionError(name)
    return _redraw(r)


def _census(frame, probe, r, occ, square):
    """Every kind's numerator, denominator and ratio on one MAP square."""
    gax = audit._named_axes(probe.fig, "minimap")
    rect = audit.square_rects(gax, int(r.meta["height"]), int(r.meta["width"]))[square]
    mask = audit._rect_mask(probe.h, probe.w, *rect)
    out = {}
    for k in {n for n in occ.get(square, ()) if n in audit.MINIMAP_PALETTE}:
        want = {k: audit.MINIMAP_PALETTE[k]}
        num = audit._classify_census(frame, mask, want)[k]
        own = [id(e.artist) for e in probe.elements
               if e.axes_name == "minimap"
               and audit._bbox_meets(e.bbox, rect, audit.REACH_PAD_PX)
               and audit._classify_census(probe._draw({id(e.artist)}), mask, want)[k]]
        den = audit._classify_census(probe._draw(set(own)), mask, want)[k] if own else 0
        out[k] = (num, den, (num / den) if den else float("nan"))
    return out


def _run_map(squares, mutation=None, at=None, amount=None, **kw):
    """Findings + per-square ratios for the World map of one rendered frame."""
    with _frame(squares, **kw) as (r, frame, occ, params):
        if mutation:
            frame = _mutate(r, mutation, at, amount)
        probe = audit.FrameProbe(r.fig, frame)
        try:
            findings = audit.minimap_overdraw(probe, "minimap", occ,
                                              int(params.height), int(params.width))
            ratios = {sq: _census(frame, probe, r, occ, sq) for sq in squares}
            return findings, ratios
        finally:
            probe.close()


@needs_fixtures
@pytest.mark.integration
@pytest.mark.parametrize("occupants", [
    ["hiding_predator"],
    ["agent", "food"],
    ["hiding_predator", "neutral"],
    ["agent", "predator", "food", "neutral"],
    ["agent", "hiding_predator", "food", "neutral"],
])
def test_the_world_map_is_silent_at_the_real_square_size(occupants):
    """The negative controls of §R22.6, at 18.40 px a square rather than on a mock.

    Scale is the whole point of running these here: a map wedge is 13–24 classified
    pixels, so a single anti-aliased pixel is 4–8 % of it. A control that only ever ran on
    a 28 px mock would not have been able to see that.
    """
    findings, ratios = _run_map({(2, 2): occupants})
    assert findings == [], (findings, ratios)
    for kind, (num, den, ratio) in ratios[(2, 2)].items():
        assert den > 0, f"{kind} could not be isolated; the geometric fallback was taken"
        assert ratio == pytest.approx(1.0, abs=1e-9), (kind, num, den)


@needs_fixtures
@pytest.mark.integration
def test_the_four_way_census_is_a_number_and_the_ratio_is_scale_free():
    """§R22.3's pre-registered branch point, recorded as a COUNT rather than a verdict.

    A quarter wedge is about 24 px² of geometry before the white split lines and the ring
    blends are removed, and the census deliberately classifies a blend as NEITHER colour.
    The branch was written down before the measurement: if the smallest wedge classifies
    at a non-zero count the ratio test is scale-free and measures ≈ 1.000, and the design
    holds at four; if it classifies at ZERO the denominator falls back to geometry, the
    rule fires on a correct picture, and the answer is a stated ceiling of THREE — never a
    lowered floor or a widened colour tolerance.

    MEASURED: 13 classified pixels per wedge, all four, ratio 1.000 — the design holds.
    """
    _findings, ratios = _run_map({(1, 1): ["agent", "predator", "food", "neutral"]})
    counts = {k: num for k, (num, _d, _r) in ratios[(1, 1)].items()}
    assert len(counts) == 4, counts
    assert min(counts.values()) > 0, (
        f"the smallest wedge classified at zero ({counts}); per §R22.3 the response is a "
        f"stated ceiling of three occupants, NOT a lowered floor")
    assert 8 <= min(counts.values()) <= 20, counts
    for _k, (_num, _den, ratio) in ratios[(1, 1)].items():
        assert ratio == pytest.approx(1.0, abs=1e-9), counts


@needs_fixtures
@pytest.mark.integration
def test_m_f4_the_identity_pip_at_the_centre_eats_its_neighbour_and_is_caught():
    """The control that keeps §R22.1's union fix from being an amnesty.

    The census now lets the hiding predator's amber accent count towards the hiding
    predator, because the accent is part of its own mark. The risk in that is obvious: if
    amber were simply ignored, an amber pip painted over a NEIGHBOUR would go unseen. So
    the pip is put back where the painter had it this morning — the square's centre, where
    it straddles both halves of a shared dot — and the rule must name the kind it ate.
    """
    findings, ratios = _run_map({(2, 2): ["hiding_predator", "neutral"]},
                                mutation="M-F4", at=(2, 2))
    assert any(f.rule == "minimap_overdraw" and f.b == "neutral" for f in findings), \
        (findings, ratios)


@needs_fixtures
@pytest.mark.integration
def test_m_f3_a_dot_painted_over_the_split_wedge_is_caught():
    findings, _ratios = _run_map({(2, 2): ["predator", "neutral"]},
                                 mutation="M-F3", at=(2, 2))
    assert any(f.rule == "minimap_overdraw" for f in findings), findings


@needs_fixtures
@pytest.mark.integration
def test_m_f5_amber_painted_by_anything_but_the_identity_pip_is_caught():
    """Amber may only ever be a hiding predator's identity pip (§R22.6).

    Caught twice over, which is worth stating: recolouring a neighbour's wedge amber makes
    that kind's own colour vanish, so the composite shows one colour where the square
    holds two kinds — and the artist-level guard below names the offending artist directly
    rather than inferring it from the colour that went missing.
    """
    findings, _ratios = _run_map({(2, 2): ["predator", "neutral"]},
                                 mutation="M-F5", at=(2, 2))
    assert any(f.rule == "minimap_overdraw" for f in findings), findings

    with _frame({(2, 2): ["predator", "neutral"]}) as (r, frame, occ, params):
        frame = _mutate(r, "M-F5", (2, 2))
        probe = audit.FrameProbe(r.fig, frame)
        try:
            amber = {"hide_eye": frozenset({P.HIDE_EYE})}
            offenders = []
            for e in probe.elements:
                if e.axes_name != "minimap":
                    continue
                ink = probe.ink(e)
                if ink.any() and audit._classify_census(
                        probe._draw({id(e.artist)}), ink, amber)["hide_eye"]:
                    offenders.append(e.label)
            assert offenders, "an amber artist on a square with no hiding predator"
        finally:
            probe.close()


@needs_fixtures
@pytest.mark.integration
def test_a_correct_three_way_loses_exactly_one_pixel_to_the_shared_split_line():
    """A pinned PROPERTY of the drawing, and the tightest correct case the floor must pass.

    On a correct three-way dot the first-drawn wedge measures 16 classified pixels against
    17 when its own artist is drawn alone. The cause was measured, not guessed: the white
    0.8 px line that divides two wedges is stroked by BOTH of them, and compositing the
    same partially-covered pixel twice leaves it whiter than either pass alone (~9 % white
    against ~5 %), which carries that one pixel from 7/255 to 13/255 away from its
    colour — just past `MINIMAP_DELTA`'s 12.

    THE SEAM IS NOT A DEFECT AND IS NOT REPAIRED (§R23.3). Three repairs were measured and
    rejected: round joins changed nothing; folding a square's wedges into one artist would
    force 1.000 by construction while hiding the draw-order defect M-F3 exists to catch;
    and drawing the wedges EDGELESS removes the one-pixel loss but yields ratios ABOVE
    1.000 (23/22, 26/25), because with no white line the two wedge colours meet directly
    and their blend is credited to one of them — error in the direction that CONCEALS
    occlusion. The white split line is what makes a blend classify as neither colour.

    WHAT CHANGED IS THE NUMBER, AND ONLY FOR THIS PANEL (§R23.1). This case used to fire,
    because the map's census path had inherited the grid panel's `SURVIVAL_MIN = 0.98` —
    swept on ~330 px² arena tokens where one seam pixel is 0.3 %, applied to a 17 px wedge
    where it is 6 %, and unreachable there at all below 50 classified pixels. The map now
    has its own floor and 16/17 clears it with room to spare, which is asserted here so
    that the margin is a measured number rather than a claim in a comment.
    """
    _findings, ratios = _run_map({(4, 4): ["agent", "predator", "neutral"]})
    num, den, ratio = ratios[(4, 4)]["agent"]
    assert (num, den) == (16, 17), ratios
    assert ratio == pytest.approx(16 / 17, abs=1e-6)
    assert ratios[(4, 4)]["predator"][2] == pytest.approx(1.0)
    assert ratios[(4, 4)]["neutral"][2] == pytest.approx(1.0)
    assert ratio - audit.MINIMAP_SURVIVAL_MIN == pytest.approx(0.0112, abs=5e-4), (
        f"16/17 = {ratio:.4f} against a floor of {audit.MINIMAP_SURVIVAL_MIN}; the margin "
        f"§R23.1 recorded was 0.0112")


@needs_fixtures
@pytest.mark.integration
def test_a_correct_three_way_is_silent():
    """The former strict xfail, retired by Revision 23 — this is the day it turned.

    It was registered to fail while the map measured against the arena's floor, precisely
    so that settling the constant would make the suite go red rather than let a stale plan
    note drift. `MINIMAP_SURVIVAL_MIN` settles it, so the picture that was always correct
    is now also silent. It must NEVER be made silent by any other means: shrinking a wedge,
    widening `MINIMAP_DELTA` or folding the wedges into one artist all turn this green
    while destroying what the rule measures (§R23.1 *Fails if:*).
    """
    findings, ratios = _run_map({(4, 4): ["agent", "predator", "neutral"]})
    assert findings == [], (findings, ratios)


# ===========================================================================
# the map's own survival floor: the re-registered family and the gap table
# ===========================================================================
#: §R23.2's re-registered family: FOUR members, each of which must fire through the RATIO
#: FLOOR rather than through the distinctness check.
#:
#: WHY IT WAS RE-REGISTERED. The three mutations §R22.6 pre-registered do not all test this
#: floor. Measured: M-F3 at full dot radius removes a neighbour's colour ENTIRELY and M-F5
#: recolours a whole wedge, so both are caught by distinctness — the composite shows fewer
#: palette colours than the square holds kinds — and the ratio is never consulted. Only
#: M-F4 reached the floor, so the defect side of the gap was one POINT rather than a
#: population, and "best mutation 0.833" said nothing about how shallow a defect this rule
#: can still see. The arena hit the same problem at §R20.3 and answered it with a graded
#: three-member family; the map never inherited that discipline until Revision 23.
#:
#: Each row is (name, occupants, mutation, amount, measured ratio at 18.40 px).
MAP_FLOOR_FAMILY = (
    ("M-F4a", ["hiding_predator", "neutral"], "M-F4", 1.00, 0.8333),   # pip at the centre
    ("M-F4b", ["hiding_predator", "neutral"], "M-F4", 0.80, 0.9167),   # shallow crossing
    ("M-F3a", ["predator", "neutral"], "M-F3", 0.35, 0.5833),
    ("M-F3b", ["predator", "neutral"], "M-F3", 0.25, 0.7500),          # shallowest seen
)

#: The negative partners, measured and kept rather than quietly dropped. At 60 % and 40 %
#: of the way to the centre the pip costs the neighbour NO classified pixel, so the rule is
#: silent and correctly so. That is this instrument's resolution limit, measured rather
#: than assumed — one classified pixel — and it is why the family stops at 0.80.
MAP_FLOOR_SILENT_PARTNERS = (
    ("M-F4 @0.60", ["hiding_predator", "neutral"], "M-F4", 0.60),
    ("M-F4 @0.40", ["hiding_predator", "neutral"], "M-F4", 0.40),
)

#: The correct side of the gap table, at the real square size. Every one of these is a
#: picture drawn exactly as specified, and the floor must sit BELOW all of them.
MAP_CORRECT_CONTROLS = (
    ("n=1 agent", ["agent"]),
    ("n=1 hiding predator (two-paint mark)", ["hiding_predator"]),
    ("two predators — two movers, ONE kind", ["predator", "predator"]),
    ("n=2 hiding predator + neutral", ["hiding_predator", "neutral"]),
    ("n=2 predator + neutral", ["predator", "neutral"]),
    ("n=3 agent + predator + neutral", ["agent", "predator", "neutral"]),
    ("n=3 agent + predator + hiding predator", ["agent", "predator", "hiding_predator"]),
    ("n=4 agent + predator + food + neutral", ["agent", "predator", "food", "neutral"]),
    ("n=4 with a hiding predator", ["agent", "hiding_predator", "food", "neutral"]),
)


def _floor_fired(findings):
    """The kinds reported by the RATIO FLOOR specifically, not by distinctness.

    The two halves of `minimap_overdraw` produce differently worded findings on purpose:
    the floor says a kind's colour "covers X % of what it covers when drawn alone", while
    distinctness says the square's kinds map to N palette colours and the composite shows
    fewer. A family member caught by the second has no ratio at all and must never be
    counted towards the floor's gap — that is precisely the mistake §R23.2 corrects.
    """
    return {f.b for f in findings
            if f.rule == "minimap_overdraw" and "covers" in f.detail}


@needs_fixtures
@pytest.mark.integration
def test_the_minimap_floor_sits_in_a_gap_and_not_on_a_cliff():
    """§R23.1's gap table, asserted — the map's mirror of the arena's at §R20.3.

    One side is the minimum over correct controls, the other the maximum over the members
    of §R23.2's family that fire THROUGH THE RATIO FLOOR. Both are measured here at the
    real 18.40 px square size, because that is the whole point: the floor this replaces was
    swept on ~330 px² arena tokens and reused on a 6–32 px map wedge, where 0.98 is not
    merely strict but arithmetically unreachable below 50 classified pixels.

    MEASURED, at square (2, 2) unless stated:

      correct   n=1 agent 60/60 · n=1 hiding predator 48/48 · two predators 48/48 ·
                n=2 hp+neutral 16/16 and 24/24 · n=2 predator+neutral 24/24 ·
                n=3 predator 15/16 = 0.9375 · n=4 8/8 ×4 · n=4 with a hiding predator 6/6
      defect    M-F4a 20/24 = 0.8333 · M-F4b 22/24 = 0.9167 ·
                M-F3a 14/24 = 0.5833 · M-F3b 18/24 = 0.7500

    so the gap is (0.9167, 0.9375] and 0.93 sits 64 % up it. NOTE THE CORRECT SIDE: §R23.1
    recorded 0.9412 (16/17, square (4, 4)) as the worst correct case, and sweeping a second
    square finds 0.9375 (15/16) — the SAME one-pixel seam on a wedge one pixel smaller, and
    exactly the resolution limit §R23.1 states in advance (a 15–24 px wedge may lose one
    pixel and stay silent; 14 or fewer may lose none). The floor is not moved for it.

    IF THIS GAP EVER COLLAPSES the answer is to report it in the plan with both populations
    and, if they overlap, to state a detection limit — never to nudge the constant until
    today's frames pass. A ratio floor on a 13 px wedge is near its resolution limit by
    construction, and saying so is the honest response (§R17.5's pattern).
    """
    correct = {}
    for name, occupants in MAP_CORRECT_CONTROLS:
        findings, ratios = _run_map({(2, 2): occupants})
        assert findings == [], (name, findings, ratios)
        correct[name] = min(r for _n, _d, r in ratios[(2, 2)].values())

    defect, fired = {}, 0
    for name, occupants, mutation, amount, expect in MAP_FLOOR_FAMILY:
        findings, ratios = _run_map({(2, 2): occupants}, mutation=mutation,
                                    at=(2, 2), amount=amount)
        kinds = _floor_fired(findings)
        assert kinds, (
            f"{name} did not fire through the RATIO FLOOR: "
            f"{[(f.rule, f.detail) for f in findings]}. A member caught only by the "
            f"distinctness check has no ratio and must not be counted towards this gap — "
            f"report it and re-register the member, never count it anyway (§R23.2)")
        fired += 1
        worst = max(ratios[(2, 2)][k][2] for k in kinds)
        defect[name] = worst
        assert worst == pytest.approx(expect, abs=1e-3), (
            f"{name} measured {worst:.4f} against the {expect} recorded in §R23.2")

    assert fired == len(MAP_FLOOR_FAMILY), (defect, fired)

    for name, occupants, mutation, amount in MAP_FLOOR_SILENT_PARTNERS:
        findings, ratios = _run_map({(2, 2): occupants}, mutation=mutation,
                                    at=(2, 2), amount=amount)
        assert findings == [], (
            f"{name} was pre-registered as SILENT — the pip costs the neighbour no "
            f"classified pixel there — and it fired: {findings}, {ratios}")

    lo, hi = min(correct.values()), max(defect.values())
    assert hi < audit.MINIMAP_SURVIVAL_MIN <= lo, (
        f"MINIMAP_SURVIVAL_MIN={audit.MINIMAP_SURVIVAL_MIN} does not sit in the measured "
        f"gap ({hi:.4f}, {lo:.4f}]. correct={correct} defect={defect}")
    assert lo - hi > 0.015, (
        f"the gap collapsed to {lo - hi:.4f} ({hi:.4f}, {lo:.4f}]; the floor would then be "
        f"a cliff, and the honest response is to REPORT that with both populations, never "
        f"to move the constant to open it")


def test_the_map_never_measures_against_the_grid_panels_floor():
    """§R20.4's ruling, made structural instead of remembered (§R23.1).

    The plan said in Revision 20 that the map "gets its own ground truth and its own floor
    … never `SURVIVAL_MIN` reused". That was honoured on the geometric path, which got
    `MINIMAP_AREA_MIN` — and then the census path added in Revision 22 took the arena's
    0.98 anyway, by nothing more sinister than assigning it beside a branch. The reuse was
    the defect, so the fix REMOVES it rather than relocating it: the rule looks its floor up
    from the path it took, which means a path added later and left unregistered raises here
    rather than silently inheriting a number swept for a panel eighteen times the size.

    No fixtures, no rendering — this is arithmetic and a source read.
    """
    import inspect
    import re

    src = inspect.getsource(audit.minimap_overdraw)
    assert "SURVIVAL_MIN" not in re.sub(r"MINIMAP_SURVIVAL_MIN", "", src), (
        "the minimap rule mentions the grid panel's floor again; the map has its own")

    assert set(audit.MINIMAP_FLOORS) == {"isolated-wedge", "own-artists", "geometric"}
    assert audit.SURVIVAL_MIN not in set(audit.MINIMAP_FLOORS.values())
    assert audit.MINIMAP_FLOORS["geometric"] == audit.MINIMAP_AREA_MIN
    assert audit.MINIMAP_FLOORS["isolated-wedge"] == audit.MINIMAP_SURVIVAL_MIN
    assert audit.MINIMAP_FLOORS["own-artists"] == audit.MINIMAP_SURVIVAL_MIN
    with pytest.raises(KeyError):
        audit.MINIMAP_FLOORS["a-path-somebody-adds-next-year"]

    # the two instruments stay apart, and the arena's number is untouched
    assert audit.SURVIVAL_MIN == 0.98
    assert audit.MINIMAP_SURVIVAL_MIN == 0.93
    assert audit.MINIMAP_AREA_MIN == 0.55
    assert audit.MINIMAP_DELTA == 12


@needs_fixtures
@pytest.mark.integration
def test_the_shared_square_caption_is_present_and_describes_what_is_drawn():
    """§R17.4's honesty condition: the coded encoding must be STATED on the page.

    The audit only checks the caption exists on a frame that holds a shared square. What
    it cannot check is whether the words are still true — so that half is asserted here,
    against the painter's own constant, and specifically against the mark that no longer
    exists.
    """
    findings, _ratios = _run_map({(2, 2): ["agent", "neutral"]})
    assert not [f for f in findings if f.rule == "minimap_caption"], findings
    whole = " ".join(PN.MINIMAP_CAPTION).lower()
    assert audit.SHARED_CAPTION in whole
    assert "up to four" in whole and "colour is the code" in whole
    assert "rim pip" not in whole and "corner pip" not in whole


# ===========================================================================
# the grid panel, on a real frame — the slow one
# ===========================================================================
@needs_fixtures
@pytest.mark.integration
def test_a_real_frame_shows_every_occupant_of_every_shared_square():
    """CP2.8's central claim, on a real recorded frame, through the whole audit.

    `M4` episode 1 step 32 is used because it carries both structures the rule needs: a
    square holding two non-terrain kinds (agent + food), so concentric drawing would have
    something to merge, and a square holding a token on a terrain floor (neutral + rock),
    so a floor drawn late would have something to cover.

    This runs the FULL audit — every rule, not just the co-occupancy ones — because the
    rule's preconditions are about the whole figure. It costs ~50 s: the instrument
    measures each element's ink by drawing it alone, which is N+1 renders over ~700
    elements. That is why CP2.8 samples at most two frames per world rather than every
    frame of every episode.
    """
    rec = FIXTURES / "M4" / "M4"
    fi = audit.load_inputs(rec, 32, episode=1)
    with _frame({}, cell="M4", episode=1, step=32) as (r, frame, _occ, params):
        saved = audit.render_capture
        audit.render_capture = lambda _renderer, _fi: (frame, r.fig)
        try:
            findings, probe, info = audit.audit_frame(
                fi, "dashboard", arena_axes="arena", cell_axes="arena")
        finally:
            audit.render_capture = saved
        try:
            cell_rules = [f for f in findings if f.rule.startswith("cell_")
                          or f.rule == "outline_like_token"]
            assert cell_rules == [], cell_rules
            measured = {tuple(m["square"]): m for m in info["cells"]}
            shared = {sq: m for sq, m in measured.items() if m["n_kinds"] > 1}
            assert shared, "the chosen frame holds no shared square; the test is vacuous"
            for sq, m in measured.items():
                assert m["components_isolated"] == m["n_kinds"], (sq, m)
                assert m["components_visible"] == m["n_kinds"], (sq, m)
                assert all(s == pytest.approx(1.0, abs=1e-9) for s in m["survival"]), \
                    (sq, m)
        finally:
            probe.close()
