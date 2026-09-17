"""Checkpoint CP2.8's own evidence, on real rendered frames.

WHAT THIS FILE IS FOR, IN PLAIN WORDS. A square of this world can hold more than one
thing at once — an agent standing where a rock is, food lying on a bush — and the old
renderer drew them on the same spot, so one covered the other and the video showed a lie.
Checkpoint CP2.8 is what certifies the fix: every occupant of a shared square must
actually be VISIBLE in a rendered frame, and the measuring instrument must be shown to
CATCH the defect when the defect is deliberately put back.

WHAT CHANGED ON 2026-09-17, AND WHY MOST OF THIS FILE IS SHORTER (plan Revision 27).

The dashboard used to draw the world twice: a big grid panel showing the WHOLE world at
50 px a square, and a small World map at 18.4 px. At 18 px no shape survives, so the map
gave up drawing what things are and encoded them as colour — one dot per square, split
into wedges when the square was shared. Most of this file measured that encoding.

The approved design draws a **window** in the grid panel — `local_view_size` squares
centred on the agent, at 96 px each — and one plain mark per entity on the map. So the
grid view answers "what is in this square?" at a size where the artwork is legible, and
the map answers "where in the world am I, and where is the window looking?". The wedge
encoding, its four tolerances and every test of them are retired with the picture they
measured; what is left is the invariant itself, asserted on the panel that now claims it.

TWO THINGS THIS FILE CHECKS THAT IT COULD NOT BEFORE:

  * the grid panel DECLARES which world squares it is showing, and the audit measures
    against that declaration rather than assuming the panel holds the whole world. A
    declaration that does not contain the agent is refused — that is the one thing a
    wrong window cannot fake, and it is tested in the failing direction.
  * terrain is an occupant now, not the floor, so "every occupant is visible" covers a
    rock sharing a square with an agent. That case is exactly the one the whole redesign
    started from, and until today it was exempted from the rule by construction.

Fixtures live under gitignored `results/`, so every frame-level test SKIPS with an
explicit reason when they are absent rather than passing vacuously.
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
from src.environment.dashboard import layout as L  # noqa: E402
from src.environment.dashboard import palette as P  # noqa: E402

FIXTURES = _ROOT / audit.DEFAULT_FIXTURE_ROOT
_MISSING = (f"render-audit fixtures not on disk ({FIXTURES}); regenerate with "
            f"scripts/eval/make_render_fixture_recordings.py")


def _have(cell="M4"):
    d = FIXTURES / cell / cell
    return d.is_dir() and any(d.glob("episode_*.rec.gz"))


needs_fixtures = pytest.mark.skipif(not _have(), reason=_MISSING)


@contextlib.contextmanager
def _frame(offsets=None, cell="M4", episode=1, step=0):
    """Render a real recording, optionally forcing occupants into the window.

    DERIVED INPUT, AND SAID SO. Some of the compositions CP2.8 asks about occur in no
    episode of any verification world — a four-way square occurs in none at all — so they
    are produced by overriding the occupancy of a real snapshot. The renderer and the
    audit are then handed THE SAME dict, so the drawing and the ground truth cannot drift
    apart and quietly agree about a frame neither is describing.

    `offsets` maps a (row, col) OFFSET FROM THE WINDOW'S TOP-LEFT CORNER to the occupants
    to put there. Offsets rather than absolute squares, because the grid view draws a
    window now: an absolute square chosen in advance may not be on screen, and a test that
    measures a square the panel is not drawing measures nothing.

    ONE HONEST LIMITATION, stated because it would otherwise look like a bug: the World
    map draws entities from the SNAPSHOT, not from this override, so on a derived frame
    the map shows the real world while the grid shows the derived one. Nothing here
    measures the map, and the divergence is deliberate rather than overlooked.
    """
    from src.environment.dashboard import episode as EP
    from src.utils.eval_recording import load_episode, load_run_meta

    rec = FIXTURES / cell / cell
    meta = load_run_meta(rec)
    payload = load_episode(sorted(rec.glob("episode_*.rec.gz"))[episode])
    real = EP.occupancy_of(payload["snapshots"][step], meta["params"])

    holder = {}

    def _patched(snap, params):
        occ = dict(real)
        if offsets and "origin" in holder:
            r0, c0 = holder["origin"]
            for (dr, dc), names in offsets.items():
                occ[(r0 + dr, c0 + dc)] = tuple(names)
        holder["occ"] = occ
        return occ

    original = EP.occupancy_of
    EP.occupancy_of = _patched
    try:
        r = EP.EpisodeRenderer(meta["params"], meta["icon_config"], payload,
                               title=f"SYNTHETIC derived input · {cell}")
        try:
            # the window origin is a property of the step, so it is known before the
            # frame is drawn and the overridden squares can be placed inside it
            holder["origin"] = r.view_origin(r.values(step))
            yield r, r.frame(step), holder["occ"], meta["params"]
        finally:
            r.close()
    finally:
        EP.occupancy_of = original


def _arena_axes(r):
    return r.axes["arena"]


# ===========================================================================
# the window: what the grid panel draws, and what it says it draws
# ===========================================================================
@needs_fixtures
@pytest.mark.integration
def test_the_grid_draws_the_window_the_config_asked_for():
    """`local_view_size` squares across, in a fixed 480 px box."""
    with _frame() as (r, _frame_px, _occ, params):
        n = r.layout.view_cells
        assert n == L.window_cells(r.ctx)
        assert n == min(int(params.local_view_size), int(params.width))
        assert r.cell_px == pytest.approx(L.ARENA_PX / n)
        grid = r.layout.arena_grid
        assert (grid.w, grid.h) == (L.ARENA_PX, L.ARENA_PX)
        # one ground patch per drawn square, and nothing left over
        grounds = [a for a in _arena_axes(r).get_children()
                   if type(a).__name__ == "FancyBboxPatch"]
        assert len(grounds) == n * n


@needs_fixtures
@pytest.mark.integration
def test_the_arena_declares_its_window_and_the_agent_is_inside_it():
    """The declaration the pixel audit measures against, checked against the agent.

    The renderer stamps the window onto the grid's own axes; the audit reads that instead
    of re-deriving the window rule, because two copies of one rule agree with each other
    exactly when both are wrong. What makes reading it safe is this: the window must
    contain the agent, which is the one thing a wrong origin cannot satisfy.
    """
    with _frame(step=32) as (r, _f, _occ, params):
        view = audit.arena_view(_arena_axes(r), int(params.height), int(params.width),
                                agent=np.asarray(r.values(32).state.agent_pos))
        r0, c0, rows, cols = view
        assert (rows, cols) == (r.layout.view_cells, r.layout.view_cells)
        assert view[:2] == r.view_origin(r.values(32))
        ar, ac = np.asarray(r.values(32).state.agent_pos)
        assert r0 <= ar < r0 + rows and c0 <= ac < c0 + cols


@needs_fixtures
@pytest.mark.integration
def test_a_window_declaration_without_the_agent_in_it_is_refused():
    """The failing direction of the check above — the half that makes it worth having.

    A rule that only ever sees correct declarations cannot be said to check anything, so
    the declaration is corrupted on purpose and the audit must refuse to measure rather
    than measure the wrong squares confidently.
    """
    with _frame(step=32) as (r, _f, _occ, params):
        ax = _arena_axes(r)
        n = r.layout.view_cells
        ax._world_view = (0, 0, n, n) if r.view_origin(r.values(32))[0] else (5, 5, n, n)
        with pytest.raises(audit.AuditError, match="does not contain the agent"):
            audit.arena_view(ax, int(params.height), int(params.width),
                             agent=np.asarray(r.values(32).state.agent_pos))
        # ...and a window that leaves the world at all is refused before that
        ax._world_view = (int(params.height) - 1, 0, n, n)
        with pytest.raises(audit.AuditError, match="not inside that world"):
            audit.arena_view(ax, int(params.height), int(params.width))


@needs_fixtures
@pytest.mark.integration
def test_the_window_follows_the_agent_without_changing_size():
    """Panning, stated as a property: the origin moves, the size never does.

    This is what keeps a concatenated video honest — a window that resized mid-episode
    would change the frame's geometry without the layout knowing.
    """
    with _frame() as (r, _f, _occ, params):
        sizes, origins = set(), []
        for t in range(0, r.n_steps, 7):
            v = r.values(t)
            origins.append(r.view_origin(v))
            sizes.add(r.layout.view_cells)
        assert len(sizes) == 1, "the window changed size mid-episode"
        assert len(set(origins)) > 1, "the window never moved; this episode proves nothing"
        h, w, n = int(params.height), int(params.width), r.layout.view_cells
        for r0, c0 in origins:
            assert 0 <= r0 <= h - n and 0 <= c0 <= w - n, "the window left the world"


@needs_fixtures
@pytest.mark.integration
def test_the_world_maps_box_marks_exactly_the_window_the_grid_is_drawing():
    """The map's whole reason for existing beside a windowed grid.

    Both panels read `view_origin`, so this cannot drift in principle; it is asserted in
    PIXELS anyway, because "they call the same function" is a claim about the source and
    this is a claim about the frame.
    """
    from matplotlib.patches import FancyBboxPatch

    with _frame(step=32) as (r, _f, _occ, params):
        gax = r.axes["minimap"]
        boxes = [a for a in gax.get_children()
                 if isinstance(a, FancyBboxPatch)
                 and a.get_edgecolor()[:3] == tuple(
                     __import__("matplotlib").colors.to_rgb(P.IRIS))
                 and a.get_facecolor()[3] == 0.0]
        assert len(boxes) == 1, f"expected exactly one viewport box, got {len(boxes)}"
        box = boxes[0]
        cell = gax._px_w / int(params.width)
        r0, c0 = r.view_origin(r.values(32))
        n = r.layout.view_cells
        assert box.get_x() == pytest.approx(c0 * cell - 1, abs=0.51)
        assert box.get_y() == pytest.approx(r0 * cell - 1, abs=0.51)
        assert box.get_width() == pytest.approx(n * cell + 2, abs=0.51)
        assert box.get_height() == pytest.approx(n * cell + 2, abs=0.51)


# ===========================================================================
# the grid panel: every occupant of a shared square is visible
# ===========================================================================
def _cells_of(r, frame, occ, params, step):
    """Run the co-occupancy rule over one rendered frame. Returns (findings, info)."""
    fi = audit.load_inputs(FIXTURES / "M4" / "M4", step, episode=1)
    probe = audit.FrameProbe(r.fig, frame)
    try:
        h, w = int(params.height), int(params.width)
        view = audit.arena_view(_arena_axes(r), h, w,
                                agent=np.asarray(fi.state.agent_pos))
        return audit.cell_overdraw(probe, "arena", occ, h, w, view=view)
    finally:
        probe.close()


@needs_fixtures
@pytest.mark.integration
@pytest.mark.parametrize("occupants", [
    ["agent", "rock"],
    ["food", "bush"],
    ["agent", "predator"],
    ["agent", "predator", "campfire"],
    ["agent", "predator", "food", "tree"],
])
def test_every_occupant_of_a_shared_square_survives_the_painting(occupants):
    """CP2.8's central claim, over the entities that used to be exempt from it.

    Terrain was "the floor" until Revision 27 and was excluded from a square's occupants
    by construction, so `agent + rock` — the archetype the whole redesign started from —
    was never actually asserted. It is now, at the real square size, on a real frame.
    """
    with _frame({(1, 1): occupants}, step=0) as (r, frame, occ, params):
        findings, measured = _cells_of(r, frame, occ, params, 0)
        assert [f for f in findings if f.rule.startswith("cell_")] == [], findings
        r0, c0 = r.view_origin(r.values(0))
        mine = [m for m in measured if tuple(m["square"]) == (r0 + 1, c0 + 1)]
        assert mine, "the derived square was not measured; is it inside the window?"
        m = mine[0]
        assert m["n_kinds"] == len(set(occupants))
        assert m["components_isolated"] == m["n_kinds"], m
        assert m["components_visible"] == m["n_kinds"], m
        assert all(s == pytest.approx(1.0, abs=1e-9) for s in m["survival"]), m


@needs_fixtures
@pytest.mark.integration
def test_a_real_frame_measures_every_square_the_window_shows_and_no_other():
    """The full audit on a real recorded frame, through the production capture path.

    `M4` episode 1 step 32 is used because it carries a square holding two kinds. This
    runs EVERY rule, not just the co-occupancy ones, because the rule's preconditions are
    about the whole figure.
    """
    rec = FIXTURES / "M4" / "M4"
    fi = audit.load_inputs(rec, 32, episode=1)
    # THE FRAME IS HANDED TO THE AUDIT, never fetched by it. The audit may not import
    # the renderer package (§D5.2) -- doing so would pull the packer and the registry
    # into the instrument that measures them -- so the substitution happens here, in a
    # test, which is allowed to import both.
    with _frame(step=32, episode=1) as (r, frame, _occ, _params):
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

        n = L.window_cells(
            __import__("src.environment.dashboard.panels", fromlist=["x"])
            .LayoutContext.from_params(fi.params))
        measured = {tuple(m["square"]) for m in info["cells"]}
        assert len(measured) <= n * n, (
            f"{len(measured)} squares measured for a {n}x{n} window — the audit is "
            f"measuring squares the panel does not draw")
        for m in info["cells"]:
            assert m["components_isolated"] == m["n_kinds"], m
            assert m["components_visible"] == m["n_kinds"], m
            assert all(s == pytest.approx(1.0, abs=1e-9) for s in m["survival"]), m
    finally:
        probe.close()


@needs_fixtures
@pytest.mark.integration
def test_the_instrument_catches_an_occupant_painted_over_at_the_real_square_size():
    """The mutation half. A correct frame proves nothing without it.

    The defect is the original one: a second occupant drawn CONCENTRICALLY with the first
    instead of in its own slot, so the later one covers the earlier. It is applied to the
    artists the real painter drew, at the real square size, and the rule must name the
    square.
    """
    with _frame({(1, 1): ["agent", "rock"]}, step=0) as (r, frame, occ, params):
        ax = _arena_axes(r)
        r0, c0 = r.view_origin(r.values(0))
        cell = r.cell_px
        cx, cy = (1 + 0.5) * cell, (1 + 0.5) * cell
        images = [a for a in ax.get_children() if type(a).__name__ == "AxesImage"
                  and a.get_visible()]
        here = [a for a in images
                if abs(sum(a.get_extent()[:2]) / 2 - cx) < cell / 2
                and abs(sum(a.get_extent()[2:]) / 2 - cy) < cell / 2]
        assert len(here) == 2, f"expected two tokens on the derived square, got {len(here)}"
        # drag the second token onto the first and raise it above: concentric drawing
        first, second = here
        h = C.shared_h(cell)
        second.set_extent((cx - h, cx + h, cy + h, cy - h))
        second.set_zorder(first.get_zorder() + 1)
        r.canvas.draw()
        frame = np.asarray(r.canvas.buffer_rgba())[..., :3].copy()

        findings, _m = _cells_of(r, frame, occ, params, 0)
        assert any(f.rule == "cell_overdraw" for f in findings), (
            "an occupant drawn on top of another went unreported; the instrument is not "
            "sensitive enough to be trusted, and the answer is never to relax it")


@needs_fixtures
@pytest.mark.integration
def test_the_ceiling_is_four_kinds_and_the_agent_is_never_the_one_dropped():
    """Five kinds in one square are out of scope for the grid panel, by design.

    `CELL_PRIORITY` puts the agent first and terrain last, so the square keeps answering
    the question it is for however crowded it gets.
    """
    five = ["neutral", "food", "hiding_predator", "predator", "agent"]
    shown = C.by_priority(five)[:C.MAX_SLOTS]
    assert shown[0] == "agent"
    assert len(shown) == 4
    assert "neutral" not in shown, "the LAST by priority is the one dropped"

    with_terrain = C.by_priority(["rock", "agent", "predator", "food", "neutral"])[:4]
    assert "rock" not in with_terrain, "terrain is last, so terrain is what drops"
